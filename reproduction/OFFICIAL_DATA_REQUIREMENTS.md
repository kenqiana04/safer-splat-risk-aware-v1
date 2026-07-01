# Official Data Requirements for SAFER-Splat

Generated: 2026-06-26T17:42:36

## Scope

This document records what is still needed before claiming an official SAFER-Splat `python run.py` reproduction. It does not claim that the official Google Drive checkpoints have been downloaded or validated.

## Official README Requirements

- Official data link from the repository README: https://drive.google.com/drive/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh?usp=sharing
- README scenes: `flightgate` / `flight`, `statues`, `stonehenge`, and `adirondacks`.
- README says the training data is in `data/` and model parameters are in `outputs/`.
- The expected workflow is to place the Google Drive `data` and `outputs` folders in the repository root and then run `python run.py` after confirming the `GSplatLoader` model path.

## Expected Directory Structure

The README gives this representative structure:

```text
SAFER-Splat/
├── data/
│   └── flight/
│       ├── images/
│       └── transforms.json
├── outputs/
│   └── flight/
│       └── splatfacto/
│           └── 2024-09-12_172434/
│               ├── nerfstudio_models/
│               ├── config.yml
│               └── dataparser_transforms.json
└── run.py
```

`run.py` also contains scene-specific checkpoint paths:

```text
outputs/old_union2/splatfacto/2024-09-02_151414/config.yml
outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml
outputs/statues/splatfacto/2024-09-11_095852/config.yml
outputs/flight/splatfacto/2024-09-12_172434/config.yml
```

## Current Path Check

| path | status |
| --- | --- |
| data | missing |
| outputs | missing |
| data/flight | missing |
| data/flight/images | missing |
| data/flight/transforms.json | missing |
| outputs/flight/splatfacto/2024-09-12_172434/config.yml | missing |
| outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models | missing |
| outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models/config.yml | missing |
| outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml | missing |
| outputs/statues/splatfacto/2024-09-11_095852/config.yml | missing |
| outputs/old_union2/splatfacto/2024-09-02_151414/config.yml | missing |

## What To Download

Download the official Google Drive folders without renaming their internal scene/checkpoint structure:

- `data/`
- `outputs/`

Then place them here:

```text
/disk1/zlab/projects/safer-splat/data
/disk1/zlab/projects/safer-splat/outputs
```

Do not fabricate or rename missing checkpoint paths unless `run.py` is intentionally updated and documented later.

## Dependency Status

Minimal offline safety-filter scripts already work in the existing Conda environment:

```text
Conda prefix: /disk1/zlab/conda_envs/safer_splat
Python: 3.10.20 (/disk1/zlab/conda_envs/safer_splat/bin/python)
PyTorch: 2.1.2+cu118
PyTorch CUDA: 11.8
CUDA available: True
Visible CUDA device: NVIDIA GeForce RTX 4090
CUDA_VISIBLE_DEVICES: 1
```

Offline safety-filter essentials used by the current checkpoint:

- Python 3.10
- PyTorch with CUDA
- NumPy / SciPy
- Clarabel QP solver
- Matplotlib / Pandas for reproduction outputs
- A real GSplat tensor snapshot for the offline evaluator

Dependencies still needed for official `run.py` / full loader / visualization:

- Nerfstudio 1.1.5
- open3d
- viser, especially for visualization
- Official `data/` and `outputs/` folders from Google Drive

ROS / SplatBridge / visualization are not required for the current offline comparison checkpoint, but they are required for online mapping, ROS nodes, or interactive visualizer workflows.

## Minimal Next-Step Command Draft

Only after the official `data/` and `outputs/` folders are present and loader dependencies are installed, run a minimal official smoke:

```bash
cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
python run.py
```

Before installing large dependencies or downloading data, check available disk space on `/disk1`.

## Validation Attempt 2026-06-26 Official Download

- Download command used `gdown --folder` against the official Google Drive URL.
- Download status: failed.
- Failure reason: gdown reported an error; see reproduction/logs/gdrive_download.log.
- `/disk1` space before and after the attempt stayed at approximately 347G available.
- No `data/` or `outputs/` symlink was created because the official folders were not downloaded.
- `official_data_path_check_after_download.csv` reports `0/10 present`.
- The official `run.py` first attempt failed before scene loading with `ModuleNotFoundError: No module named 'open3d'`.
- Because official `data/outputs` are still missing, heavier loader dependencies such as Nerfstudio/open3d/viser were not installed in this existing environment during this attempt; use a fresh `safer_splat_official` environment if continuing with full official loader validation.

## Resume Attempt 2026-06-29

- Retried remote Google Drive access with `curl`, Python requests, and `gdown`.
- Result: failed; remote server cannot reach drive.google.com:443; curl timed out and Python/gdown reported network unreachable.
- Also checked Windows client access with `curl.exe -I --connect-timeout 20 https://drive.google.com`; it timed out after 20 seconds.
- Official `data/` and `outputs/` remain missing; after-retry path check is `0/10 present`.
- Added `reproduction/MANUAL_OFFICIAL_DATA_DOWNLOAD.md` with manual download/upload/symlink/resume commands.

## Manual Upload Completed 2026-06-29

- Official `data/` and `outputs/` were provided locally at `C:/Users/zlab/Desktop/SAFER_DATA` as Google Drive zip archives.
- Uploaded and extracted only the `data` and `outputs` archives to `/disk1/zlab/datasets/safer_splat_gdrive`.
- Repository root uses symlinks for `data` and `outputs`.
- Official path check now reports `10/10 present`.
- A separate `/disk1/zlab/conda_envs/safer_splat_official` environment was created for official loader dependencies.
- Unmodified `python run.py` loaded the official `stonehenge` checkpoint but timed out before completing all 100 trajectories.
- `reproduction/scripts/run_official_runpy_smoke.py` completed a one-trial official smoke and wrote metrics to `reproduction/results/official_run_smoke/metrics.json`.
