# Official Checkpoint Filter Comparison Report

## Scope

This report covers an official-checkpoint multi-trial comparison for SAFER-Splat on the `stonehenge` scene.

Compared methods:

- `no_filter`: execute the nominal PD command directly.
- `safer_splat_filter`: execute the same nominal PD command through the official CBF/QP safety filter.

This is not a full paper reproduction. It is a controlled official-checkpoint safety-filter comparison using a limited `stonehenge` trial subset.

## Repository And Environment

- Repository: `/disk1/zlab/projects/safer-splat`
- Commit: `adfeba258f34aa949011638b54243cfb595568d2`
- Conda environment: `/disk1/zlab/conda_envs/safer_splat_official`
- Python: `3.10.20`
- Torch: `2.1.2+cu118`
- GPU selection: `CUDA_VISIBLE_DEVICES=1`
- Bytecode disabled during runs: `PYTHONDONTWRITEBYTECODE=1`

No core algorithm source files were modified. New work was placed under `reproduction/`.

## Data And Checkpoint

Scene:

```text
stonehenge
```

Official checkpoint:

```text
outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml
```

Loaded model size:

```text
116446 Gaussians
```

## Parameter Alignment

The wrapper aligns with unmodified `run.py` for:

- `alpha = 5.0`
- `beta = 1.0`
- `dt = 0.05`
- `distance_type = ball-to-ellipsoid`
- `DoubleIntegrator(ndim=3)`
- official 100 circular start-goal configurations
- nominal PD controller and acceleration clamp
- stopped-motion test with default tolerance `0.001`
- loose timeout behavior, recorded as `max_steps_loose_success`

Additional details are recorded in:

```text
reproduction/notes/RUNPY_WRAPPER_PARAM_ALIGNMENT.md
```

## Metric Note

`min_safety_h` is the official `GSplatLoader.query_distance` / CBF safety value:

```text
official GSplatLoader.query_distance safety h value; not meters
```

It is not Euclidean clearance in meters.

## Smoke3 Run

Command:

```bash
python reproduction/scripts/run_official_checkpoint_filter_comparison.py \
  --scene stonehenge \
  --methods no_filter safer_splat_filter \
  --trial-start 0 \
  --trial-end 2 \
  --max-steps 600 \
  --output-dir reproduction/results/official_checkpoint_filter_comparison_stonehenge_smoke3 \
  --resume \
  --skip-existing
```

Results:

| method | total_rows | success_count | feasible_count | collision_count | collision_free_count | stopped_before_goal_count | min_safety_h_min | min_safety_h_mean | worst_trial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 3 | 0 | 3 | 3 | 0 | 3 | -0.00022701872512698174 | -0.00022588240002126744 | 2 |
| safer_splat_filter | 3 | 0 | 3 | 0 | 3 | 3 | 0.0008069269824773073 | 0.0009905836001659434 | 1 |

Smoke3 completed without program errors.

## 10-Trial Run

Command:

```bash
python reproduction/scripts/run_official_checkpoint_filter_comparison.py \
  --scene stonehenge \
  --methods no_filter safer_splat_filter \
  --trial-start 0 \
  --trial-end 9 \
  --max-steps 800 \
  --output-dir reproduction/results/official_checkpoint_filter_comparison_stonehenge_10 \
  --resume \
  --skip-existing
```

Results:

| method | total_rows | success_count | feasible_count | collision_count | collision_free_count | stopped_before_goal_count | min_safety_h_min | min_safety_h_mean | worst_trial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | 10 | 0 | 10 | 10 | 0 | 10 | -0.00022833772527519614 | -0.00022537535114679484 | 7 |
| safer_splat_filter | 10 | 0 | 10 | 0 | 10 | 10 | 0.0005385841941460967 | 0.0008541817194782197 | 6 |

Additional 10-trial SAFER-Splat filter aggregates:

| metric | value |
|---|---:|
| runtime_mean_mean | 0.05843785662985779 |
| runtime_p95_mean | 0.06717321328818798 |
| intervention_rate_mean | 0.9430757779970408 |
| control_deviation_mean_mean | 0.052679793921064234 |
| active_constraints_mean_mean | 438.6315581009876 |
| active_constraints_p95_mean | 779.6649999999998 |
| qp_infeasible_count_sum | 0 |

## Key Findings

On the official `stonehenge` checkpoint subset:

- `no_filter` produced negative `min_safety_h` on every evaluated trial.
- `safer_splat_filter` kept positive `min_safety_h` on every evaluated trial.
- Neither method reached the strict goal condition on these trial subsets; all evaluated rows stopped before the goal.
- The filter had zero QP infeasible events in the smoke3 and 10-trial runs.

The filter comparison therefore supports the expected safety-filter effect for this subset, but it does not establish full task success under the strict stopped-motion goal condition.

## Output Files

Smoke3:

```text
reproduction/results/official_checkpoint_filter_comparison_stonehenge_smoke3/trials.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_smoke3/summary.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_smoke3/metrics.json
reproduction/results/official_checkpoint_filter_comparison_stonehenge_smoke3/comparison_plot.png
reproduction/results/official_checkpoint_filter_comparison_stonehenge_smoke3/run_log.txt
reproduction/logs/official_checkpoint_filter_comparison_stonehenge_smoke3.log
```

10-trial:

```text
reproduction/results/official_checkpoint_filter_comparison_stonehenge_10/trials.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_10/summary.csv
reproduction/results/official_checkpoint_filter_comparison_stonehenge_10/metrics.json
reproduction/results/official_checkpoint_filter_comparison_stonehenge_10/comparison_plot.png
reproduction/results/official_checkpoint_filter_comparison_stonehenge_10/run_log.txt
reproduction/logs/official_checkpoint_filter_comparison_stonehenge_10.log
```

## Limitations

- Only `stonehenge` trials `0-9` were run for the main comparison.
- The reported safety metric is official safety h, not meter-scale clearance.
- This does not evaluate all official scenes or all 100 start-goal pairs.
- This does not replace unmodified `run.py` full-run reproduction.

## Next Steps

Recommended next steps:

1. Run all 100 `stonehenge` trials with `--resume --skip-existing`.
2. Repeat the same comparison for `flight`, `statues`, and `old_union2`.
3. Run the unmodified `run.py` full command in `tmux` using:

```text
reproduction/scripts/run_unmodified_runpy_tmux.sh
```

The tmux helper was created but not executed in this task.
