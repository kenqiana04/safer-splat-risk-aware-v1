# Official Data and run.py Smoke Checkpoint

Generated: 2026-06-29T12:08:46

## Scope

This is an official data/checkpoint validation and minimal run.py smoke checkpoint.
This is not a full SAFER-Splat paper reproduction.
ROS, online SplatBridge mapping, and hardware experiments are still out of scope.

## Data Status

- Google Drive download status: completed via manual local download and upload to the server.
- Uploaded archives: `data-20260629T025116Z-3-001.zip`, `data-20260629T025116Z-3-002.zip`, `outputs-20260629T025116Z-3-001.zip`.
- Remote archive directory: `/disk1/zlab/datasets/safer_splat_gdrive_zips`.
- Extracted official data directory: `/disk1/zlab/datasets/safer_splat_gdrive`.
- Repository symlinks: `data -> /disk1/zlab/datasets/safer_splat_gdrive/data`, `outputs -> /disk1/zlab/datasets/safer_splat_gdrive/outputs`.
- Official path check: 10/10 present.
- Data sizes with symlinks dereferenced:

```text
3.2G	data
1.5G	outputs
```

### SHA256 Verification

Local hashes:

```text
90cd68c4be108044c564a2ac3850d71bc10e2d9fdd5362c2a67c7629c653d2de  data-20260629T025116Z-3-001.zip
fe64571fc69d9ada16d73f7751da98615d34b88144a514ac56d0ffc8a8c6f93f  data-20260629T025116Z-3-002.zip
83cdf05935f7873672957e6c8f150f17424f0436aad1eade5ab7813331bb812d  outputs-20260629T025116Z-3-001.zip
```

Remote hashes:

```text
90cd68c4be108044c564a2ac3850d71bc10e2d9fdd5362c2a67c7629c653d2de  data-20260629T025116Z-3-001.zip
fe64571fc69d9ada16d73f7751da98615d34b88144a514ac56d0ffc8a8c6f93f  data-20260629T025116Z-3-002.zip
83cdf05935f7873672957e6c8f150f17424f0436aad1eade5ab7813331bb812d  outputs-20260629T025116Z-3-001.zip
```

### Official Path Check

| path | exists | kind | file_count_limited | size_bytes |
| --- | --- | --- | --- | --- |
| data | True | symlink_dir->/disk1/zlab/datasets/safer_splat_gdrive/data | 4874 |  |
| outputs | True | symlink_dir->/disk1/zlab/datasets/safer_splat_gdrive/outputs | 24 |  |
| data/flight | True | dir | 1993 |  |
| data/flight/images | True | dir | 496 |  |
| data/flight/transforms.json | True | file | 0 | 439346 |
| outputs/flight/splatfacto/2024-09-12_172434/config.yml | True | file | 0 | 7105 |
| outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models | True | dir | 1 |  |
| outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml | True | file | 0 | 6933 |
| outputs/statues/splatfacto/2024-09-11_095852/config.yml | True | file | 0 | 7107 |
| outputs/old_union2/splatfacto/2024-09-02_151414/config.yml | True | file | 0 | 7113 |

## Environment

| item | value |
| --- | --- |
| repo path | /disk1/zlab/projects/safer-splat |
| git commit | adfeba258f34aa949011638b54243cfb595568d2 |
| base offline conda environment | /disk1/zlab/conda_envs/safer_splat |
| official loader conda environment | /disk1/zlab/conda_envs/safer_splat_official |
| Python executable | /disk1/zlab/conda_envs/safer_splat_official/bin/python |
| Python version | 3.10.20 |
| CUDA_VISIBLE_DEVICES | 1 |
| PyTorch | 2.1.2+cu118 |
| PyTorch CUDA | 11.8 |
| CUDA available | True |
| visible GPU 0 | NVIDIA GeForce RTX 4090 |

## New Dependencies Installed

To avoid breaking the working offline comparison environment, a separate Conda environment was cloned:

```text
/disk1/zlab/conda_envs/safer_splat_official
```

Installed official loader dependencies there:

- `open3d==0.19.0`
- `nerfstudio==1.1.5`
- `viser==0.2.7`, selected by `nerfstudio==1.1.5`

Note: `requirements.txt` pins `viser==0.2.23`, but pip reported a dependency conflict because `nerfstudio==1.1.5` requires `viser==0.2.7`. For the official loader smoke, the Nerfstudio-compatible `viser==0.2.7` was used in the separate official environment.

Import check:

```text
[OK] open3d 0.19.0
[OK] nerfstudio no __version__
[OK] viser no __version__
[OK] torch 2.1.2+cu118
[OK] numpy 1.26.4
```

## Official run.py Status

The unmodified `python run.py` was executed in the official loader environment after data upload.

- Command: `timeout 900s python run.py`
- Result: did not fully complete; timeout after `901` seconds.
- Exit code: `124`.
- Default scene in current `run.py`: `stonehenge`.
- Checkpoint path used: `outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml`.
- Loader result: succeeded, loaded `116446` Gaussians from the official checkpoint.
- Reason not counted as full success: original `run.py` is hard-coded for 100 trajectories and only writes final `trajs/*.json` after all trajectories finish.

Because original `run.py` has no CLI short-run option, a reproduction-only wrapper was added under `reproduction/scripts/run_official_runpy_smoke.py`. It reuses official `GSplatLoader`, `CBF`, and dynamics code, keeps the same `stonehenge` scene configuration, and runs one official trajectory for a minimal smoke checkpoint without modifying core source.

## One-Trial Official Smoke Metrics

Source: `reproduction/results/official_run_smoke/metrics.json`

| metric | value |
| --- | --- |
| scene | stonehenge |
| trial | 0 |
| checkpoint | outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml |
| success | False |
| feasible | True |
| collision | False |
| minimum_clearance | 0.0008511263877153397 |
| minimum_clearance_note | This is the official run.py safety h value from GSplatLoader.query_distance, not a postprocessed metric in meters. |
| path_length | 0.6425270438194275 |
| num_steps | 325 |
| runtime_mean | 0.059711818213646226 |
| runtime_p95 | 0.06999427638947964 |
| intervention_rate | 0.9046153846153846 |
| control_deviation_mean | 0.02506676091135905 |
| control_deviation_max | 0.07492418864905848 |
| active_constraints_mean | 316.7938461538462 |
| active_constraints_p95 | 485.0 |
| qp_infeasible_count | 0 |
| load_seconds | 4.59068248514086 |
| gaussian_count | 116446 |
| stop_reason | stopped_before_goal |

## Deviations

1. `run.py` was not modified.
2. `data/` and `outputs/` are symlinks to `/disk1/zlab/datasets/safer_splat_gdrive` to avoid duplicating data.
3. Original `python run.py` was attempted, but not completed because it is a 100-trajectory full run and hit the 900-second smoke timeout.
4. A reproduction-only wrapper was used for one official trajectory smoke to produce metrics.
5. Nerfstudio/open3d/viser were installed only in `/disk1/zlab/conda_envs/safer_splat_official`, not in the earlier offline comparison environment.
6. ROS, SplatBridge, and hardware experiments were not run.

## Artifacts

- `reproduction/scripts/check_official_data_paths.py`
- `reproduction/scripts/run_official_runpy_smoke.py`
- `reproduction/results/official_data_path_check_after_download.csv`
- `reproduction/results/official_run_smoke/metrics.json`
- `reproduction/results/official_run_smoke/official_smoke_summary.csv`
- `reproduction/results/official_run_smoke/official_smoke_trajectory.csv`
- `reproduction/results/official_run_smoke/official_smoke_trajectory_plot.png`
- `reproduction/results/official_run_smoke/run_status.json`
- `reproduction/logs/manual_data_unzip_20260629_113841.log`
- `reproduction/logs/pip_install_official_loader_deps_retry_20260629_114301.log`
- `reproduction/logs/official_loader_import_check.log`
- `reproduction/logs/official_run_after_manual_upload.log`
- `reproduction/logs/official_runpy_smoke_wrapper.log`
- `reproduction/notes/official_data_manifest.txt`
- `reproduction/notes/official_outputs_manifest.txt`
- `reproduction/notes/official_data_size.txt`
- `reproduction/notes/safer_data_hashes_local.txt`
- `reproduction/notes/safer_data_hashes_remote.txt`
- `reproduction/COMMANDS_OFFICIAL_RUN.md`
- `reproduction/REPORT_OFFICIAL_RUN_SMOKE.md`

## Current Blockers

1. Full unmodified `run.py` still needs a longer unattended run if complete 100-trajectory JSON output is required.
2. `run.py` has no CLI scene selector and defaults to `stonehenge`; running `flight` without editing core source requires a reproduction wrapper or documented copy.
3. One-trial official smoke ended with `success=False` / `stop_reason=stopped_before_goal`, but it was collision-free and QP feasible. More trials are needed before making paper-level claims.

## Next Steps

1. If a complete official run is required, run unmodified `python run.py` in `tmux` without the 900-second timeout and let all 100 trajectories finish.
2. Add a reproduction wrapper for the official `flight` scene if flight-specific smoke is required without modifying `run.py`.
3. Extend no-filter vs SAFER-Splat comparison on the official checkpoint.
4. Later, design risk-aware CBF insertion points after the official baseline is stable.
