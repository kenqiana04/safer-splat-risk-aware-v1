# Risk-Aware CBF Preparation Report

## 1. Scope

This report prepares the risk-aware CBF direction.
It does not implement a new controller.
It does not modify the official SAFER-Splat baseline.

The goal is to decide whether Gaussian-level and trajectory-interaction cues provide a scientifically defensible basis for a future risk-aware CBF wrapper.

## 2. Baseline Motivation

The official `stonehenge` 100-trial checkpoint comparison motivates this direction:

| method | rows | collision_count | collision_free_count | success_count | stopped_before_goal_count | goal_distance_reduction_ratio_mean | intervention_rate_mean | active_constraints_mean_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 100 | 99 | 1 | 0 | 100 | 0.9915018246518946 | 0.0 | 0.0 |
| safer_splat_filter | 100 | 0 | 100 | 0 | 100 | 0.324696751118169 | 0.9254504193236854 | 505.58664953518127 |

The no-filter baseline is unsafe but high-progress. The SAFER-Splat filter is safe but conservative under this wrapper. This creates a clear safety-progress trade-off worth analyzing before implementing any new method.

## 3. Interface Map

The interface review is documented in:

```text
work/risk_aware_cbf/notes/BASELINE_INTERFACE_MAP.md
work/risk_aware_cbf/notes/interface_keyword_search.txt
```

The recommended safe insertion hierarchy is:

1. risk-aware logging only;
2. risk-aware candidate ranking before CBF;
3. risk-aware top-k active constraint selection with hard safety fallback;
4. adaptive inflation / margin;
5. QP slack / penalty changes;
6. direct CBF formula modification.

The first implementation should avoid direct CBF formula modification.

## 4. Gaussian Attribute Extraction

Gaussian attributes were extracted from the official `stonehenge` checkpoint with `GSplatLoader`.

| item | value |
|---|---:|
| gaussian_count | 116446 |
| max_scale_mean | 0.026693237931033762 |
| max_scale_median | 0.002225174568593502 |
| anisotropy_mean | 25027.4422093587 |
| anisotropy_median | 107.98498756991884 |
| opacity_mean | 0.6362844037819716 |
| opacity_median | 0.6834975779056549 |
| volume_proxy_mean | 0.0010649254315496745 |

Available attributes:

```text
means, scales, max/min/mean scale, anisotropy, volume_proxy, distance_to_scene_center, opacity, rotation/quaternion, color_or_sh_norm
```

Missing attributes:

```text
None observed in this extraction
```

The extracted attributes are suitable for geometry/confidence risk-score design. They do not by themselves prove which Gaussians cause conservatism; trajectory interaction evidence is still needed.

## 5. Trajectory-Interaction Analysis

Analyzed groups:

| group | method | rows | progress_mean | min_safety_h_mean | sampled_trajectory_rows |
|---|---|---:|---:|---:|---:|
| no_filter_collision | no_filter | 99 | 0.9915012752510739 | -0.0002216544579079544 | 0 |
| other | no_filter | 1 | 0.9915562153331426 | 0.0005809700815007091 | 0 |
| other | safer_splat_filter | 50 | 0.21289725266244916 | 0.0008148439216893167 | 0 |
| safer_collision_free_higher_progress | safer_splat_filter | 25 | 0.8346539908285728 | 0.0007474718440789729 | 1 |
| safer_collision_free_low_progress | safer_splat_filter | 25 | 0.03833850831920476 | 0.0010648279532324524 | 0 |


Key observations:

- `no_filter_collision` contains 99 rows and has high progress, but negative safety values.
- `safer_collision_free_low_progress` and `safer_collision_free_higher_progress` split the safe trajectories into low/high progress groups.
- Gaussian-neighborhood trajectory features are currently limited because `trajectory_samples.csv` contains sampled path points only for `safer_splat_filter:0`.

Limitations:

- No synthetic trajectory samples were generated.
- Gaussian-neighborhood correlations cannot be claimed from one sampled trajectory.
- Full per-step trajectory logging or active-constraint logging is needed before making strong Gaussian-level claims.

## 6. Conservatism Analysis

Strongest SAFER-Splat indicators by absolute Spearman correlation with progress:

| feature | n | pearson | spearman | note |
|---|---:|---:|---:|---|
| num_steps | 100 | 0.9877838224471274 | 0.9873673775518845 |  |
| control_deviation_mean | 100 | -0.7813226773734677 | -0.7760202581473635 |  |
| runtime_mean | 100 | -0.41860642522245906 | -0.5662423229618133 |  |
| min_safety_h | 100 | -0.3373725501223465 | -0.4581305618395549 |  |
| intervention_rate | 100 | -0.5226073923802206 | -0.42316507551691374 |  |
| active_constraints_mean | 100 | -0.3276341946299355 | -0.3266206217859092 |  |


Top/bottom progress comparison:

| feature | low_progress_mean | high_progress_mean | high_minus_low |
|---|---:|---:|---:|
| intervention_rate | 0.9666137819161479 | 0.8611787601017469 | -0.10543502181440101 |
| active_constraints_mean | 538.4008099534783 | 442.00759094487745 | -96.39321900860085 |
| control_deviation_mean | 0.08839554397122315 | 0.04397118330172951 | -0.04442436066949364 |

Interpretation:

- Higher intervention and higher control deviation are associated with lower progress.
- Higher active-constraint counts are also associated with lower progress, but the relationship is weaker than control deviation.
- `num_steps` correlates strongly with progress, but this mostly reflects that longer-moving trajectories make more progress; it is not an independent causal explanation.
- Gaussian neighborhood features are insufficient for correlation analysis with the current sampled trajectory coverage.

## 7. Risk Score Design

The risk-score design is documented in:

```text
work/risk_aware_cbf/notes/RISK_SCORE_DESIGN_V0.md
```

Recommended first method:

```text
Risk-Aware Top-K Constraint Ranking with Hard Safety Fallback
```

Hard safety fallback:

1. Always include any Gaussian / constraint with low `h`.
2. Always include any near-field Gaussian inside a distance threshold.
3. Always include any Gaussian inside a heading cone or high TTC-risk zone.
4. Apply risk-aware ranking only to the remaining non-critical candidates.

## 8. Go / No-Go Decision

Decision:

```text
WEAK GO
```

Rationale:

- GO evidence: the baseline safety-progress trade-off is strong; intervention/control deviation/active constraints are associated with low progress; Gaussian attributes are available; a wrapper-level insertion point exists.
- Weakness: current trajectory samples are insufficient to prove Gaussian-level causal relationships. Static Gaussian attributes are useful candidates, but their interaction with conservatism needs better per-step logging.
- Safety condition: any next implementation must preserve hard near-critical constraints and compare against the original SAFER-Splat baseline without modifying official code.

## 9. Recommended Next Implementation

Implement risk-aware top-k constraint ranking with hard safety fallback in a separate `work/risk_aware_cbf` wrapper.

Do not modify official SAFER-Splat code.

Compare:

```text
no_filter vs SAFER-Splat baseline vs risk-aware wrapper
```

on `stonehenge` 100-trial first, using the same collision, `min_safety_h`, progress, intervention, runtime, active-constraint, and QP infeasible metrics.

## Claim-Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| SAFER-Splat is safe but conservative on this checkpoint | 100/100 collision-free; mean progress ratio 0.3247 | supported for this wrapper/checkpoint |
| no_filter is high-progress but unsafe | 99/100 collisions; mean progress ratio 0.9915 | supported for this wrapper/checkpoint |
| intervention/control deviation relate to low progress | correlation and group comparison tables | supported as association, not causality |
| Gaussian-level risk cues are promising | attributes are available and interpretable | needs more trajectory interaction evidence |
| risk-aware CBF can be implemented safely by direct formula changes | not supported | avoid this claim |

## Output Files

```text
work/risk_aware_cbf/results/stonehenge_gaussian_attributes.csv
work/risk_aware_cbf/results/stonehenge_gaussian_attribute_summary.csv
work/risk_aware_cbf/results/trajectory_interaction_features.csv
work/risk_aware_cbf/results/trajectory_interaction_feature_summary.csv
work/risk_aware_cbf/results/conservatism_correlation_table.csv
work/risk_aware_cbf/results/conservatism_group_comparison.csv
work/risk_aware_cbf/figures/stonehenge_gaussian_attribute_histograms.png
work/risk_aware_cbf/figures/trajectory_interaction_feature_plots.png
work/risk_aware_cbf/figures/conservatism_indicator_plots.png
```

## Environment

- repo: `/disk1/zlab/projects/safer-splat`
- git commit: `adfeba258f34aa949011638b54243cfb595568d2`
- python path: `/disk1/zlab/conda_envs/safer_splat_official/bin/python`
- python version: `Python 3.10.20`

## Final Self-Review

- Contribution clarity: this is preparation and evidence gathering, not a new controller.
- Writing clarity: all claims are tied to extracted CSVs or reproduced baseline tables.
- Experimental strength: sufficient for a preparation decision; insufficient for final method claims.
- Evaluation completeness: missing dense per-step trajectory samples and active Gaussian IDs.
- Method design soundness: hard safety fallback is mandatory before any top-k pruning.
