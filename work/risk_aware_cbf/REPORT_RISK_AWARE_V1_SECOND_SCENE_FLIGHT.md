# Risk-Aware V1 Second-Scene Flight Report

## Scope

This report validates Risk-Aware V1 pre-CBF candidate-budgeting on a second scene, flight.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF theorem.

## Scene Setup

- scene: flight
- checkpoint path: outputs/flight/splatfacto/2024-09-12_172434/config.yml
- data path: data/flight/transforms.json
- gaussian_count: 281756
- flight risk score table generated: True
- flight active_frequency available: False
- active_frequency note: filled with zero

## Smoke3 Results

| method_label | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_smoke3_safer_splat_filter_default_run | 0 | 0.0006012368249 | 0.2731245624 | 180.7259015 | 0.1175054605 | 0.1284092402 | 0 |  |
| flight_smoke3_risk_aware_v1_default | 0 | 0.0006012364756 | 0.2740711179 | 155.8393518 | 0.06095616484 | 0.06574545885 | 0 | 0 |
| flight_smoke3_safer_splat_filter_bestD_run | 0 | 0.0006012368249 | 0.2731245624 | 180.7259015 | 0.1199043131 | 0.1318977667 | 0 |  |
| flight_smoke3_risk_aware_v1_bestD | 0 | 0.0006012296071 | 0.2741485934 | 152.1125908 | 0.06260310934 | 0.06890268267 | 0 | 0 |

## 20-Trial Results

| method_label | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_no_filter | 20 | -0.000911206298 | 0.9883772842 | 0 | 2.407801243e-05 | 3.914110828e-05 | 0 |  |
| flight_safer_splat_filter | 0 | 0.0003255571937 | 0.211364061 | 242.0554452 | 0.1201600652 | 0.1334189785 | 0 |  |
| flight_risk_aware_v1_default | 0 | 0.0003255566116 | 0.2115071513 | 217.8666192 | 0.06539617364 | 0.07576430325 | 0 | 0 |
| flight_risk_aware_v1_bestD | 0 | 0.000327736605 | 0.211536198 | 199.0931163 | 0.06295115068 | 0.06628800807 | 0 | 0 |

## Cross-Scene Interpretation

- V1 keeps safety on flight: yes
- V1 keeps progress on flight: yes
- V1 reduces runtime on flight: yes
- preferred config: risk_aware_v1_bestD
- preferred config reason: bestD is faster and uses fewer active constraints on flight 20-trial.
The stonehenge result was mixed: default was the fastest V1 setting, while bestD used fewer active constraints.
On flight 20-trial, bestD is both faster and lower-constraint than default V1, while both remain collision-free.

## Claim Boundary

The reported min_safety_h is not meter clearance.
This is still a wrapper-level prototype.
The method does not prove a new CBF theorem.
The method has now been tested on stonehenge and flight only.

## Next Step Decision

PROCEED_TO_FLIGHT_100: Both V1 configurations preserve flight safety/progress and reduce runtime versus SAFER-Splat on 20 trials.
