# Official Stonehenge 100-Trial Checkpoint Comparison

## 1. Scope

This is an official-checkpoint stonehenge 100-trial no-filter vs SAFER-Splat comparison checkpoint.
This is not a full SAFER-Splat paper reproduction.
ROS, online SplatBridge mapping, and hardware experiments are not included.

This run compares the official `stonehenge` checkpoint under the repository-aligned wrapper in `reproduction/scripts/run_official_checkpoint_filter_comparison.py`.

## 2. Environment

- repo path: `/disk1/zlab/projects/safer-splat`
- git commit: `adfeba258f34aa949011638b54243cfb595568d2`
- conda environment: `/disk1/zlab/conda_envs/safer_splat_official`
- python path: `/disk1/zlab/conda_envs/safer_splat_official/bin/python`
- Python version: `Python 3.10.20`
- CUDA_VISIBLE_DEVICES: `1`
- checkpoint path: `outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml`
- gaussian_count: `116446`

## 3. Methods

Both methods use the same scene, official start-goal generation, nominal controller, double-integrator dynamics, termination logic, and safety evaluator.

- `no_filter`: directly applies the nominal PD acceleration command.
- `safer_splat_filter`: passes the same nominal command through the official CBF/QP filter.

The safety metric is `min_safety_h`, the official `GSplatLoader.query_distance` / CBF safety value. It is not meter-scale clearance.

## 4. Safety Results

| method | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | worst_trial | qp_infeasible_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 100 | 99 | 1 | -0.00023618369596078992 | -0.00021362821251386777 | 21 | 0 |
| safer_splat_filter | 100 | 0 | 100 | 0.000317254540277645 | 0.0008604969101725146 | 44 | 0 |

The filter removed the negative safety values observed in the no-filter baseline for this `stonehenge` run.

## 5. Progress / Success Results

| method | success_count | stopped_before_goal_count | initial_goal_distance_mean | final_goal_distance_mean | closest_goal_distance_mean | goal_distance_reduction_ratio_mean | reached_goal_tolerance_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 0 | 100 | 0.7841262601063096 | 0.006663629342434534 | 0.0008040468408001629 | 0.9915018246518946 | 86 |
| safer_splat_filter | 0 | 100 | 0.7841262601063096 | 0.5295235229671028 | 0.5291133673398228 | 0.324696751118169 | 5 |

`success_count` is the strict wrapper goal condition count. `stopped_before_goal` is not collision.

The no-filter run often gets very close to the goal in position, but it does so while colliding in 99/100 trials. The SAFER-Splat filter stays collision-free in 100/100 trials, but its progress ratio is lower and it stops before the strict goal condition in all evaluated trials. This supports the interpretation that the safety filter is safe but conservative under this wrapper and controller.

## 6. Runtime And Intervention

| method | runtime_mean_mean | runtime_p95_mean | intervention_rate_mean | control_deviation_mean_mean | active_constraints_mean_mean |
|---|---:|---:|---:|---:|---:|
| no_filter | 2.1168987846034727e-05 | 2.9011406935751433e-05 | 0.0 | 0.0 | 0.0 |
| safer_splat_filter | 0.06072978809015214 | 0.0688118215012364 | 0.9254504193236854 | 0.069097154702652 | 505.58664953518127 |

## 7. stopped_before_goal Analysis

The success and stop-reason definitions are documented in:

```text
reproduction/notes/STOP_REASON_AND_SUCCESS_DEFINITION.md
```

The 100-trial result has:

- `no_filter`: 100/100 `stopped_before_goal`, 0/100 strict success.
- `safer_splat_filter`: 100/100 `stopped_before_goal`, 0/100 strict success.

For `no_filter`, `reached_goal_tolerance_count=86` but strict success remains 0 because the strict wrapper logic follows `run.py`'s stopped-motion/full-state condition rather than a pure 3D position tolerance.

For `safer_splat_filter`, only `5` trajectories reached the 3D goal tolerance, and all still failed strict success.

### max_steps=1600 Diagnostic

The diagnostic ran `safer_splat_filter` trials 0-2 with `max_steps=1600`.

Diagnostic summary:

| rows | success_count | stopped_before_goal_count | collision_count | collision_free_count | final_goal_distance_mean | closest_goal_distance_mean | goal_distance_reduction_ratio_mean |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0 | 3 | 0 | 3 | 0.4690688264632958 | 0.4690688264632958 | 0.4018082982258126 |

The `steps800_vs_1600_comparison.csv` file shows zero delta for trial 0-2 on `num_steps`, `final_goal_distance`, `closest_goal_distance`, `goal_distance_reduction_ratio`, `collision`, `min_safety_h`, and `intervention_rate`. For these trials, increasing `max_steps` does not help because they terminate early with `stopped_before_goal`.

The current supported explanation is that the nominal controller plus CBF-filtered dynamics settles before reaching the strict full-state goal condition. Whether this exactly matches the paper's success metric is not confirmed.

## 8. Limitations

1. `min_safety_h` is not meter-scale clearance.
2. The current run only covers `stonehenge`.
3. The current result comes from a reproduction wrapper, not the complete unmodified `run.py` output.
4. ROS is not included.
5. SplatBridge online mapping is not included.
6. Hardware experiments are not included.
7. No risk-aware new method was implemented.

## 9. Next Steps

1. If `stonehenge` 100-trial remains the reference checkpoint, next run `flight` 10-trial or 100-trial.
2. Align the wrapper's progress/success reporting with the paper's exact progress/success metric.
3. Extract a clean CBF/QP/pruning interface only after the official reproduction baseline is stable, to prepare for later risk-aware CBF work.
4. Do not modify the official CBF algorithm yet.

## Output Files

```text
reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trials.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/summary.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/metrics.json
reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/comparison_plot.png
reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trajectory_samples.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/run_log.txt
reproduction/logs/official_checkpoint_filter_comparison_stonehenge_100.log
reproduction/results/official_checkpoint_filter_comparison_stonehenge_steps1600_diag/
```

The helper `reproduction/scripts/run_unmodified_runpy_tmux.sh` remains available for a future complete unmodified `run.py` run, but it was not executed in this task.
