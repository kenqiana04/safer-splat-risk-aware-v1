# SAFER-Splat Offline Baseline Install Notes

Generated: 2026-06-26T16:39:36

## Official Recommendation From README

- Repository: https://github.com/chengine/safer-splat.git
- Tested stack in README: Python 3.10, Nerfstudio 1.1.5, viser 0.2.7/0.2.23, Clarabel 0.10.0, NumPy 1.26.4, PyTorch 2.1.2, CUDA 11.8.
- Official full setup commands include PyTorch cu118, CUDA toolkit 11.8, Nerfstudio 1.1.5, and `pip install -r requirements.txt`.
- Official data is hosted on Google Drive. Scenes mentioned by README: flightgate/flight, statues, stonehenge, adirondacks/old_union style examples.
- Official demo entry point: `python run.py`, after editing/confirming the GSplatLoader model path.
- Visualization entry point: `python visualize.py`, requires viser and trained model outputs.

## Actual Minimal Offline Environment Used Here

- Conda environment: `/disk1/zlab/conda_envs/safer_splat` (`conda activate safer_splat`).
- Python: Python 3.10.20
- Python path: `/disk1/zlab/conda_envs/safer_splat/bin/python`
- PyTorch/CUDA/GPU info:

```text
2.1.2+cu118
11.8
True
NVIDIA GeForce RTX 4090
```

- Installed minimal packages: torch 2.1.2+cu118, torchvision 0.16.2+cu118, numpy 1.26.4, scipy, clarabel 0.10.0, matplotlib, pandas, cvxpy, osqp, tqdm.
- Nerfstudio, open3d, and viser were not installed for the offline smoke path. This avoids blocking on full training/visualization/ROS dependencies.

## Data Used

- Official SAFER-Splat Google Drive data was not downloaded in this checkpoint.
- Offline smoke uses a real GSplat tensor snapshot already available on this server:
  `/disk1/zlab/projects/splatnav/reproduction/flight_gsplat_tensors.pt`.
- The smoke harness uses only start/goal from `/disk1/zlab/projects/splatnav/trajs/flight_splatplan_official100.json` trial 53. It does not use the saved SplatPlan trajectory as a rollout.

## Current Minimal Reproduction Path

1. Use the independent `safer_splat` conda environment.
2. Run `reproduction/scripts/test_distance_cbf_sanity.py` to validate distance and CBF-QP behavior.
3. Run `reproduction/scripts/run_offline_safety_filter_smoke.py` to perform one offline safety-filter rollout with real GSplat geometry.
4. Read metrics from `reproduction/results/offline_smoke/`.

## Environment Risks

- Full official `GSplatLoader` import currently fails because `open3d` and `nerfstudio` are not installed. This is expected for the minimal offline checkpoint and is logged in `reproduction/logs/optional_loader_imports.log`.
- Full `python run.py` requires Google Drive data/model outputs at the expected paths under `outputs/.../config.yml`.
- The official distance code has numerical edge cases for batch size 1 and exact identity quaternions; the sanity script avoids those degenerate synthetic cases and records this as an implementation caveat.
- Root filesystem is nearly full; use `/disk1` for environments, logs, cache, and datasets.
