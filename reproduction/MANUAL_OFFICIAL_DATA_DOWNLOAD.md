# Manual Official SAFER-Splat Data Download Instructions

Generated: 2026-06-29T10:45:51

## Why Manual Download Is Needed

The 4090 server and this Windows client both failed to reach the official Google Drive URL during the resume attempt.

Remote evidence:

- Network probe: `reproduction/logs/gdrive_network_probe_20260629_103813.log`
- Download retry log: `reproduction/logs/gdrive_download_retry_20260629_103813.log`
- Result: remote server cannot reach drive.google.com:443; curl timed out and Python/gdown reported network unreachable

Local Windows probe evidence from this Codex run: `curl.exe -I --connect-timeout 20 https://drive.google.com` timed out after 20 seconds.

## Official Source

Download the official SAFER-Splat folders from:

```text
https://drive.google.com/drive/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh?usp=sharing
```

The repository README says the official package should contain:

```text
data/
outputs/
```

Do not rename internal scene/checkpoint folders.

## Upload To Server

After downloading on a network that can access Google Drive, place the folders on the server under:

```text
/disk1/zlab/datasets/safer_splat_gdrive/data
/disk1/zlab/datasets/safer_splat_gdrive/outputs
```

Example from Windows PowerShell, if your downloaded folders are under `C:/Users/zlab/Downloads/safer_splat_gdrive`:

```powershell
scp -r C:/Users/zlab/Downloads/safer_splat_gdrive/data zlab-4090:/disk1/zlab/datasets/safer_splat_gdrive/
scp -r C:/Users/zlab/Downloads/safer_splat_gdrive/outputs zlab-4090:/disk1/zlab/datasets/safer_splat_gdrive/
```

## Link Into Repository

Run this only after both folders exist in `/disk1/zlab/datasets/safer_splat_gdrive`:

```bash
cd /disk1/zlab/projects/safer-splat
if [ ! -e data ]; then ln -s /disk1/zlab/datasets/safer_splat_gdrive/data data; fi
if [ ! -e outputs ]; then ln -s /disk1/zlab/datasets/safer_splat_gdrive/outputs outputs; fi
```

## Resume Validation

```bash
cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1

python reproduction/scripts/check_official_data_paths.py --phase after_download 2>&1 | tee reproduction/logs/check_official_data_paths_after_manual_upload.log
find data -maxdepth 4 -type f | sort > reproduction/notes/official_data_manifest.txt
find outputs -maxdepth 6 -type f | sort > reproduction/notes/official_outputs_manifest.txt
du -sh data outputs > reproduction/notes/official_data_size.txt
```

If the path check passes, use a separate official-loader environment before installing heavy dependencies:

```bash
conda create -n safer_splat_official python=3.10 -y
conda activate safer_splat_official
pip install torch==2.1.2+cu118 torchvision==0.16.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
conda install -c nvidia/label/cuda-11.8.0 cuda-toolkit -y
pip install nerfstudio==1.1.5 open3d viser clarabel==0.10.0 numpy==1.26.4 tqdm matplotlib pandas scipy
python run.py 2>&1 | tee reproduction/logs/official_run_after_manual_upload.log
```

Current core `run.py` defaults to `stonehenge`, not `flight`, and has no CLI scene selector. Do not edit `run.py`; if flight-specific smoke is required later, write a wrapper or documented temporary copy under `reproduction/`.

## Completion Note 2026-06-29

Manual upload has now been completed for `data` and `outputs`; this file remains as a recovery note. Current path check: `10/10 present`.
