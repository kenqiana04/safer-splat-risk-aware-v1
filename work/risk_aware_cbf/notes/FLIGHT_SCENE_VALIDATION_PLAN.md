# Flight Scene Validation Plan

## Scope

This plan validates Risk-Aware V1 pre-CBF candidate budgeting on the second scene, `flight`.
It does not modify official SAFER-Splat source code, `run.py`, or baseline safety logic.

## Scene Assets

- scene: `flight`
- checkpoint path: `outputs/flight/splatfacto/2024-09-12_172434/config.yml`
- checkpoint weights: `outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models/step-000029999.ckpt`
- data path: `data/flight/transforms.json`

## Wrapper Support

`work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py` already contains a `flight` entry in its local `SCENES` mapping.
The runner is a wrapper-level experiment script under `work/risk_aware_cbf/`; no changes to `run.py` or official source are required.

The runner now selects a scene-specific risk-score table when `--risk-score-table` is not explicitly passed:

- `stonehenge`: `work/risk_aware_cbf/results/risk_score_table_v0.csv`
- `flight`: `work/risk_aware_cbf/results/flight_risk_score_table_v0.csv`

## Flight Risk Score Table

Flight uses its own checkpoint to extract Gaussian attributes:

- `work/risk_aware_cbf/results/flight_gaussian_attributes.csv`
- `work/risk_aware_cbf/results/flight_gaussian_attribute_summary.csv`

Before flight baseline detailed logging exists, flight active-frequency data is unavailable.
For this initial validation, `active_frequency` is filled with zero in the risk-score builder.
Thus, `risk_v2_hybrid` uses static Gaussian attributes and online distance / heading terms only for flight.

Expected risk-score outputs:

- `work/risk_aware_cbf/results/flight_risk_score_table_v0.csv`
- `work/risk_aware_cbf/results/flight_risk_score_summary_v0.csv`
- `work/risk_aware_cbf/results/flight_risk_score_metadata_v0.json`

## Execution Plan

1. Run flight smoke3 with V1 default:
   - `candidate_budget=2000`
   - `near_distance_threshold=0.08`
   - `heading_distance_threshold=0.25`
   - `heading_cos_threshold=0.5`
   - `risk_score=risk_v2_hybrid`

2. Run flight smoke3 with V1 bestD:
   - `candidate_budget=2000`
   - `near_distance_threshold=0.05`
   - `heading_distance_threshold=0.25`
   - `heading_cos_threshold=0.5`
   - `risk_score=risk_v2_hybrid`

3. Gate before flight 20-trial:
   - `collision_count == 0`
   - `min_safety_h_min > 0`
   - `qp_infeasible_count == 0`

4. If both smoke3 runs pass, run flight 20-trial for default and bestD.

5. Do not run flight 100-trial in this task.

## Claim Boundary

The reported `min_safety_h` is not meter clearance.
This is a wrapper-level prototype.
The method does not prove a new CBF theorem.
