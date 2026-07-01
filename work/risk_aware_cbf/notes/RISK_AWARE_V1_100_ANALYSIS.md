# Risk-Aware V1 100-Trial Analysis

Generated: 2026-06-30T17:04:03

## 100-Trial Comparison

| dataset | scene | method | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | goal_distance_reduction_ratio_mean | intervention_rate_mean | control_deviation_mean_mean | active_constraints_mean_mean | runtime_mean_mean | runtime_p95_mean | qp_infeasible_count_sum | fallback_used_rate | candidate_count_final_mean | candidate_count_final_min | candidate_count_final_p95 | candidate_count_final_max | v1_insertion_level | source_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_100 | stonehenge | no_filter | 100 | 99 | 1 | -0.000236183696 | -0.0002136282125 | 0.9915018247 | 0 | 0 | 0 | 1.96243231e-05 | 2.51446031e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v1_100 | stonehenge | safer_splat_filter | 100 | 0 | 100 | 0.0003172545403 | 0.0008604969102 | 0.3246967511 | 0.9254504193 | 0.06909715478 | 505.5866495 | 0.06214337873 | 0.07051209185 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v1_100 | stonehenge | risk_aware_v1_pre_cbf | 100 | 0 | 100 | 0.0003172539582 | 0.0008605107386 | 0.3246946944 | 0.9203294458 | 0.06905307731 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 | 2000 | 20437.2 | 25421 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v0_100 | stonehenge | risk_aware_topk_v0 | 100 | 0 | 100 | 0.0003172536672 | 0.000860599968 | 0.3247081815 | 0.923859098 | 0.06907969636 | 295.7127763 | 0.06135442953 | 0.06913961265 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_stonehenge_100 |

## V1 Safety Check

1. collision_count == 0: yes; value = 0.
2. min_safety_h_min > 0: yes; value = 0.000317253958201.
3. qp_infeasible_count == 0: yes; value = 0.
4. fallback_used_rate: 0.0.
5. candidate_count_final: mean = 10809.802230086132, min = 2000.0, p95 = 20437.199999999997, max = 25421.0.
6. No min_safety_h near-zero warning under the 1e-4 heuristic.

## What Improved

- safety preserved: yes
- progress improved: no
- active constraints reduced: yes
- runtime improved: yes
- QP stability preserved: yes

## Decision

PROCEED_TO_ABLATION: V1 preserved safety and reduced mean step runtime at 100-trial scale.

Figure: `work/risk_aware_cbf/figures/risk_aware_v1_100_comparison_plots.png`
