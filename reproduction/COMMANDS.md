# SAFER-Splat Offline Baseline Commands

```bash
mkdir -p /disk1/zlab/projects
cd /disk1/zlab/projects
git clone https://github.com/chengine/safer-splat.git
# Full clone was too slow; the incomplete clone was removed and retried with:
git clone --depth 1 https://github.com/chengine/safer-splat.git
cd /disk1/zlab/projects/safer-splat
git branch codex/checkpoint-before-safer-offline-20260626_1603 HEAD
mkdir -p reproduction/logs reproduction/results reproduction/notes reproduction/scripts
git rev-parse HEAD > reproduction/notes/git_commit.txt
git log --oneline --max-count=5 > reproduction/notes/git_log_last5.txt
find . -maxdepth 3 -type f | sort > reproduction/notes/file_tree_depth3.txt
sed -n '1,260p' README.md
find . -maxdepth 3 \( -iname '*install*' -o -iname '*requirements*' -o -iname '*environment*' -o -iname '*docker*' \) -print
source ~/anaconda3/etc/profile.d/conda.sh
conda create -y -n safer_splat python=3.10
conda activate safer_splat
python -m pip install --upgrade pip
python -m pip install torch==2.1.2+cu118 torchvision==0.16.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
python -m pip install --no-cache-dir numpy==1.26.4 scipy clarabel==0.10.0 matplotlib pandas cvxpy osqp tqdm
which python | tee reproduction/notes/python_path.txt
python -V | tee reproduction/notes/python_version.txt
python -m pip freeze > reproduction/notes/pip_freeze.txt
conda list > reproduction/notes/conda_list.txt
python reproduction/scripts/test_distance_cbf_sanity.py 2>&1 | tee reproduction/logs/test_distance_cbf_sanity.log
python reproduction/scripts/run_offline_safety_filter_smoke.py 2>&1 | tee reproduction/logs/offline_safety_filter_smoke.log
git status --short
git diff --name-only
```

## Offline No-Filter Comparison Commands

Generated: 2026-06-26T17:42:36

```bash
cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
python reproduction/scripts/run_offline_filter_comparison.py 2>&1 | tee reproduction/logs/run_offline_filter_comparison.log
python reproduction/scripts/run_offline_filter_comparison_hardcase.py 2>&1 | tee reproduction/logs/run_offline_filter_comparison_hardcase.log
```
