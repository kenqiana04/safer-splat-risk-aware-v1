#!/usr/bin/env bash
set -euo pipefail

cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate /disk1/zlab/conda_envs/safer_splat_official
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-1}"
export PYTHONDONTWRITEBYTECODE=1

python reproduction/scripts/run_official_checkpoint_filter_comparison.py \
  --scene stonehenge \
  --methods no_filter safer_splat_filter \
  --trial-start 0 \
  --trial-end 99 \
  --max-steps 800 \
  --output-dir reproduction/results/official_checkpoint_filter_comparison_stonehenge_100 \
  --resume \
  --skip-existing \
  2>&1 | tee reproduction/logs/official_checkpoint_filter_comparison_stonehenge_100.log
