# Baseline Detailed Logging Schema

This schema defines the independent logging wrapper used for risk-aware CBF evidence gathering. It does not modify the official SAFER-Splat baseline.

## 3.1 Per-Trial Fields

The `trials.csv` file records one row per completed method/trial pair:

```text
scene
method
trial
checkpoint
gaussian_count
success
collision
collision_free
stop_reason
min_safety_h
goal_distance_reduction_ratio
initial_goal_distance
final_goal_distance
closest_goal_distance
num_steps
runtime_mean
runtime_p95
intervention_rate
control_deviation_mean
active_constraints_mean
qp_infeasible_count
seconds_total
error
```

`min_safety_h` is the official `GSplatLoader.query_distance` / CBF safety value. It is not meter-scale clearance.

## 3.2 Per-Step Trajectory Fields

The `per_step_trajectory.csv` file records one row per rollout step:

```text
scene
method
trial
step
time
x
y
z
vx
vy
vz
goal_x
goal_y
goal_z
goal_distance
nominal_u_x
nominal_u_y
nominal_u_z
filtered_u_x
filtered_u_y
filtered_u_z
control_deviation
min_safety_h_step
collision_step
qp_feasible
runtime_step
active_constraints_count
```

For `no_filter`, `filtered_u_*` equals `nominal_u_*`, and `active_constraints_count=0`.

For `safer_splat_filter`, `active_constraints_count` is the number of QP constraints after the baseline minimal half-space pruning step, as observed by the independent instrumentation wrapper.

## 3.3 Active Constraint / Gaussian Fields

The `active_constraints.csv` file records a bounded subset of active constraints per step. The default wrapper logs the lowest-`h` selected constraints up to `--active-log-limit` rows per step to avoid producing multi-gigabyte files.

Fields:

```text
scene
method
trial
step
gaussian_id
candidate_local_id
candidate_rank
selected_by_baseline
is_forced_near_critical
h_value
distance_or_safety_value
mean_x
mean_y
mean_z
scale_x
scale_y
scale_z
max_scale
anisotropy
opacity
volume_proxy
distance_to_robot
heading_alignment_proxy
mapping_status
logging_scope
```

If true global Gaussian IDs cannot be recovered from the pruning stage, `gaussian_id` is left empty, `candidate_local_id` is used, and `mapping_status` explains the limitation.

The wrapper must not fabricate Gaussian IDs.

## Current Implementation Note

The official `CBF.get_QP_matrices` calls `h_rep_minimal`, whose public return value does not expose original Gaussian IDs. The detailed logging wrapper therefore reimplements the same matrix-building logic inside `work/risk_aware_cbf` and records IDs when SciPy's `HalfspaceIntersection.dual_vertices` provides a direct mapping. If the fallback ConvexHull path is used, the mapping is marked incomplete.

The logging is for diagnosis only. It does not implement risk-aware control.
