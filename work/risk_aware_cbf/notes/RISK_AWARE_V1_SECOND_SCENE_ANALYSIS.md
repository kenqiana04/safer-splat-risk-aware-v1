# Risk-Aware V1 Second-Scene Flight Analysis

Generated: 2026-07-01T11:28:39

## Scene Setup

| scene | checkpoint | data | gaussian_count | risk_score_available | active_frequency_available | active_frequency_note | risk_score_table |
| --- | --- | --- | --- | --- | --- | --- | --- |
| flight | outputs/flight/splatfacto/2024-09-12_172434/config.yml | data/flight/transforms.json | 281756 | True | False | filled with zero | /disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/flight_risk_score_table_v0.csv |

## Summary

| run_label | method_label | rows | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_smoke3_default | flight_smoke3_safer_splat_filter_default_run | 3 | 0 | 0.0006012368249 | 0.2731245624 | 180.7259015 | 0.1175054605 | 0.1284092402 | 0 |  |  |
| flight_smoke3_default | flight_smoke3_risk_aware_v1_default | 3 | 0 | 0.0006012364756 | 0.2740711179 | 155.8393518 | 0.06095616484 | 0.06574545885 | 0 | 0 | 21844.14079 |
| flight_smoke3_bestD | flight_smoke3_safer_splat_filter_bestD_run | 3 | 0 | 0.0006012368249 | 0.2731245624 | 180.7259015 | 0.1199043131 | 0.1318977667 | 0 |  |  |
| flight_smoke3_bestD | flight_smoke3_risk_aware_v1_bestD | 3 | 0 | 0.0006012296071 | 0.2741485934 | 152.1125908 | 0.06260310934 | 0.06890268267 | 0 | 0 | 21435.00362 |
| flight_20 | flight_no_filter | 20 | 20 | -0.000911206298 | 0.9883772842 | 0 | 2.407801243e-05 | 3.914110828e-05 | 0 |  |  |
| flight_20 | flight_safer_splat_filter | 20 | 0 | 0.0003255571937 | 0.211364061 | 242.0554452 | 0.1201600652 | 0.1334189785 | 0 |  |  |
| flight_20 | flight_risk_aware_v1_default | 20 | 0 | 0.0003255566116 | 0.2115071513 | 217.8666192 | 0.06539617364 | 0.07576430325 | 0 | 0 | 23758.49601 |
| flight_20 | flight_risk_aware_v1_bestD | 20 | 0 | 0.000327736605 | 0.211536198 | 199.0931163 | 0.06295115068 | 0.06628800807 | 0 | 0 | 23346.94074 |
| stonehenge_100 | stonehenge_risk_aware_v1_default | 100 | 0 | 0.0003172539582 | 0.3246946944 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 |
| stonehenge_100 | stonehenge_risk_aware_v1_bestD | 100 | 0 | 0.0003172536672 | 0.3246745833 | 252.2219893 | 0.04044284326 | 0.04454808397 | 0 | 0 | 9905.290047 |

## Cross-Scene Checks

- safety_preserved: True
- progress_preserved: True
- runtime_improved: True
- default_safe: True
- bestD_safe: True
- default_progress_preserved: True
- bestD_progress_preserved: True
- default_runtime_improved: True
- bestD_runtime_improved: True
- preferred_config: risk_aware_v1_bestD
- preferred_reason: bestD is faster and uses fewer active constraints on flight 20-trial.
- recommended_decision: PROCEED_TO_FLIGHT_100
- decision_reason: Both V1 configurations preserve flight safety/progress and reduce runtime versus SAFER-Splat on 20 trials.

## Claim Boundary

`min_safety_h` is not meter clearance. This remains a wrapper-level prototype tested on stonehenge and flight only.
