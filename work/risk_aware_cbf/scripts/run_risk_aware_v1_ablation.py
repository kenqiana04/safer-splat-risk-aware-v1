#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py"

DEFAULT_CONFIGS = [
    ("A_budget1000_near008_hybrid", 1000, 0.08, "risk_v2_hybrid"),
    ("B_budget2000_near008_hybrid", 2000, 0.08, "risk_v2_hybrid"),
    ("C_budget5000_near008_hybrid", 5000, 0.08, "risk_v2_hybrid"),
    ("D_budget2000_near005_hybrid", 2000, 0.05, "risk_v2_hybrid"),
    ("E_budget2000_near012_hybrid", 2000, 0.12, "risk_v2_hybrid"),
    ("F_budget2000_near008_activefreq", 2000, 0.08, "risk_v0_active_frequency"),
    ("G_budget2000_near008_geometry", 2000, 0.08, "risk_v1_geometry"),
]

SUMMARY_FIELDS = [
    "ablation_id",
    "candidate_budget",
    "near_distance_threshold",
    "heading_distance_threshold",
    "heading_cos_threshold",
    "risk_score",
    "rows",
    "collision_count",
    "collision_free_count",
    "min_safety_h_min",
    "min_safety_h_mean",
    "progress_mean",
    "intervention_rate_mean",
    "control_deviation_mean",
    "active_constraints_mean",
    "runtime_mean",
    "runtime_p95",
    "qp_infeasible_count",
    "fallback_used_rate",
    "candidate_count_final_mean",
    "candidate_count_final_p95",
    "candidate_count_final_min",
    "candidate_count_final_max",
    "output_dir",
]


def log(handle, message: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
    print(line, flush=True)
    handle.write(line + "\n")
    handle.flush()


def parse_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def mean(values: list[float]) -> float | str:
    clean = [v for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(clean) / len(clean)) if clean else ""


def percentile(values: list[float], q: float) -> float | str:
    clean = [v for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return ""
    return float(pd.Series(clean).quantile(q / 100.0))


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def default_configs() -> list[dict[str, Any]]:
    return [
        {
            "ablation_id": label,
            "candidate_budget": budget,
            "near_distance_threshold": near,
            "risk_score": risk,
        }
        for label, budget, near, risk in DEFAULT_CONFIGS
    ]


def all_combo_configs(candidate_budgets: str, near_thresholds: str, risk_scores: str) -> list[dict[str, Any]]:
    budgets = [int(x.strip()) for x in candidate_budgets.split(",") if x.strip()]
    nears = [float(x.strip()) for x in near_thresholds.split(",") if x.strip()]
    risks = [x.strip() for x in risk_scores.split(",") if x.strip()]
    configs = []
    for budget in budgets:
        for near in nears:
            for risk in risks:
                near_label = f"{near:.2f}".replace(".", "")
                risk_label = risk.replace("risk_", "")
                configs.append(
                    {
                        "ablation_id": f"budget{budget}_near{near_label}_{risk_label}",
                        "candidate_budget": budget,
                        "near_distance_threshold": near,
                        "risk_score": risk,
                    }
                )
    return configs


def command_for_config(args: argparse.Namespace, config: dict[str, Any], output_dir: Path) -> list[str]:
    cmd = [
        sys.executable,
        str(RUNNER),
        "--scene",
        args.scene,
        "--methods",
        "risk_aware_v1_pre_cbf",
        "--trial-start",
        str(args.trial_start),
        "--trial-end",
        str(args.trial_end),
        "--max-steps",
        str(args.max_steps),
        "--candidate-budget",
        str(config["candidate_budget"]),
        "--near-distance-threshold",
        str(config["near_distance_threshold"]),
        "--heading-distance-threshold",
        str(args.heading_distance_threshold),
        "--heading-cos-threshold",
        str(args.heading_cos_threshold),
        "--risk-score",
        config["risk_score"],
        "--output-dir",
        str(output_dir),
        "--device",
        args.device,
    ]
    if args.resume:
        cmd.append("--resume")
    if args.skip_existing:
        cmd.append("--skip-existing")
    return cmd


def debug_stats(path: Path) -> dict[str, Any]:
    rows = load_csv(path)
    if not rows:
        return {
            "fallback_used_rate": "",
            "candidate_count_final_mean": "",
            "candidate_count_final_p95": "",
            "candidate_count_final_min": "",
            "candidate_count_final_max": "",
        }
    fallback = []
    candidates = []
    for row in rows:
        text = str(row.get("fallback_used", "")).strip().lower()
        if text in {"true", "1", "yes"}:
            fallback.append(1.0)
        elif text in {"false", "0", "no"}:
            fallback.append(0.0)
        value = parse_float(row.get("candidate_count_final"))
        if value is not None:
            candidates.append(value)
    return {
        "fallback_used_rate": mean(fallback),
        "candidate_count_final_mean": mean(candidates),
        "candidate_count_final_p95": percentile(candidates, 95),
        "candidate_count_final_min": min(candidates) if candidates else "",
        "candidate_count_final_max": max(candidates) if candidates else "",
    }


def summary_for_config(
    *,
    config: dict[str, Any],
    output_dir: Path,
    heading_distance_threshold: float,
    heading_cos_threshold: float,
) -> dict[str, Any]:
    rows = load_csv(output_dir / "summary.csv")
    risk_row = next((row for row in rows if row.get("method") == "risk_aware_v1_pre_cbf"), None)
    if risk_row is None:
        out = {field: "" for field in SUMMARY_FIELDS}
        out.update(
            {
                "ablation_id": config["ablation_id"],
                "candidate_budget": config["candidate_budget"],
                "near_distance_threshold": config["near_distance_threshold"],
                "heading_distance_threshold": heading_distance_threshold,
                "heading_cos_threshold": heading_cos_threshold,
                "risk_score": config["risk_score"],
                "output_dir": str(output_dir),
            }
        )
        return out

    stats = debug_stats(output_dir / "v1_candidate_debug.csv")
    return {
        "ablation_id": config["ablation_id"],
        "candidate_budget": config["candidate_budget"],
        "near_distance_threshold": config["near_distance_threshold"],
        "heading_distance_threshold": heading_distance_threshold,
        "heading_cos_threshold": heading_cos_threshold,
        "risk_score": config["risk_score"],
        "rows": risk_row.get("rows", ""),
        "collision_count": risk_row.get("collision_count", ""),
        "collision_free_count": risk_row.get("collision_free_count", ""),
        "min_safety_h_min": risk_row.get("min_safety_h_min", ""),
        "min_safety_h_mean": risk_row.get("min_safety_h_mean", ""),
        "progress_mean": risk_row.get("goal_distance_reduction_ratio_mean", ""),
        "intervention_rate_mean": risk_row.get("intervention_rate_mean", ""),
        "control_deviation_mean": risk_row.get("control_deviation_mean_mean", ""),
        "active_constraints_mean": risk_row.get("active_constraints_mean_mean", ""),
        "runtime_mean": risk_row.get("runtime_mean_mean", ""),
        "runtime_p95": risk_row.get("runtime_p95_mean", ""),
        "qp_infeasible_count": risk_row.get("qp_infeasible_count_sum", ""),
        "fallback_used_rate": stats["fallback_used_rate"],
        "candidate_count_final_mean": stats["candidate_count_final_mean"],
        "candidate_count_final_p95": stats["candidate_count_final_p95"],
        "candidate_count_final_min": stats["candidate_count_final_min"],
        "candidate_count_final_max": stats["candidate_count_final_max"],
        "output_dir": str(output_dir),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_trials(output_dir: Path, configs: list[dict[str, Any]]) -> None:
    merged: list[dict[str, Any]] = []
    fields: list[str] | None = None
    for config in configs:
        config_dir = output_dir / config["ablation_id"]
        rows = load_csv(config_dir / "trials.csv")
        for row in rows:
            if row.get("method") != "risk_aware_v1_pre_cbf":
                continue
            out = {
                "ablation_id": config["ablation_id"],
                "candidate_budget": config["candidate_budget"],
                "near_distance_threshold": config["near_distance_threshold"],
                "risk_score": config["risk_score"],
            }
            out.update(row)
            merged.append(out)
            if fields is None:
                fields = list(out.keys())
    if fields is None:
        fields = ["ablation_id", "candidate_budget", "near_distance_threshold", "risk_score"]
    write_csv(output_dir / "ablation_trials.csv", merged, fields)


def write_plot(output_dir: Path, summaries: list[dict[str, Any]]) -> None:
    if not summaries:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    table = pd.DataFrame(summaries)
    metrics = [
        "collision_count",
        "min_safety_h_min",
        "progress_mean",
        "active_constraints_mean",
        "runtime_mean",
        "candidate_count_final_mean",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        values = pd.to_numeric(table[metric], errors="coerce").fillna(0.0)
        ax.bar(table["ablation_id"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "ablation_plots.png", dpi=180)
    plt.close(fig)


def read_baseline_summary(path: Path) -> dict[str, Any]:
    rows = load_csv(path)
    row = next((r for r in rows if r.get("method") == "safer_splat_filter"), None)
    if row is None:
        return {}
    return {
        "source": str(path),
        "rows": row.get("rows", ""),
        "collision_count": row.get("collision_count", ""),
        "min_safety_h_min": row.get("min_safety_h_min", ""),
        "progress_mean": row.get("goal_distance_reduction_ratio_mean", ""),
        "active_constraints_mean": row.get("active_constraints_mean_mean", ""),
        "runtime_mean": row.get("runtime_mean_mean", ""),
        "runtime_p95": row.get("runtime_p95_mean", ""),
        "qp_infeasible_count": row.get("qp_infeasible_count_sum", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Risk-Aware V1 pre-CBF stonehenge ablation.")
    parser.add_argument("--scene", default="stonehenge")
    parser.add_argument("--trial-start", type=int, default=0)
    parser.add_argument("--trial-end", type=int, default=19)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--heading-distance-threshold", type=float, default=0.25)
    parser.add_argument("--heading-cos-threshold", type=float, default=0.5)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--output-dir", "--output-root", type=Path, default=Path("work/risk_aware_cbf/results/risk_aware_v1_ablation_stonehenge_20"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all-combinations", action="store_true")
    parser.add_argument("--candidate-budgets", default="1000,2000,5000")
    parser.add_argument("--near-distance-thresholds", default="0.05,0.08,0.12")
    parser.add_argument("--risk-scores", default="risk_v0_active_frequency,risk_v1_geometry,risk_v2_hybrid")
    parser.add_argument("--baseline-summary", type=Path, default=Path("work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20/summary.csv"))
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    run_log = output_dir / "run_log.txt"
    configs = (
        all_combo_configs(args.candidate_budgets, args.near_distance_thresholds, args.risk_scores)
        if args.all_combinations
        else default_configs()
    )

    with run_log.open("a", encoding="utf-8") as handle:
        log(handle, f"script={Path(__file__).resolve()}")
        log(handle, f"scene={args.scene} trials={args.trial_start}-{args.trial_end} configs={len(configs)}")
        log(handle, f"baseline_summary_reused={args.baseline_summary}")
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "runner": str(RUNNER),
            "scene": args.scene,
            "trial_start": args.trial_start,
            "trial_end": args.trial_end,
            "max_steps": args.max_steps,
            "heading_distance_threshold": args.heading_distance_threshold,
            "heading_cos_threshold": args.heading_cos_threshold,
            "baseline_reference": read_baseline_summary(args.baseline_summary),
            "note": "SAFER-Splat baseline is reused from the existing 20-trial V1 comparison to avoid rerunning an identical baseline per ablation config.",
            "configs": [],
        }

        for config in configs:
            config_dir = output_dir / config["ablation_id"]
            config_dir.mkdir(parents=True, exist_ok=True)
            cmd = command_for_config(args, config, config_dir)
            manifest["configs"].append({**config, "output_dir": str(config_dir), "command": cmd})
            (config_dir / "ablation_command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
            log(handle, f"config_start {config['ablation_id']} command={' '.join(cmd)}")
            if not args.dry_run:
                subprocess.run(cmd, check=True)
            else:
                log(handle, f"dry_run_skip {config['ablation_id']}")
            log(handle, f"config_done {config['ablation_id']}")

        (output_dir / "ablation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        summaries = [
            summary_for_config(
                config=config,
                output_dir=output_dir / config["ablation_id"],
                heading_distance_threshold=args.heading_distance_threshold,
                heading_cos_threshold=args.heading_cos_threshold,
            )
            for config in configs
        ]
        write_csv(output_dir / "ablation_summary.csv", summaries, SUMMARY_FIELDS)
        write_trials(output_dir, configs)
        write_plot(output_dir, summaries)
        metrics = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "baseline_reference": read_baseline_summary(args.baseline_summary),
            "summary": summaries,
        }
        (output_dir / "ablation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        log(handle, f"wrote={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
