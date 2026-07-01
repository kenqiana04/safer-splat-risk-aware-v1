# Offline No-Filter vs SAFER-Splat Safety-Filter Comparison

Generated: 2026-06-26T17:42:36

## Scope

This is an offline SAFER-Splat no-filter vs safety-filter comparison checkpoint.
This is not a full SAFER-Splat paper reproduction.
Official SAFER-Splat datasets/checkpoints are not yet validated unless explicitly stated.

The comparison uses the existing real flight GSplat tensor snapshot from the local SplatNav workspace and does not use random Gaussian maps or Gaussian center-only clearance.

## Environment

| item | value |
| --- | --- |
| repo path | /disk1/zlab/projects/safer-splat |
| git commit | adfeba258f34aa949011638b54243cfb595568d2 |
| conda environment | /disk1/zlab/conda_envs/safer_splat |
| Python executable | /disk1/zlab/conda_envs/safer_splat/bin/python |
| Python version | 3.10.20 |
| CUDA_VISIBLE_DEVICES | 1 |
| PyTorch | 2.1.2+cu118 |
| PyTorch CUDA | 11.8 |
| CUDA available | True |
| visible GPU 0 | NVIDIA GeForce RTX 4090 |

## Methods Compared

- `no_filter`: directly executes the same nominal command without CBF-QP correction.
- `safer_splat_filter`: uses the current SAFER-Splat CBF/QP/pruning path through the existing `CBF.solve_QP` implementation.

Both methods use the same start-goal pair, nominal controller, robot radius, real GSplat tensor snapshot, and ellipsoid collision/clearance evaluator.

## Main Comparison Metrics

Source CSV: `reproduction/results/offline_filter_comparison/comparison_summary.csv`

| method | trial | success | collision | minimum_clearance | path_length | num_steps | runtime_mean | runtime_p95 | intervention_rate | control_deviation_mean | control_deviation_max | active_constraints_mean | active_constraints_p95 | qp_infeasible_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_filter | 53 | True | False | 0.01270182803273201 | 0.596582355383411 | 105 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| safer_splat_filter | 53 | True | False | 0.02475292980670929 | 0.601032039677821 | 145 | 0.016535115126391938 | 0.0170144185423851 | 0.5517241379310345 | 0.050513701346008064 | 0.12639239797922006 | 23.358620689655172 | 36.0 | 0 |

## Hardcase Metrics

The main trial was safe for both methods, so a deterministic hardcase scan was run. The scan selected trial `9` with reason `no_filter_collision`.

Source CSV: `reproduction/results/offline_filter_comparison_hardcase/comparison_summary.csv`

| method | trial | success | collision | minimum_clearance | path_length | num_steps | runtime_mean | runtime_p95 | intervention_rate | control_deviation_mean | control_deviation_max | active_constraints_mean | active_constraints_p95 | qp_infeasible_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_filter | 9 | False | True | -0.0051793502643704414 | 0.23206933795873907 | 41 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| safer_splat_filter | 9 | True | False | 0.043391887098550797 | 0.6275636857467566 | 134 | 0.016984800947135063 | 0.017723818589001895 | 0.44029850746268656 | 0.052613016222617805 | 0.17359948860633942 | 23.074626865671643 | 32.349999999999994 | 0 |

## Key Findings

1. On the main comparison trial 53, the safety filter increased minimum clearance from `0.01270182803273201` m to `0.02475292980670929` m while both rollouts remained collision-free.
2. Because the main trial did not produce a no-filter collision, a deterministic hardcase scan was run over real official100 flight start-goal pairs. Trial 9 produced a no-filter collision with minimum clearance `-0.0051793502643704414` m, while the SAFER-Splat filter remained collision-free with minimum clearance `0.043391887098550797` m.
3. The safety filter intervention rate was `0.5517241379310345` on the main trial and `0.44029850746268656` on the hardcase. Mean control deviation stayed near `0.05` in both runs.
4. QP infeasible count was `0` on the main filtered run and `0` on the hardcase filtered run.
5. Runtime mean for the filtered runs was `0.016535115126391938` s on the main trial and `0.016984800947135063` s on the hardcase. This is consistent with an offline checkpoint, but it is not a substitute for the paper's full online timing validation.

## Artifacts

Main comparison:

- `reproduction/scripts/run_offline_filter_comparison.py`
- `reproduction/results/offline_filter_comparison/no_filter_trajectory.csv`
- `reproduction/results/offline_filter_comparison/safer_splat_filter_trajectory.csv`
- `reproduction/results/offline_filter_comparison/comparison_summary.csv`
- `reproduction/results/offline_filter_comparison/comparison_metrics.json`
- `reproduction/results/offline_filter_comparison/comparison_plot.png`
- `reproduction/results/offline_filter_comparison/run_log.txt`
- `reproduction/logs/run_offline_filter_comparison.log`

Hardcase:

- `reproduction/scripts/run_offline_filter_comparison_hardcase.py`
- `reproduction/results/offline_filter_comparison_hardcase/hardcase_scan_no_filter.csv`
- `reproduction/results/offline_filter_comparison_hardcase/no_filter_trajectory.csv`
- `reproduction/results/offline_filter_comparison_hardcase/safer_splat_filter_trajectory.csv`
- `reproduction/results/offline_filter_comparison_hardcase/comparison_summary.csv`
- `reproduction/results/offline_filter_comparison_hardcase/comparison_metrics.json`
- `reproduction/results/offline_filter_comparison_hardcase/comparison_plot.png`
- `reproduction/results/offline_filter_comparison_hardcase/run_log.txt`
- `reproduction/logs/run_offline_filter_comparison_hardcase.log`

Documentation:

- `reproduction/OFFICIAL_DATA_REQUIREMENTS.md`
- `reproduction/REPORT_OFFLINE_FILTER_COMPARISON.md`

## Limitations

1. This is still not an official full `run.py` reproduction.
2. The current checkpoint uses an existing flight GSplat tensor snapshot, not a validated official SAFER-Splat Google Drive checkpoint.
3. ROS was not run.
4. Online SplatBridge mapping was not run.
5. Hardware experiments were not run.
6. The hardcase was found by deterministic scan over available start-goal pairs; no hardcase result is fabricated.

## Next Steps

1. Download official SAFER-Splat `data/` and `outputs/` folders from Google Drive.
2. Install and validate the official loader dependencies needed by `python run.py`, especially Nerfstudio, open3d, and viser.
3. Run the smallest official `run.py` scene after confirming the `GSplatLoader` checkpoint path.
4. Expand offline evaluation to more start-goal trials.
5. Extract reusable interfaces for later risk-aware CBF work without changing the baseline filter logic.
