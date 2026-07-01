# Risk-Aware V1 Pre-CBF Candidate-Budget Prototype

## Scope

This report evaluates a V1 pre-CBF candidate-budgeting prototype.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF theorem.

## Feasibility Conclusion

`PARTIALLY_FEASIBLE`.

The official loader has no native candidate-subset API, but a reproduction-only `SubsetGSplatLoader` can temporarily expose subset tensors before the official distance query and restore the full tensors after each query.

## Method

- candidate budget: 2000
- near-distance threshold: 0.08
- heading threshold: distance 0.25 and cosine 0.5
- risk score: `risk_v2_hybrid`
- hard fallback: full official baseline query if the candidate subset is too small or selector metadata fails
- actual insertion level: `partial_pre_cbf`

## Smoke3 Results

| dataset | scene | method | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | goal_distance_reduction_ratio_mean | intervention_rate_mean | control_deviation_mean_mean | active_constraints_mean_mean | runtime_mean_mean | runtime_p95_mean | qp_infeasible_count_sum | fallback_used_rate | candidate_count_final_mean | candidate_count_final_min | candidate_count_final_p95 | candidate_count_final_max | v1_insertion_level | source_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_smoke3 | stonehenge | no_filter | 3 | 3 | 0 | -0.0002270187251 | -0.0002258824 | 0.9913371756 | 0 | 0 | 0 | 1.845290025e-05 | 2.016955987e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_smoke3 |
| v1_smoke3 | stonehenge | risk_aware_v1_pre_cbf | 3 | 0 | 3 | 0.0008069268661 | 0.0009905818151 | 0.4018284973 | 0.9581264058 | 0.05253257815 | 255.2240508 | 0.03497561287 | 0.03830439753 | 0 | 0 | 10315.26703 | 3614 | 20146.3 | 24337 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_smoke3 |
| v1_smoke3 | stonehenge | safer_splat_filter | 3 | 0 | 3 | 0.0008069269825 | 0.0009905836002 | 0.4018082982 | 0.9591520468 | 0.05253575513 | 416.4105893 | 0.05770104615 | 0.06662259223 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_smoke3 |

## 20-Trial Results

| dataset | scene | method | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | goal_distance_reduction_ratio_mean | intervention_rate_mean | control_deviation_mean_mean | active_constraints_mean_mean | runtime_mean_mean | runtime_p95_mean | qp_infeasible_count_sum | fallback_used_rate | candidate_count_final_mean | candidate_count_final_min | candidate_count_final_p95 | candidate_count_final_max | v1_insertion_level | source_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_20 | stonehenge | no_filter | 20 | 20 | 0 | -0.0002317183244 | -0.0002260564281 | 0.9917401775 | 0 | 0 | 0 | 1.951412285e-05 | 2.42393231e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20 |
| v1_20 | stonehenge | risk_aware_v1_pre_cbf | 20 | 0 | 20 | 0.0003336731752 | 0.000763409608 | 0.5712284434 | 0.9090094445 | 0.05932401445 | 296.3107912 | 0.03665814935 | 0.04024592503 | 0 | 0 | 10215.54632 | 2000 | 17746 | 25421 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20 |
| v1_20 | stonehenge | safer_splat_filter | 20 | 0 | 20 | 0.0003336710215 | 0.0007631153654 | 0.5711932643 | 0.9114099913 | 0.05933765727 | 466.0328274 | 0.05970819485 | 0.06894749828 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20 |

## Honest Interpretation

If V1 only falls back to baseline most of the time, it is not a real V1 improvement.
If V1 reduces candidates but causes collision, it is unsafe.
If V1 reduces runtime without losing safety, it is promising.
If V1 still does not improve progress, that should be reported directly.

Observed V1 fallback_used_rate: 0.0.
Observed V1 candidate_count_final_mean: 10215.546316851665.
Observed V1 collision_count: 0.
Observed V1 min_safety_h_min: 0.0003336731751915.
Observed V1 runtime_mean_mean: 0.0366581493465829.
Observed V1 progress mean: 0.5712284434302061.

## Next Step Decision

PROCEED_TO_100: V1 preserved safety and reduced mean step runtime against the 20-trial SAFER-Splat baseline.
