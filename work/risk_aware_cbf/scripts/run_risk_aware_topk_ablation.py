#!/usr/bin/env python3
"""Run a small 20-trial ablation for wrapper-level risk-aware top-k V0."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "work" / "risk_aware_cbf" / "scripts" / "run_risk_aware_topk_comparison.py"

CONFIGS = [
    {"ablation_id": "A_topk150_h0006_hybrid", "topk": 150, "h_critical": 0.0006, "risk_score": "risk_v2_hybrid"},
    {"ablation_id": "B_topk300_h0006_hybrid", "topk": 300, "h_critical": 0.0006, "risk_score": "risk_v2_hybrid"},
    {"ablation_id": "C_topk500_h0006_hybrid", "topk": 500, "h_critical": 0.0006, "risk_score": "risk_v2_hybrid"},
    {"ablation_id": "D_topk300_h0004_hybrid", "topk": 300, "h_critical": 0.0004, "risk_score": "risk_v2_hybrid"},
    {"ablation_id": "E_topk300_h0010_hybrid", "topk": 300, "h_critical": 0.0010, "risk_score": "risk_v2_hybrid"},
    {"ablation_id": "F_topk300_h0006_activefreq", "topk": 300, "h_critical": 0.0006, "risk_score": "risk_v0_active_frequency"},
    {"ablation_id": "G_topk300_h0006_geometry", "topk": 300, "h_critical": 0.0006, "risk_score": "risk_v1_geometry"},
]


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = self.path.open("a", encoding="utf-8")

    def log(self, message: str) -> None:
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
        print(line, flush=True)
        self.fh.write(line + "\n")
        self.fh.flush()

    def close(self) -> None:
        self.fh.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="stonehenge")
    parser.add_argument("--trial-start", type=int, default=0)
    parser.add_argument("--trial-end", type=int, default=19)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--near-distance-threshold", type=float, default=0.05)
    parser.add_argument("--output-dir", type=Path, default=Path("work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    return parser.parse_args()


def read_debug_rate(path: Path) -> tuple[float | str, float | str]:
    debug_path = path / "risk_aware_selection_debug.csv"
    if not debug_path.exists() or debug_path.stat().st_size == 0:
        return "", ""
    debug = pd.read_csv(debug_path)
    if debug.empty:
        return "", ""
    fallback = debug["fallback_used"].astype(str).str.lower().isin(["true", "1", "yes"])
    selected = pd.to_numeric(debug["risk_aware_selected_count"], errors="coerce")
    return float(fallback.mean()), float(selected.mean())


def aggregate(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    trial_frames = []
    summary_rows: list[dict[str, Any]] = []
    for cfg in CONFIGS:
        run_dir = output_dir / cfg["ablation_id"]
        trials_path = run_dir / "trials.csv"
        summary_path = run_dir / "summary.csv"
        if trials_path.exists():
            trials = pd.read_csv(trials_path)
            for key, value in cfg.items():
                trials[key] = value
            trial_frames.append(trials)
        row: dict[str, Any] = dict(cfg)
        if summary_path.exists():
            summary = pd.read_csv(summary_path)
            hit = summary[summary["method"] == "risk_aware_topk_v0"]
            if not hit.empty:
                s = hit.iloc[0].to_dict()
                row.update(
                    {
                        "rows": s.get("rows", ""),
                        "collision_count": s.get("collision_count", ""),
                        "collision_free_count": s.get("collision_free_count", ""),
                        "min_safety_h_min": s.get("min_safety_h_min", ""),
                        "min_safety_h_mean": s.get("min_safety_h_mean", ""),
                        "goal_distance_reduction_ratio_mean": s.get("goal_distance_reduction_ratio_mean", ""),
                        "intervention_rate_mean": s.get("intervention_rate_mean", ""),
                        "control_deviation_mean": s.get("control_deviation_mean_mean", ""),
                        "active_constraints_mean": s.get("active_constraints_mean_mean", ""),
                        "runtime_mean": s.get("runtime_mean_mean", ""),
                        "runtime_p95": s.get("runtime_p95_mean", ""),
                        "qp_infeasible_count": s.get("qp_infeasible_count_sum", ""),
                    }
                )
        fallback_rate, selected_mean = read_debug_rate(run_dir)
        row["fallback_used_rate"] = fallback_rate
        row["risk_aware_selected_count_debug_mean"] = selected_mean
        summary_rows.append(row)
    trials_out = pd.concat(trial_frames, ignore_index=True) if trial_frames else pd.DataFrame()
    summary_out = pd.DataFrame(summary_rows)
    return trials_out, summary_out


def write_plot(summary: pd.DataFrame, output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = [
        "collision_count",
        "min_safety_h_min",
        "goal_distance_reduction_ratio_mean",
        "active_constraints_mean",
        "runtime_mean",
        "fallback_used_rate",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        values = pd.to_numeric(summary[metric], errors="coerce").fillna(0.0)
        ax.bar(summary["ablation_id"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=75, labelsize=7)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def run_config(args: argparse.Namespace, cfg: dict[str, Any], logger: Logger) -> int:
    run_dir = args.output_dir / cfg["ablation_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(SCRIPT),
        "--scene",
        args.scene,
        "--methods",
        "risk_aware_topk_v0",
        "--trial-start",
        str(args.trial_start),
        "--trial-end",
        str(args.trial_end),
        "--max-steps",
        str(args.max_steps),
        "--topk",
        str(cfg["topk"]),
        "--h-critical",
        str(cfg["h_critical"]),
        "--near-distance-threshold",
        str(args.near_distance_threshold),
        "--risk-score",
        str(cfg["risk_score"]),
        "--output-dir",
        str(run_dir),
        "--device",
        args.device,
    ]
    if args.resume:
        command.append("--resume")
    if args.skip_existing:
        command.append("--skip-existing")
    logger.log("start " + cfg["ablation_id"] + " command=" + " ".join(command))
    with (run_dir / "ablation_command.log").open("a", encoding="utf-8") as fh:
        fh.write(" ".join(command) + "\n")
        result = subprocess.run(command, stdout=fh, stderr=subprocess.STDOUT, cwd=ROOT)
    logger.log(f"done {cfg['ablation_id']} returncode={result.returncode}")
    return int(result.returncode)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger = Logger(args.output_dir / "run_log.txt")
    return_codes: dict[str, int] = {}
    try:
        logger.log(f"script={Path(__file__).resolve()}")
        logger.log(f"configs={len(CONFIGS)} trials={args.trial_start}-{args.trial_end}")
        for cfg in CONFIGS:
            return_codes[cfg["ablation_id"]] = run_config(args, cfg, logger)
            trials, summary = aggregate(args.output_dir)
            trials.to_csv(args.output_dir / "ablation_trials.csv", index=False)
            summary.to_csv(args.output_dir / "ablation_summary.csv", index=False)
            write_plot(summary, args.output_dir / "ablation_plots.png")

        trials, summary = aggregate(args.output_dir)
        trials.to_csv(args.output_dir / "ablation_trials.csv", index=False)
        summary.to_csv(args.output_dir / "ablation_summary.csv", index=False)
        write_plot(summary, args.output_dir / "ablation_plots.png")
        metrics = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "configs": CONFIGS,
            "trial_start": args.trial_start,
            "trial_end": args.trial_end,
            "return_codes": return_codes,
            "summary_csv": str(args.output_dir / "ablation_summary.csv"),
        }
        (args.output_dir / "ablation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        logger.log(f"wrote={args.output_dir}")
        return 0 if all(code == 0 for code in return_codes.values()) else 1
    finally:
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
