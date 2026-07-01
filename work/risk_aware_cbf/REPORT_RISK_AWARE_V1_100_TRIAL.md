# Risk-Aware V1 Pre-CBF 100-Trial Validation

## Scope

This report validates Risk-Aware V1 pre-CBF candidate-budgeting on the stonehenge 100-trial official checkpoint.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF safety theorem.

## Method

- candidate budget: 2000
- near-distance threshold: 0.08
- heading threshold: distance 0.25 and cosine 0.5
- risk score: `risk_v2_hybrid`
- hard fallback: full official baseline query if the candidate subset is too small or selector metadata fails
- actual insertion level: `partial_pre_cbf`
- uses SubsetGSplatLoader: yes, as a reproduction-only wrapper
- modifies official source code: no

## 100-Trial Comparison

| dataset | scene | method | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | goal_distance_reduction_ratio_mean | intervention_rate_mean | control_deviation_mean_mean | active_constraints_mean_mean | runtime_mean_mean | runtime_p95_mean | qp_infeasible_count_sum | fallback_used_rate | candidate_count_final_mean | candidate_count_final_min | candidate_count_final_p95 | candidate_count_final_max | v1_insertion_level | source_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_100 | stonehenge | no_filter | 100 | 99 | 1 | -0.000236183696 | -0.0002136282125 | 0.9915018247 | 0 | 0 | 0 | 1.96243231e-05 | 2.51446031e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v1_100 | stonehenge | safer_splat_filter | 100 | 0 | 100 | 0.0003172545403 | 0.0008604969102 | 0.3246967511 | 0.9254504193 | 0.06909715478 | 505.5866495 | 0.06214337873 | 0.07051209185 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v1_100 | stonehenge | risk_aware_v1_pre_cbf | 100 | 0 | 100 | 0.0003172539582 | 0.0008605107386 | 0.3246946944 | 0.9203294458 | 0.06905307731 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 | 2000 | 20437.2 | 25421 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v0_100 | stonehenge | risk_aware_topk_v0 | 100 | 0 | 100 | 0.0003172536672 | 0.000860599968 | 0.3247081815 | 0.923859098 | 0.06907969636 | 295.7127763 | 0.06135442953 | 0.06913961265 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_stonehenge_100 |

## What Improved

- safety preserved: yes
- progress improved: no
- active constraints reduced: yes
- runtime improved: yes
- QP stability preserved: yes

## Honest Interpretation

If V1 preserves safety and reduces runtime, this is promising preliminary evidence for pre-CBF candidate budgeting.
If progress remains unchanged, do not claim navigation progress improvement.
If V1 does not reduce runtime at 100-trial scale, do not claim computational improvement.
If V1 causes collision or QP infeasible, do not proceed; V1 fallback is insufficient.

## Claim Boundary

This is still a wrapper-level prototype.
The reported `min_safety_h` is not meter clearance.
The method does not prove a new CBF theorem.
The method has only been validated on stonehenge so far.

## Next Step Decision

PROCEED_TO_ABLATION: V1 preserved safety and reduced mean step runtime at 100-trial scale.

V1 ablation is prepared but not executed in this task unless explicitly requested.
