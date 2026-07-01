#!/usr/bin/env python
"""Deterministic hardcase search for no-filter vs SAFER-Splat comparison.

The search uses real flight start-goal pairs from the existing official100 JSON
and the same real GSplat tensor/evaluator as the comparison script. It does not
use random data and does not alter the safety filter.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import torch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from run_offline_filter_comparison import (  # noqa: E402
    FIELDS,
    plot_comparison,
    run_rollout,
    write_summary,
    write_trajectory,
)

OUT_DIR = ROOT / "reproduction" / "results" / "offline_filter_comparison_hardcase"
CANDIDATE_TRIALS = [
    55, 46, 53,
    2, 3, 6, 8, 9, 10, 12, 15, 33, 35, 39, 42, 44, 45, 47, 49, 50, 51, 54,
    56, 58, 59, 62, 64, 65, 66, 83, 84, 86, 87, 95, 96, 97, 98,
]


def write_scan(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    keys = ["trial", "success", "collision", "minimum_clearance", "path_length", "num_steps", "wall_time_s"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in keys})


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    scan_rows: List[Dict[str, object]] = []
    print("Scanning deterministic candidate trials for no-filter low-clearance/collision cases...")
    for trial in CANDIDATE_TRIALS:
        result = run_rollout("no_filter", trial_index=trial)
        metrics = result["metrics"]
        scan_rows.append(metrics)
        print(f"trial={trial} collision={metrics['collision']} min_clearance={metrics['minimum_clearance']} success={metrics['success']}")
        if metrics["collision"]:
            break
    write_scan(OUT_DIR / "hardcase_scan_no_filter.csv", scan_rows)

    collisions = [r for r in scan_rows if r["collision"]]
    if collisions:
        selected = collisions[0]
        hardcase_found = True
        reason = "no_filter_collision"
    else:
        selected = min(scan_rows, key=lambda r: float(r["minimum_clearance"]))
        hardcase_found = False
        reason = "lowest_no_filter_clearance_without_collision"

    trial = int(selected["trial"])
    results = {
        "no_filter": run_rollout("no_filter", trial_index=trial),
        "safer_splat_filter": run_rollout("safer_splat_filter", trial_index=trial),
    }
    write_trajectory(OUT_DIR / "no_filter_trajectory.csv", results["no_filter"]["trajectory"])
    write_trajectory(OUT_DIR / "safer_splat_filter_trajectory.csv", results["safer_splat_filter"]["trajectory"])
    metric_rows = [results["no_filter"]["metrics"], results["safer_splat_filter"]["metrics"]]
    write_summary(OUT_DIR / "comparison_summary.csv", metric_rows)
    payload = {
        "hardcase_found": hardcase_found,
        "selection_reason": reason,
        "selected_trial": trial,
        "scan_candidate_trials": CANDIDATE_TRIALS,
        "metrics": {k: v["metrics"] for k, v in results.items()},
    }
    with (OUT_DIR / "comparison_metrics.json").open("w") as f:
        json.dump(payload, f, indent=2)
    plot_comparison(OUT_DIR / "comparison_plot.png", results)
    log = ["offline hardcase no-filter vs SAFER-Splat comparison", f"selected_trial={trial}", f"hardcase_found={hardcase_found}", f"reason={reason}"]
    for row in metric_rows:
        log.append(json.dumps(row, sort_keys=True))
    (OUT_DIR / "run_log.txt").write_text("\n".join(log) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
