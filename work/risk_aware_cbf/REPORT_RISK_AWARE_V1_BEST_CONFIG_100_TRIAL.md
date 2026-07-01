# Risk-Aware V1 Best Config 100-Trial Report

## Scope

This report validates the best V1 ablation configuration on stonehenge 100-trial.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF theorem.

## Best Config

- ablation_id: D_budget2000_near005_hybrid
- candidate_budget: 2000
- near_distance_threshold: 0.05
- heading_distance_threshold: 0.25
- heading_cos_threshold: 0.5
- risk_score: risk_v2_hybrid
- actual_insertion_level: partial_pre_cbf

## 100-Trial Comparison

| comparison_label | collision_count | min_safety_h_min | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_filter | 99 | -0.000236183696 | 0.9915018247 | 0 | 0 | 0 | 1.969417039e-05 | 2.600115724e-05 | 0 |  |  |
| safer_splat_filter | 0 | 0.0003172545403 | 0.3246967511 | 0.9254504193 | 0.06909715478 | 505.5866495 | 0.06307919365 | 0.07194588652 | 0 |  |  |
| risk_aware_topk_v0 | 0 | 0.0003172536672 | 0.3247081815 | 0.923859098 | 0.06907969636 | 295.7127763 | 0.06135442953 | 0.06913961265 | 0 | 0 | 291.1100134 |
| risk_aware_v1_pre_cbf_default | 0 | 0.0003172539582 | 0.3246946944 | 0.9203294458 | 0.06905307731 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 |
| risk_aware_v1_pre_cbf_bestD | 0 | 0.0003172536672 | 0.3246745833 | 0.9183233525 | 0.06903840588 | 252.2219893 | 0.04044284326 | 0.04454808397 | 0 | 0 | 9905.290047 |

## What Improved

- safety preserved: yes
- progress preserved: yes
- progress improved: no
- active constraints reduced: yes
- runtime improved: yes
- QP stability preserved: yes
- active constraints lower than default V1: yes
- runtime lower than default V1: no

## Honest Interpretation

If bestD preserves safety and reduces runtime, this supports V1 pre-CBF candidate budgeting as a computational-efficiency method.
If progress remains unchanged, do not claim navigation progress improvement.
In this run, bestD reduces active constraints relative to default V1, but default V1 remains slightly faster on runtime_mean and runtime_p95.
Therefore, bestD is the lower-constraint configuration for next validation, while default V1 remains the fastest V1 setting observed here.
If bestD causes collision or QP infeasible cases, do not proceed to second-scene validation.

## Claim Boundary

This is still a wrapper-level prototype.
The reported min_safety_h is not meter clearance.
The method does not prove a new CBF theorem.
The method has only been validated on stonehenge so far.

## Next Step Decision

PROCEED_TO_SECOND_SCENE: bestD preserves safety and progress while reducing runtime versus the SAFER-Splat baseline.
