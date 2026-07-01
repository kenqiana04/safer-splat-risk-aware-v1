# Stop Reason And Success Definition

## Scope

This note documents the trajectory termination and success definitions used by the unmodified `run.py` and by `reproduction/scripts/run_official_checkpoint_filter_comparison.py`.

The current wrapper is for reproduction diagnostics only. It does not modify the official CBF, GSplat distance query, dynamics, or `run.py`.

## Unmodified run.py Termination

In `run.py`, each trajectory runs up to `n_steps = 500` by default.

At every step, `run.py`:

1. computes the nominal PD command `u_des`;
2. applies the CBF/QP safety filter with `u = cbf.solve_QP(x, u_des)`;
3. stops immediately if the QP solver reports failure;
4. propagates the double-integrator state with `dt = 0.05`;
5. evaluates safety with `GSplatLoader.query_distance(..., distance_type='ball-to-ellipsoid')`;
6. checks whether the state stopped moving with `torch.norm(x - x_) < 0.001`;
7. if stopped, marks success only when `torch.norm(x_ - goal) < 0.001`;
8. if the loop reaches the final step, appends `success=True` and `feasible=True`.

The final-step behavior is a loose timeout success in `run.py`; it is not the same as reaching the goal.

## Wrapper Definitions

The wrapper keeps the same nominal controller, dynamics, distance type, CBF/QP filter, and stopped-motion threshold unless changed through CLI arguments.

### success

`success=True` means one of:

- strict stopped-motion goal condition: the robot has stopped and `norm(x_prev - goal) < goal_tolerance`;
- `max_steps_loose_success`, which follows the loose timeout behavior in `run.py`.

Rows with `stop_reason=stopped_before_goal` are always recorded with `success=False`.

### stopped_before_goal

`stopped_before_goal` means the state changed by less than `goal_tolerance`, but the previous state was not within `goal_tolerance` of the goal.

This is not a collision label. A stopped-before-goal trajectory can be collision-free or in collision depending on `min_safety_h`.

### collision

`collision=True` means the minimum official safety value along the evaluated trajectory is negative:

```text
min_safety_h < 0
```

`min_safety_h` is the official `GSplatLoader.query_distance` / CBF safety value, not metric clearance in meters.

### max_steps_reached

The wrapper records the unmodified `run.py` timeout behavior as:

```text
stop_reason=max_steps_loose_success
success=True
```

This is kept for alignment with `run.py`, but reports should separate strict goal success from loose timeout progress.

### qp_infeasible

When the CBF/QP solver fails, the wrapper records:

```text
success=False
feasible=False
stop_reason=solver_failed
```

The wrapper does not skip the QP for `safer_splat_filter`.

## Alignment With Paper Metrics

Not confirmed. The current wrapper's `success_count` is a strict implementation-level goal/timeout label derived from `run.py`, not a confirmed paper-level success metric.

Reports should therefore present:

- `success_count` as strict wrapper success;
- `stopped_before_goal_count` as a separate termination class;
- progress metrics such as `final_goal_distance`, `closest_goal_distance`, and `goal_distance_reduction_ratio`.

## Why The 10-Trial Run Was stopped_before_goal

Observed in the 10-trial run:

- all `no_filter` rows had `stop_reason=stopped_before_goal` and negative `min_safety_h`;
- all `safer_splat_filter` rows had `stop_reason=stopped_before_goal` and positive `min_safety_h`;
- all rows had `success=False` under the strict stopped-motion goal condition.

Possible explanations:

- `goal_tolerance=0.001` may be too strict for this controller and dynamics setup.
- The nominal PD command is capped at `0.1`, so progress can become very slow near constrained regions.
- The CBF filter may conservatively alter the command to preserve positive safety.
- The unmodified `run.py` appears more focused on generating feasible/safety trajectories than on reporting a paper-level goal-success metric.
- Whether `max_steps` alone is insufficient is not confirmed until the 1600-step diagnostic is run.

Do not convert `stopped_before_goal` to success without explicitly changing and reporting the success definition.

## 100-Trial And 1600-Step Diagnostic Update

The official-checkpoint `stonehenge` 100-trial comparison produced:

- `no_filter`: 100/100 `stopped_before_goal`, 99/100 collision, 0/100 strict success.
- `safer_splat_filter`: 100/100 `stopped_before_goal`, 0/100 collision, 0/100 strict success.

For `safer_splat_filter` trials 0, 1, and 2, increasing `max_steps` from 800 to 1600 did not change:

- `num_steps`;
- `final_goal_distance`;
- `closest_goal_distance`;
- `goal_distance_reduction_ratio`;
- `collision`;
- `min_safety_h`;
- `intervention_rate`.

Those three trajectories stop before reaching the goal well before the 800-step limit, so the observed stopped-before-goal result for them is not explained by the 800-step cap.

The most defensible current explanation is that the wrapper follows the strict `run.py` stopped-motion logic, while the nominal controller and CBF-filtered dynamics often settle before the full 6D goal state is reached. The exact paper-level success metric remains not confirmed.

## Reporting Recommendation

For subsequent reports:

1. Report `success_count` as strict wrapper success.
2. Report `stopped_before_goal_count` separately.
3. Report `collision_count` and `collision_free_count` separately.
4. Use progress metrics to describe how far trajectories moved toward the goal.
5. State that `min_safety_h` is not meter-scale clearance.
6. If a looser paper-level criterion is needed, define it as a separate metric rather than overwriting `success`.
