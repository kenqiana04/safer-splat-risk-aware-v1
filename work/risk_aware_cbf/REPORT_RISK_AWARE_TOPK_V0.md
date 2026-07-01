# Risk-Aware Top-K V0 Report

## Scope

This report evaluates a first wrapper-level risk-aware top-k constraint ranking prototype.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF safety theorem.

The safety metric `min_safety_h` is the official GSplat safety h value used by the existing baseline wrapper. It is not meter clearance.

## Method

Method:

```text
Risk-Aware Top-K Constraint Ranking with Hard Safety Fallback
```

Configuration used in smoke3 and 20-trial:

| item | value |
|---|---:|
| risk score | risk_v2_hybrid |
| topk | 300 |
| h_critical | 0.0006 |
| near_distance_threshold | 0.05 |
| heading_force_threshold | 0.65 |
| heading_force_distance | 0.15 |

Risk score inputs:

```text
active_frequency_norm
opacity_norm
anisotropy_norm
max_scale_norm
online inverse distance_to_robot
online heading_alignment
```

Hard fallback:

1. Keep all selected constraints with `h_value <= h_critical`.
2. Keep all selected constraints with `distance_to_robot <= near_distance_threshold`.
3. Keep selected heading-cone constraints when heading alignment and distance thresholds are satisfied.
4. If global Gaussian IDs, h values, or metadata are incomplete, fallback to the original baseline selected constraints for that step.
5. If risk-aware selection becomes empty or below `min_required_constraints`, fallback to the original baseline selected constraints.

Insertion point:

```text
reproduction wrapper after baseline CBF minimal constraints and before Clarabel QP solve
```

This is a wrapper-level approximation because the official `CBF` class does not expose an external candidate-selection hook. The prototype mirrors the baseline CBF matrix construction in `work/risk_aware_cbf/` and applies top-k only to the final selected constraint matrix before solving the same QP form.

## Results

### Smoke3

| method | collision_count | min_safety_h_min | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | qp_infeasible_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 3 | -0.00022701872512698174 | 0.9913371756492282 | 0.0 | 0.0 | 0.0 | 0.00002009803500979478 | 0 |
| safer_splat_filter | 0 | 0.0008069269824773073 | 0.4018082982258126 | 0.9591520467836258 | 0.05253575512589793 | 416.41058929374714 | 0.057074419453135156 | 0 |
| risk_aware_topk_v0 | 0 | 0.0008069268660619855 | 0.40180828555717424 | 0.9591520467836258 | 0.05253576096451673 | 277.718126405758 | 0.05868035583492507 | 0 |

Smoke3 selection diagnostics:

| item | value |
|---|---:|
| fallback_used_rate | 0.0 |
| baseline_active_constraints_count_debug_mean | 376.43830570902395 |
| risk_aware_selected_count_debug_mean | 275.11418047882137 |
| forced_low_h_count_mean | 0.0 |
| forced_near_count_mean | 13.541436464088397 |
| forced_heading_count_mean | 61.9060773480663 |

### 20-Trial

| method | collision_count | min_safety_h_min | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | qp_infeasible_count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 20 | -0.00023171832435764372 | 0.9917401775145688 | 0.0 | 0.0 | 0.0 | 0.000019516158367300394 | 0 |
| safer_splat_filter | 0 | 0.00033367102150805295 | 0.5711932642733182 | 0.9114099913014566 | 0.05933765727175662 | 466.03282741675037 | 0.058994448356648674 | 0 |
| risk_aware_topk_v0 | 0 | 0.00033367102150805295 | 0.5711940388034845 | 0.9110555508394894 | 0.059337716137548194 | 289.56279464390497 | 0.06009501738077701 | 0 |

20-trial selection diagnostics:

| item | value |
|---|---:|
| fallback_used_rate | 0.0 |
| baseline_active_constraints_count_debug_mean | 462.7893037336024 |
| risk_aware_selected_count_debug_mean | 286.75237134207873 |
| forced_low_h_count_mean | 0.13481331987891018 |
| forced_near_count_mean | 18.65005045408678 |
| forced_heading_count_mean | 77.77961654894047 |

## Safety Check

Smoke3:

```text
risk_aware_topk_v0 collision_count = 0
risk_aware_topk_v0 min_safety_h_min = 0.0008069268660619855
risk_aware_topk_v0 qp_infeasible_count_sum = 0
fallback_used_rate = 0.0
```

20-trial:

```text
risk_aware_topk_v0 collision_count = 0
risk_aware_topk_v0 min_safety_h_min = 0.00033367102150805295
risk_aware_topk_v0 qp_infeasible_count_sum = 0
fallback_used_rate = 0.0
```

No negative `min_safety_h` was observed for `risk_aware_topk_v0` in smoke3 or 20-trial. No QP infeasible case was observed.

## Interpretation

The prototype is safe on smoke3 and 20-trial under the tested configuration.
It reduces selected constraints substantially:

```text
20-trial active_constraints_mean:
safer_splat_filter = 466.03282741675037
risk_aware_topk_v0 = 289.56279464390497
relative change = -37.86643824020511%
```

It does not materially improve progress:

```text
20-trial progress_mean:
safer_splat_filter = 0.5711932642733182
risk_aware_topk_v0 = 0.5711940388034845
```

It does not reduce runtime in this implementation:

```text
20-trial runtime_mean:
safer_splat_filter = 0.058994448356648674
risk_aware_topk_v0 = 0.06009501738077701
```

The likely reason is the insertion point. V0 ranks constraints after baseline distance querying and minimal-polytope construction, so it reduces QP constraint count but not the earlier candidate-processing work. This is preliminary evidence that risk-aware ranking can preserve safety while reducing the final QP constraint set, not evidence that V0 improves navigation progress or end-to-end runtime.

## Can Proceed To 100-Trial?

Decision:

```text
yes, with a narrow objective
```

Reason:

The 20-trial run is collision-free, has no QP infeasible cases, and preserves the baseline minimum safety h. A 100-trial run is reasonable if the objective is to validate safety and constraint-count reduction at larger scale.

It should not be framed as a final method win unless a follow-up sweep also improves progress, intervention, or runtime.

## Next Steps

1. Run `stonehenge` 100-trial for the same V0 configuration to validate stability.
2. Sweep `topk`, `h_critical`, and `risk_score`.
3. Add an ablation comparing `risk_v0_active_frequency`, `risk_v1_geometry`, and `risk_v2_hybrid`.
4. If runtime improvement is the target, design a cleaner wrapper API that reduces candidate work before minimal-polytope construction, without editing official source files.
5. After stable `stonehenge` 100-trial results, test `flight` as a second scene.

## Output Files

```text
work/risk_aware_cbf/notes/RISK_AWARE_TOPK_V0_DESIGN.md
work/risk_aware_cbf/scripts/build_risk_score_table.py
work/risk_aware_cbf/results/risk_score_table_v0.csv
work/risk_aware_cbf/results/risk_score_summary_v0.csv
work/risk_aware_cbf/figures/risk_score_distribution_v0.png
work/risk_aware_cbf/scripts/run_risk_aware_topk_comparison.py
work/risk_aware_cbf/results/risk_aware_topk_stonehenge_smoke3/
work/risk_aware_cbf/results/risk_aware_topk_stonehenge_20/
work/risk_aware_cbf/scripts/analyze_risk_aware_topk_results.py
work/risk_aware_cbf/results/risk_aware_topk_analysis_summary.csv
work/risk_aware_cbf/figures/risk_aware_topk_comparison_plots.png
work/risk_aware_cbf/notes/RISK_AWARE_TOPK_V0_ANALYSIS.md
work/risk_aware_cbf/REPORT_RISK_AWARE_TOPK_V0.md
```

## Environment

| item | value |
|---|---|
| repository | `/disk1/zlab/projects/safer-splat` |
| git commit | `adfeba258f34aa949011638b54243cfb595568d2` |
| conda environment | `/disk1/zlab/conda_envs/safer_splat_official` |
| GPU selector | `CUDA_VISIBLE_DEVICES=1` |

## Self-Review

- Core-source modification: no intended modification to `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, or `run.py`.
- Method claim: this is a wrapper-level V0 prototype, not the final method.
- Safety claim: supported for smoke3 and 20-trial only under the tested configuration.
- Runtime claim: no end-to-end runtime improvement was observed in V0.
- Theory claim: no new CBF safety theorem is claimed.
