# Risk-Aware Top-K V0 Design

## Method Name

```text
Risk-Aware Top-K Constraint Ranking with Hard Safety Fallback
```

## Core Principle

Risk-aware ranking must never remove near-critical constraints.
It can only prioritize non-critical candidate constraints under a runtime or constraint budget.
The official SAFER-Splat CBF/QP solve remains unchanged.

This V0 implementation is a wrapper-level prototype under `work/risk_aware_cbf/`.
It does not modify `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, or `run.py`.

## Wrapper Insertion Point

The official `CBF` class does not expose an external hook for replacing its selected constraint set.
V0 therefore uses a reproduction-only wrapper that mirrors the baseline CBF matrix construction, obtains the same selected CBF constraints, and then applies risk-aware top-k selection before calling the same Clarabel QP solve.

This is an approximation relative to a future clean API-level integration. It is suitable for feasibility testing, but it is not a change to the official SAFER-Splat baseline.

## Hard Safety Fallback Rules

1. Force include all candidates with `h_value <= h_critical`.
2. Force include all candidates with `distance_to_robot <= near_distance_threshold` when Gaussian means are available.
3. Force include heading-cone candidates when the heading proxy is available and the Gaussian is in front of the current command direction.
4. If candidate metadata or global Gaussian IDs are incomplete, fallback to the original baseline selected constraints for that step.
5. If risk-aware selection would produce fewer than `min_required_constraints`, fallback to baseline selected constraints.
6. If the QP solver fails, the rollout records the failure and does not hide it.

If forced constraints exceed `topk`, all forced constraints are retained. The budget only limits non-critical ranked constraints.

## Risk Score Candidates

### risk_v0_active_frequency

```text
score = normalize(active_frequency)
```

This uses how often a Gaussian appeared in the baseline detailed logging active set. Missing frequency is treated as zero.

### risk_v1_geometry

Runtime score:

```text
score =
  0.25 * normalize(opacity)
+ 0.25 * normalize(anisotropy)
+ 0.25 * normalize(max_scale)
+ 0.25 * normalize(1 / distance_to_robot)
```

The first three terms come from the precomputed Gaussian risk table. The inverse-distance term is computed online for the current robot state.

### risk_v2_hybrid

Runtime score:

```text
score =
  0.35 * normalize(active_frequency)
+ 0.20 * normalize(opacity)
+ 0.15 * normalize(anisotropy)
+ 0.15 * normalize(max_scale)
+ 0.10 * normalize(1 / distance_to_robot)
+ 0.05 * normalize(heading_alignment)
```

This is the default V0 score. The weights are engineering defaults for smoke testing, not tuned or claimed optimal.

## Risk Score Data

The risk score table is built from:

```text
work/risk_aware_cbf/results/stonehenge_gaussian_attributes.csv
work/risk_aware_cbf/results/active_gaussian_frequency.csv
work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100/active_constraints.csv
```

All static normalizations use robust min-max scaling with percentile clipping to reduce extreme-value domination.

## Evaluation Protocol

Compare:

```text
no_filter
safer_splat_filter
risk_aware_topk_v0
```

Metrics:

```text
collision_count
collision_free_count
min_safety_h_min
min_safety_h_mean
goal_distance_reduction_ratio_mean
final_goal_distance_mean
closest_goal_distance_mean
intervention_rate_mean
control_deviation_mean
active_constraints_mean
runtime_mean
runtime_p95
qp_infeasible_count
fallback_used_rate
```

V0 starts with:

```text
topk = 300
h_critical = 0.0006
near_distance_threshold = 0.05
risk_score = risk_v2_hybrid
```

These defaults are only for initial feasibility testing.
