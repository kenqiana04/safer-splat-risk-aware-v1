# run.py Wrapper Parameter Alignment

This note records how `reproduction/scripts/run_official_checkpoint_filter_comparison.py` aligns with the unmodified repository `run.py`.

## Scope

The wrapper is for official-checkpoint multi-trial comparison of:

- `no_filter`: directly applies the nominal PD command from `run.py`.
- `safer_splat_filter`: applies the official CBF/QP safety filter path from `run.py`.

It does not modify `run.py` or any core algorithm source.

## Default Scene And Checkpoint

Unmodified `run.py` iterates over `['stonehenge']` by default.

The wrapper also defaults to `--scene stonehenge` and uses:

```text
outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml
```

The wrapper additionally exposes the other official scene checkpoints from `run.py`:

```text
old_union2 -> outputs/old_union2/splatfacto/2024-09-02_151414/config.yml
stonehenge -> outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml
statues    -> outputs/statues/splatfacto/2024-09-11_095852/config.yml
flight     -> outputs/flight/splatfacto/2024-09-12_172434/config.yml
```

## Start-Goal Generation

Both scripts generate 100 official start-goal pairs with:

```python
t = np.linspace(0, 2*np.pi, 100)
t_z = 10*np.linspace(0, 2*np.pi, 100)
x0 = [radius_config*cos(t), radius_config*sin(t), radius_z*sin(t_z)] + mean_config
xf = [radius_config*cos(t+pi), radius_config*sin(t+pi), radius_z*sin(t_z+pi)] + mean_config
```

The wrapper exposes inclusive `--trial-start` and `--trial-end` selectors and never creates random start-goal pairs.

## Dynamics And Controller

Both scripts use:

```text
DoubleIntegrator(ndim=3)
dt = 0.05
alpha = 5.0
beta = 1.0
distance_type = ball-to-ellipsoid
```

The nominal control is copied from `run.py`:

```python
vel_des = 5.0*(goal[:3] - x[:3])
vel_des = torch.clamp(vel_des, -0.1, 0.1)
vel_des = vel_des + 1.0*(goal[3:] - x[3:])
u_des = 1.0*(vel_des - x[3:])
u_des = torch.clamp(u_des, -0.1, 0.1)
```

## Method Difference

`safer_splat_filter` matches the official safety-filter branch:

```python
u = cbf.solve_QP(x, u_des)
```

`no_filter` bypasses only that filter:

```python
u = u_des
```

Both methods still evaluate safety after propagation using the official `GSplatLoader.query_distance(..., distance_type='ball-to-ellipsoid')`.

## Termination And Success

The wrapper preserves the `run.py` stopped-motion test:

```python
if torch.norm(x - x_prev) < goal_tolerance:
    success = torch.norm(x_prev - goal) < goal_tolerance
```

The default `--goal-tolerance` is `0.001`, matching `run.py`.

If the loop reaches `--max-steps`, the wrapper records `stop_reason=max_steps_loose_success` and `success=True`, matching the loose timeout behavior in `run.py`.

If the robot stops before the goal, the wrapper records:

```text
success=False
feasible=True
stop_reason=stopped_before_goal
```

This prevents stopped-before-goal trajectories from being counted as successful.

## Minimum Safety Value

`min_safety_h` is the minimum official CBF/query safety value:

```text
official GSplatLoader.query_distance safety h value; not meters
```

It is not a postprocessed metric in meters and should not be reported as Euclidean clearance.

## Known Wrapper Differences

The wrapper adds:

- command-line scene/method/trial selection;
- resume and skip-existing behavior;
- per-trial CSV rows;
- aggregate summary CSV;
- JSON metrics;
- a compact comparison plot;
- explicit `no_filter` vs `safer_splat_filter` comparison.

It does not change the official checkpoint loader, GSplat distance computation, CBF, dynamics, or QP implementation.
