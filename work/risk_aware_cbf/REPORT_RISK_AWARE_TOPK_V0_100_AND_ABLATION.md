# Risk-Aware Top-K V0 100-Trial and Ablation Report

## Scope

This report validates Risk-Aware Top-K V0 on `stonehenge` 100-trial and runs a small 20-trial ablation.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF safety theorem.

The safety value `min_safety_h` is the official GSplat safety h value used by the existing SAFER-Splat wrapper. It is not meter clearance.

## 100-Trial Result

| method | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | qp_infeasible_count | fallback_used_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 99 | 1 | -0.00023618369596078992 | -0.00021362821251386777 | 0.9915018246518946 | 0.0 | 0.0 | 0.0 | 0.000019203924978311324 | 0 | n/a |
| safer_splat_filter | 0 | 100 | 0.000317254540277645 | 0.0008604969101725146 | 0.324696751118169 | 0.9254504193236854 | 0.06909715477600109 | 505.58664953518127 | 0.06125752391329338 | 0 | n/a |
| risk_aware_topk_v0 | 0 | 100 | 0.0003172536671627313 | 0.0008605999680003151 | 0.3247081815273468 | 0.9238590979584118 | 0.06907969635546894 | 295.71277631192885 | 0.06135442952596271 | 0 | 0.0 |

The 100-trial run confirms the narrow stability claim: `risk_aware_topk_v0` preserved collision-free behavior and kept QP infeasible count at zero.
It reduced the final selected constraint count from `505.58664953518127` to `295.71277631192885`, a relative reduction of about `41.5%`.

The 100-trial run does not show a meaningful navigation-progress gain:

```text
safer_splat_filter progress_mean = 0.324696751118169
risk_aware_topk_v0 progress_mean = 0.3247081815273468
```

It also does not show an end-to-end runtime gain:

```text
safer_splat_filter runtime_mean = 0.06125752391329338
risk_aware_topk_v0 runtime_mean = 0.06135442952596271
```

The likely reason remains the V0 insertion point: this wrapper ranks constraints after baseline distance querying and minimal-polytope construction, so it reduces the final QP constraint set but not the earlier candidate-processing work.

## What Improved

| question | answer | evidence |
|---|---|---|
| safety preserved? | yes | `risk_aware_topk_v0` has `collision_count = 0`, `min_safety_h_min > 0`, and `qp_infeasible_count = 0` on 100-trial. |
| QP constraints reduced? | yes | active constraints mean drops from `505.58664953518127` to `295.71277631192885`. |
| progress improved? | no meaningful improvement | progress mean differs by only about `1.14e-5`. |
| intervention reduced? | only very slightly | intervention rate changes from `0.9254504193236854` to `0.9238590979584118`. |
| runtime improved? | no | runtime mean is slightly higher for V0 in this implementation. |

## Ablation

All ablation settings ran `stonehenge` trial 0-19 for `risk_aware_topk_v0`.
No ablation setting produced a collision or QP infeasible case.

| ablation_id | topk | h_critical | risk_score | collision_count | min_safety_h_min | progress_mean | intervention_rate_mean | active_constraints_mean | runtime_mean | qp_infeasible_count | fallback_used_rate |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A_topk150_h0006_hybrid | 150 | 0.0006 | risk_v2_hybrid | 0 | 0.000333671545377 | 0.5711912208769162 | 0.9072577612196993 | 156.81418088630886 | 0.0601684841068095 | 0 | 0.0 |
| B_topk300_h0006_hybrid | 300 | 0.0006 | risk_v2_hybrid | 0 | 0.000333671021508 | 0.5711940388034845 | 0.9110555508394894 | 289.56279464390497 | 0.0606368119109501 | 0 | 0.0 |
| C_topk500_h0006_hybrid | 500 | 0.0006 | risk_v2_hybrid | 0 | 0.000333671370754 | 0.571193285800073 | 0.9112865345113332 | 397.34620269590425 | 0.0602993758730048 | 0 | 0.0 |
| D_topk300_h0004_hybrid | 300 | 0.0004 | risk_v2_hybrid | 0 | 0.000333671021508 | 0.5711940388034845 | 0.9110555508394894 | 289.56279464390497 | 0.0601679286543523 | 0 | 0.0 |
| E_topk300_h0010_hybrid | 300 | 0.0010 | risk_v2_hybrid | 0 | 0.000333671021508 | 0.5711940388034845 | 0.9110555508394894 | 289.56279464390497 | 0.0601853558661076 | 0 | 0.0 |
| F_topk300_h0006_activefreq | 300 | 0.0006 | risk_v0_active_frequency | 0 | 0.0003336713125463 | 0.5711932778092528 | 0.9111630777212096 | 289.56293132909786 | 0.0599662861631554 | 0 | 0.0 |
| G_topk300_h0006_geometry | 300 | 0.0006 | risk_v1_geometry | 0 | 0.000333671370754 | 0.571165545055878 | 0.908456116405932 | 289.5305693629206 | 0.0607603085531838 | 0 | 0.0 |

### Ablation Interpretation

1. `topk = 150` did not lose safety on these 20 trials and produced the lowest active constraint count. This is promising for constraint budgeting, but it still did not improve progress or runtime.
2. `topk = 500` kept safety but selected more constraints, as expected.
3. Changing `h_critical` from `0.0004` to `0.0010` did not change the 20-trial summary for `topk = 300` in this setup. This suggests the selected forced set was dominated by near-field or heading rules, or that low-h candidates were already retained.
4. `risk_v0_active_frequency`, `risk_v1_geometry`, and `risk_v2_hybrid` all preserved safety. Their progress differences are too small to claim a navigation improvement.
5. No ablation group simultaneously produced a meaningful progress or runtime improvement.

## Honest Interpretation

V0 is a stable constraint-budgeting wrapper under the tested `stonehenge` settings.
It preserves SAFER-Splat safety on 100-trial and reduces final QP constraints substantially.

It should not be described as improving navigation progress.
It should not be described as a real-time acceleration method in this implementation.
It should not be described as a final risk-aware CBF method.

The current evidence supports keeping V0 as a constraint-budgeting baseline, not as the final paper contribution.

## Next Step Recommendation

Recommended next method change:

```text
Move risk-aware ranking earlier, before candidate generation / distance query / minimal-polytope construction.
```

Rationale:

The present wrapper reduces the final QP size but does not reduce earlier GSplat distance and pruning work. To improve runtime or progress, the risk-aware mechanism likely needs to affect candidate generation before the CBF constraints are built, while still preserving hard near-critical fallback.

Concrete next steps:

1. Keep V0 as a safe constraint-budgeting baseline.
2. Run a 100-trial validation for `topk = 150` only if the goal is to test more aggressive constraint budgeting.
3. Do not claim progress or runtime benefit from V0.
4. Design V1 around pre-CBF candidate generation or a loader-level candidate-budget API, still only in `work/risk_aware_cbf/`.

## Output Files

```text
work/risk_aware_cbf/results/risk_aware_topk_stonehenge_100/
work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20/
work/risk_aware_cbf/scripts/run_risk_aware_topk_ablation.py
work/risk_aware_cbf/results/risk_aware_topk_analysis_summary.csv
work/risk_aware_cbf/figures/risk_aware_topk_comparison_plots.png
work/risk_aware_cbf/REPORT_RISK_AWARE_TOPK_V0_100_AND_ABLATION.md
```

## Self-Review

- Claim support: safety and constraint-count claims are supported by 100-trial and ablation CSVs.
- Unsupported claims removed: no progress improvement, no runtime improvement, no new CBF theorem.
- Remaining limitation: V0 acts after baseline candidate processing, so it is not expected to reduce end-to-end runtime.
