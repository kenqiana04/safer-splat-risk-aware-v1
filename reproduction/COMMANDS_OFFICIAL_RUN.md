# SAFER-Splat Official Run Commands

Started: 20260626_180125

```bash
cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
which python > reproduction/notes/python_path_official_run.txt
python -V > reproduction/notes/python_version_official_run.txt
python -m pip freeze > reproduction/notes/pip_freeze_before_official_run.txt
conda list > reproduction/notes/conda_list_before_official_run.txt
df -h /disk1 > reproduction/notes/disk_space_before_official_download.txt
```

## Data path check script

```bash
python reproduction/scripts/check_official_data_paths.py 2>&1 | tee reproduction/logs/check_official_data_paths_before_download.log
```

## Official Google Drive download attempt

```bash
df -h /disk1
python -m pip show gdown || python -m pip install gdown
mkdir -p /disk1/zlab/datasets/safer_splat_gdrive
cd /disk1/zlab/datasets/safer_splat_gdrive
gdown --folder "https://drive.google.com/drive/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh?usp=sharing"
```

## After-download path check and manifest attempt

```bash
python reproduction/scripts/check_official_data_paths.py --phase after_download 2>&1 | tee reproduction/logs/check_official_data_paths_after_download.log
find data -maxdepth 4 -type f | sort > reproduction/notes/official_data_manifest.txt || true
find outputs -maxdepth 6 -type f | sort > reproduction/notes/official_outputs_manifest.txt || true
du -sh data outputs > reproduction/notes/official_data_size.txt || true
```

## First official run.py attempt

```bash
python run.py 2>&1 | tee reproduction/logs/official_run_first_attempt.log
```

## Resume retry 20260629_103746

```bash
git status --short > reproduction/checkpoints/status_before_resume_gdown_retry_<timestamp>.txt
git diff --name-only > reproduction/checkpoints/diff_names_before_resume_gdown_retry_<timestamp>.txt
df -h /disk1 > reproduction/notes/disk_space_before_gdown_retry_<timestamp>.txt
```

## Google Drive retry 20260629_103813

```bash
curl -I --connect-timeout 20 https://drive.google.com
cd /disk1/zlab/datasets/safer_splat_gdrive
gdown --folder "https://drive.google.com/drive/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh?usp=sharing"
```

Network probe log: reproduction/logs/gdrive_network_probe_20260629_103813.log
Download retry log: reproduction/logs/gdrive_download_retry_20260629_103813.log

## After retry path check 20260629_104237

```bash
python reproduction/scripts/check_official_data_paths.py --phase after_download 2>&1 | tee reproduction/logs/check_official_data_paths_after_retry_<timestamp>.log
```

exit_status=2

## Manual official data upload/unzip 20260629_113841

```bash
scp data-*.zip outputs-*.zip zlab-4090:/disk1/zlab/datasets/safer_splat_gdrive_zips/
unzip -n -q <zip> -d /disk1/zlab/datasets/safer_splat_gdrive
ln -s /disk1/zlab/datasets/safer_splat_gdrive/data data
ln -s /disk1/zlab/datasets/safer_splat_gdrive/outputs outputs
python reproduction/scripts/check_official_data_paths.py --phase after_download
```

## Create separate official loader env 20260629_114053

```bash
conda create -p /disk1/zlab/conda_envs/safer_splat_official --clone /disk1/zlab/conda_envs/safer_splat -y
conda activate /disk1/zlab/conda_envs/safer_splat_official
python -m pip install open3d nerfstudio==1.1.5 viser==0.2.23
```

## Retry official loader deps without explicit viser pin 20260629_114301

Reason: nerfstudio==1.1.5 requires viser==0.2.7, while repo requirements.txt pins viser==0.2.23.

```bash
python -m pip install open3d nerfstudio==1.1.5
```

## Official run.py after manual data upload 20260629_114754

```bash
conda activate /disk1/zlab/conda_envs/safer_splat_official
timeout 900s python run.py 2>&1 | tee reproduction/logs/official_run_after_manual_upload.log
```

## Official one-trial smoke wrapper

```bash
python reproduction/scripts/run_official_runpy_smoke.py --scene stonehenge --trial 0 --n-steps 500
```

## Official one-trial smoke wrapper

```bash
python reproduction/scripts/run_official_runpy_smoke.py --scene stonehenge --trial 0 --n-steps 500
```
