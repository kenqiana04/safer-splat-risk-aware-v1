# Risk-Aware V1 Pre-CBF Design

## Method Name

Risk-Aware Pre-CBF Candidate-Budgeting with Hard Safety Fallback.

## Insertion Point

The prototype inserts candidate selection before the official distance query and before CBF matrix construction by using a reproduction-only `SubsetGSplatLoader` wrapper. The actual insertion level is recorded as `partial_pre_cbf` because the official loader and CBF source are unchanged and no official subset API exists.

## Candidate Subset Rule

At each control step, V1 starts from all Gaussian ids and constructs a subset:

1. Force include near-field candidates with distance to the robot less than `near_distance_threshold`.
2. Force include heading-cone candidates whose distance is less than `heading_distance_threshold` and whose alignment with nominal control is at least `heading_cos_threshold`.
3. Force include locally relevant historically active candidates from the V0 risk table.
4. Rank remaining candidates by the selected risk score.
5. Fill the remaining budget with highest-ranked candidates.
6. If the selected subset is too small or selector metadata fails, fall back to the original full-loader baseline for that step.

The default candidate budget is 2000.

## Risk Scores

The wrapper supports:

- `risk_v0_active_frequency`
- `risk_v1_geometry`
- `risk_v2_hybrid`

The input table is `work/risk_aware_cbf/results/risk_score_table_v0.csv`.

## Hard Fallback

The fallback policy is conservative:

1. Always include near-field candidates within `near_distance_threshold`.
2. Always include heading-cone candidates within `heading_distance_threshold`.
3. Always include high-active-frequency candidates when they are spatially relevant to the current robot position.
4. If final subset size is below `min_candidate_budget`, query the full official loader.
5. If smoke3 produces any collision, non-positive `min_safety_h`, or QP infeasibility, do not run 20-trial; generate diagnosis instead.

## Difference From V0

V0 trims final QP constraints after baseline CBF construction.

V1 attempts to reduce candidate processing before CBF construction. When the subset is active, fewer Gaussian tensors enter the official distance query, minimal-polytope construction, and QP construction. When fallback is active, V1 is equivalent to the full SAFER-Splat baseline for that step.

## Logged Fields

`v1_candidate_debug.csv` records:

- candidate budget
- total Gaussian count
- forced near-field count
- forced heading-cone count
- risk-ranked count
- final candidate count
- fallback state
- actual insertion level
- per-step safety value after full-scene validation
- runtime, control deviation, and active constraint count
