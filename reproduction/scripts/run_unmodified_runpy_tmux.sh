#!/usr/bin/env bash
set -euo pipefail

cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate /disk1/zlab/conda_envs/safer_splat_official
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-1}"
export PYTHONDONTWRITEBYTECODE=1

python run.py 2>&1 | tee reproduction/logs/unmodified_runpy_full_$(date +%Y%m%d_%H%M%S).log
