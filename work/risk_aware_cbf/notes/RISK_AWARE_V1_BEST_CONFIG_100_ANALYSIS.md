# Risk-Aware V1 Best Config 100-Trial Analysis

Generated: 2026-07-01T10:35:14

## Scope

This analysis validates `D_budget2000_near005_hybrid` on stonehenge 100-trial and compares it against existing same-scale baselines.
It does not modify the official SAFER-Splat baseline and does not claim a new CBF theorem.

## 100-Trial Comparison

| comparison_label | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean | actual_insertion_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_filter | 99 | -0.000236183696 | 0.9915018247 | 0 | 1.969417039e-05 | 2.600115724e-05 | 0 |  |  |  |
| safer_splat_filter | 0 | 0.0003172545403 | 0.3246967511 | 505.5866495 | 0.06307919365 | 0.07194588652 | 0 |  |  |  |
| risk_aware_topk_v0 | 0 | 0.0003172536672 | 0.3247081815 | 295.7127763 | 0.06135442953 | 0.06913961265 | 0 | 0 | 291.1100134 | risk_aware_topk_v0 |
| risk_aware_v1_pre_cbf_default | 0 | 0.0003172539582 | 0.3246946944 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 | partial_pre_cbf |
| risk_aware_v1_pre_cbf_bestD | 0 | 0.0003172536672 | 0.3246745833 | 252.2219893 | 0.04044284326 | 0.04454808397 | 0 | 0 | 9905.290047 | partial_pre_cbf |

## Validation Checks

- safety_preserved: True
- progress_preserved: True
- progress_improved: False
- active_constraints_reduced: True
- runtime_improved: True
- qp_stability_preserved: True
- fallback_low: True
- active_constraints_lower_than_default_v1: True
- runtime_lower_than_default_v1: False

## Decision

- recommended_decision: PROCEED_TO_SECOND_SCENE
- reason: bestD preserves safety and progress while reducing runtime versus the SAFER-Splat baseline.

## Claim Boundary

`min_safety_h` is not meter clearance. This remains a wrapper-level prototype validated on stonehenge only.
