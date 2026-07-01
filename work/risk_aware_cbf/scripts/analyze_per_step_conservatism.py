#!/usr/bin/env python3
"""Analyze per-step conservatism from baseline detailed logging outputs.

This script consumes artifacts produced by run_baseline_with_detailed_logging.py.
It does not run rollouts and does not modify SAFER-Splat controller code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_BASE = Path("work/risk_aware_cbf")
DEFAULT_RESULTS = DEFAULT_BASE / "results"
DEFAULT_INPUT_DIR = DEFAULT_RESULTS / "baseline_detailed_logging_stonehenge_100"


SUMMARY_COLUMNS = [
    "metric",
    "value",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument(
        "--gaussian-attributes",
        type=Path,
        default=DEFAULT_RESULTS / "stonehenge_gaussian_attributes.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=DEFAULT_BASE / "figures",
    )
    parser.add_argument(
        "--notes-dir",
        type=Path,
        default=DEFAULT_BASE / "notes",
    )
    parser.add_argument("--top-k-steps", type=int, default=200)
    parser.add_argument("--plot-sample", type=int, default=30000)
    return parser.parse_args()


def read_csv(path: Path, *, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return pd.DataFrame()
    return pd.read_csv(path)


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def scalar(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if pd.isna(value):
        return ""
    return value


def add_summary(rows: list[dict[str, Any]], metric: str, value: Any, note: str = "") -> None:
    rows.append({"metric": metric, "value": scalar(value), "note": note})


def finite_corr(a: pd.Series, b: pd.Series) -> float:
    frame = pd.DataFrame({"a": a, "b": b}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 3:
        return float("nan")
    if frame["a"].nunique() < 2 or frame["b"].nunique() < 2:
        return float("nan")
    return float(frame["a"].corr(frame["b"]))


def prepare_per_step(per_step: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "trial",
        "step",
        "time",
        "x",
        "y",
        "z",
        "vx",
        "vy",
        "vz",
        "goal_distance",
        "control_deviation",
        "min_safety_h_step",
        "runtime_step",
        "active_constraints_count",
    ]
    per_step = to_numeric(per_step.copy(), numeric_cols)
    trials = to_numeric(trials.copy(), ["trial", "initial_goal_distance"])
    per_step = per_step.sort_values(["method", "trial", "step"]).reset_index(drop=True)
    initial = trials[["method", "trial", "initial_goal_distance"]].drop_duplicates()
    per_step = per_step.merge(initial, on=["method", "trial"], how="left")
    previous = per_step.groupby(["method", "trial"])["goal_distance"].shift(1)
    previous = previous.fillna(per_step["initial_goal_distance"])
    per_step["goal_progress_delta"] = previous - per_step["goal_distance"]
    per_step["goal_progress_delta_abs"] = per_step["goal_progress_delta"].abs()
    return per_step


def summarize_per_step(
    trials: pd.DataFrame,
    per_step: pd.DataFrame,
    active: pd.DataFrame,
    active_ids_available: bool,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    add_summary(rows, "trial_rows", len(trials))
    add_summary(rows, "per_step_rows", len(per_step))
    add_summary(rows, "active_constraint_rows", len(active))
    add_summary(rows, "methods", ",".join(sorted(map(str, trials["method"].dropna().unique()))))
    add_summary(rows, "trial_min", trials["trial"].min())
    add_summary(rows, "trial_max", trials["trial"].max())
    add_summary(rows, "unique_trials", trials["trial"].nunique())
    add_summary(rows, "active_gaussian_ids_available", "yes" if active_ids_available else "no")

    numeric_metrics = {
        "control_deviation_mean": per_step["control_deviation"].mean(),
        "control_deviation_p95": per_step["control_deviation"].quantile(0.95),
        "control_deviation_max": per_step["control_deviation"].max(),
        "active_constraints_count_mean": per_step["active_constraints_count"].mean(),
        "active_constraints_count_p95": per_step["active_constraints_count"].quantile(0.95),
        "active_constraints_count_max": per_step["active_constraints_count"].max(),
        "runtime_step_mean_s": per_step["runtime_step"].mean(),
        "runtime_step_p95_s": per_step["runtime_step"].quantile(0.95),
        "runtime_step_max_s": per_step["runtime_step"].max(),
        "min_safety_h_step_min": per_step["min_safety_h_step"].min(),
        "min_safety_h_step_mean": per_step["min_safety_h_step"].mean(),
        "goal_progress_delta_mean": per_step["goal_progress_delta"].mean(),
        "goal_progress_delta_p05": per_step["goal_progress_delta"].quantile(0.05),
        "goal_progress_delta_min": per_step["goal_progress_delta"].min(),
        "corr_control_deviation_vs_goal_progress_delta": finite_corr(
            per_step["control_deviation"], per_step["goal_progress_delta"]
        ),
        "corr_control_deviation_vs_min_safety_h_step": finite_corr(
            per_step["control_deviation"], per_step["min_safety_h_step"]
        ),
        "corr_active_constraints_count_vs_runtime_step": finite_corr(
            per_step["active_constraints_count"], per_step["runtime_step"]
        ),
        "corr_active_constraints_count_vs_control_deviation": finite_corr(
            per_step["active_constraints_count"], per_step["control_deviation"]
        ),
    }
    for metric, value in numeric_metrics.items():
        add_summary(rows, metric, value)

    high_cut = per_step["control_deviation"].quantile(0.95)
    high = per_step[per_step["control_deviation"] >= high_cut]
    add_summary(rows, "high_intervention_threshold_p95", high_cut)
    add_summary(rows, "high_intervention_rows", len(high))
    add_summary(rows, "high_intervention_goal_progress_delta_mean", high["goal_progress_delta"].mean())
    add_summary(rows, "high_intervention_min_safety_h_step_mean", high["min_safety_h_step"].mean())
    add_summary(rows, "high_intervention_active_constraints_count_mean", high["active_constraints_count"].mean())
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_high_intervention_steps(per_step: pd.DataFrame, output_path: Path, top_k: int) -> pd.DataFrame:
    cols = [
        "scene",
        "method",
        "trial",
        "step",
        "time",
        "x",
        "y",
        "z",
        "goal_distance",
        "goal_progress_delta",
        "control_deviation",
        "min_safety_h_step",
        "active_constraints_count",
        "runtime_step",
        "qp_feasible",
        "collision_step",
    ]
    cols = [col for col in cols if col in per_step.columns]
    high = per_step.sort_values("control_deviation", ascending=False).head(top_k)[cols].copy()
    high.to_csv(output_path, index=False)
    return high


def prepare_active(active: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    if active.empty or "gaussian_id" not in active.columns:
        return active.copy(), False
    active = active.copy()
    active["gaussian_id_numeric"] = pd.to_numeric(active["gaussian_id"], errors="coerce")
    active_ids_available = active["gaussian_id_numeric"].notna().any()
    numeric_cols = [
        "trial",
        "step",
        "candidate_rank",
        "h_value",
        "distance_or_safety_value",
        "scale_x",
        "scale_y",
        "scale_z",
        "max_scale",
        "anisotropy",
        "opacity",
        "volume_proxy",
        "distance_to_robot",
        "heading_alignment_proxy",
    ]
    active = to_numeric(active, numeric_cols)
    return active, bool(active_ids_available)


def write_active_frequency(active: pd.DataFrame, attrs: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    if active.empty or "gaussian_id_numeric" not in active.columns:
        out = pd.DataFrame([{"note": "active Gaussian IDs unavailable"}])
        out.to_csv(output_path, index=False)
        return out

    active_with_id = active.dropna(subset=["gaussian_id_numeric"]).copy()
    if active_with_id.empty:
        out = pd.DataFrame([{"note": "active Gaussian IDs unavailable"}])
        out.to_csv(output_path, index=False)
        return out

    active_with_id["gaussian_id"] = active_with_id["gaussian_id_numeric"].astype(np.int64)
    grouped = (
        active_with_id.groupby("gaussian_id")
        .agg(
            active_event_count=("gaussian_id", "size"),
            active_trial_count=("trial", "nunique"),
            active_step_count=("step", "nunique"),
            h_value_min=("h_value", "min"),
            h_value_mean=("h_value", "mean"),
            candidate_rank_mean=("candidate_rank", "mean"),
            opacity_logged_mean=("opacity", "mean"),
            max_scale_logged_mean=("max_scale", "mean"),
            anisotropy_logged_mean=("anisotropy", "mean"),
            volume_proxy_logged_mean=("volume_proxy", "mean"),
            distance_to_robot_mean=("distance_to_robot", "mean"),
            heading_alignment_proxy_mean=("heading_alignment_proxy", "mean"),
        )
        .reset_index()
        .sort_values(["active_event_count", "active_trial_count", "h_value_min"], ascending=[False, False, True])
    )
    if not attrs.empty and "gaussian_id" in attrs.columns:
        attrs = attrs.copy()
        attrs["gaussian_id"] = pd.to_numeric(attrs["gaussian_id"], errors="coerce").astype("Int64")
        grouped = grouped.merge(attrs, on="gaussian_id", how="left", suffixes=("", "_scene"))
    grouped.to_csv(output_path, index=False)
    return grouped


def attribute_summary(active: pd.DataFrame, attrs: pd.DataFrame, freq: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    attributes = ["opacity", "max_scale", "mean_scale", "anisotropy", "volume_proxy", "distance_to_scene_center"]
    if freq.empty or "gaussian_id" not in freq.columns or "active_event_count" not in freq.columns:
        out = pd.DataFrame([{"note": "active Gaussian IDs unavailable"}])
        out.to_csv(output_path, index=False)
        return out

    rows: list[dict[str, Any]] = []
    if not attrs.empty and "gaussian_id" in attrs.columns:
        attrs = attrs.copy()
        attrs["gaussian_id"] = pd.to_numeric(attrs["gaussian_id"], errors="coerce").astype("Int64")
        active_ids = freq[["gaussian_id", "active_event_count"]].copy()
        active_ids["gaussian_id"] = pd.to_numeric(active_ids["gaussian_id"], errors="coerce").astype("Int64")
        active_attrs = active_ids.merge(attrs, on="gaussian_id", how="left")
        top_ids = active_ids.sort_values("active_event_count", ascending=False).head(100)
        top_attrs = top_ids.merge(attrs, on="gaussian_id", how="left")
        for attr in attributes:
            if attr not in attrs.columns:
                continue
            full_values = pd.to_numeric(attrs[attr], errors="coerce")
            active_values = pd.to_numeric(active_attrs[attr], errors="coerce")
            top_values = pd.to_numeric(top_attrs[attr], errors="coerce")
            weights = pd.to_numeric(active_attrs["active_event_count"], errors="coerce").fillna(0.0)
            weighted_mean = np.average(active_values.fillna(0.0), weights=weights) if weights.sum() > 0 else np.nan
            rows.append(
                {
                    "attribute": attr,
                    "full_scene_mean": full_values.mean(),
                    "full_scene_median": full_values.median(),
                    "active_unique_mean": active_values.mean(),
                    "active_unique_median": active_values.median(),
                    "active_event_weighted_mean": weighted_mean,
                    "top100_active_mean": top_values.mean(),
                    "top100_active_median": top_values.median(),
                }
            )
    if not rows:
        for attr in ["opacity", "max_scale", "anisotropy", "volume_proxy"]:
            if attr in active.columns:
                values = pd.to_numeric(active[attr], errors="coerce")
                rows.append(
                    {
                        "attribute": attr,
                        "active_event_weighted_mean": values.mean(),
                        "active_unique_mean": values.mean(),
                        "note": "scene-wide attributes unavailable; values from active constraint log",
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(output_path, index=False)
    return out


def make_plots(per_step: pd.DataFrame, output_path: Path, plot_sample: int) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_df = per_step.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["control_deviation", "min_safety_h_step", "active_constraints_count", "runtime_step"]
    )
    if len(plot_df) > plot_sample:
        plot_df = plot_df.sample(plot_sample, random_state=0)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes[0, 0].scatter(plot_df["min_safety_h_step"], plot_df["control_deviation"], s=4, alpha=0.25)
    axes[0, 0].set_xlabel("min_safety_h_step (official h, not meters)")
    axes[0, 0].set_ylabel("control_deviation")
    axes[0, 0].set_title("Intervention vs safety h")

    axes[0, 1].scatter(plot_df["active_constraints_count"], plot_df["runtime_step"], s=4, alpha=0.25)
    axes[0, 1].set_xlabel("active_constraints_count")
    axes[0, 1].set_ylabel("runtime_step (s)")
    axes[0, 1].set_title("Active constraints vs runtime")

    valid_progress = plot_df.dropna(subset=["goal_progress_delta"])
    axes[1, 0].scatter(valid_progress["control_deviation"], valid_progress["goal_progress_delta"], s=4, alpha=0.25)
    axes[1, 0].set_xlabel("control_deviation")
    axes[1, 0].set_ylabel("goal_progress_delta")
    axes[1, 0].set_title("Intervention vs goal progress")

    axes[1, 1].hist(plot_df["control_deviation"].dropna(), bins=60)
    axes[1, 1].set_xlabel("control_deviation")
    axes[1, 1].set_ylabel("step count")
    axes[1, 1].set_title("Intervention distribution")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def summary_value(summary: pd.DataFrame, metric: str, default: str = "") -> str:
    hit = summary.loc[summary["metric"] == metric, "value"]
    if hit.empty:
        return default
    return str(hit.iloc[0])


def write_markdown(
    *,
    output_path: Path,
    input_dir: Path,
    summary: pd.DataFrame,
    high_steps: pd.DataFrame,
    freq: pd.DataFrame,
    attr_summary: pd.DataFrame,
    plot_path: Path,
) -> None:
    active_available = summary_value(summary, "active_gaussian_ids_available") == "yes"
    top_freq = pd.DataFrame()
    if active_available and "active_event_count" in freq.columns:
        top_freq = freq.head(10)

    lines: list[str] = []
    lines.append("# Per-Step Conservatism Analysis")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "This analysis uses baseline detailed logging outputs only. It does not implement a risk-aware CBF controller and does not modify the official SAFER-Splat baseline."
    )
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Input directory: `{input_dir}`")
    lines.append("- `min_safety_h_step` is the official GSplat safety h value, not a meter clearance.")
    lines.append("- Active constraints are logged as the lowest-h selected baseline constraints up to the configured per-step limit.")
    lines.append("")
    lines.append("## Logging Coverage")
    lines.append("")
    for metric in [
        "trial_rows",
        "per_step_rows",
        "active_constraint_rows",
        "methods",
        "trial_min",
        "trial_max",
        "unique_trials",
        "active_gaussian_ids_available",
    ]:
        lines.append(f"- {metric}: {summary_value(summary, metric)}")
    lines.append("")
    lines.append("## Per-Step Findings")
    lines.append("")
    for metric in [
        "control_deviation_mean",
        "control_deviation_p95",
        "control_deviation_max",
        "active_constraints_count_mean",
        "active_constraints_count_p95",
        "active_constraints_count_max",
        "runtime_step_mean_s",
        "runtime_step_p95_s",
        "min_safety_h_step_min",
        "min_safety_h_step_mean",
        "corr_control_deviation_vs_goal_progress_delta",
        "corr_control_deviation_vs_min_safety_h_step",
        "corr_active_constraints_count_vs_runtime_step",
        "corr_active_constraints_count_vs_control_deviation",
        "high_intervention_threshold_p95",
        "high_intervention_rows",
        "high_intervention_goal_progress_delta_mean",
        "high_intervention_min_safety_h_step_mean",
    ]:
        lines.append(f"- {metric}: {summary_value(summary, metric)}")
    if not high_steps.empty:
        row = high_steps.iloc[0]
        lines.append(
            f"- Max intervention step: trial {int(row['trial'])}, step {int(row['step'])}, control_deviation {row['control_deviation']:.6g}, min_safety_h_step {row['min_safety_h_step']:.6g}."
        )
    lines.append("")
    lines.append("## Active Gaussian Findings")
    lines.append("")
    if active_available and not top_freq.empty:
        lines.append(f"- Unique active Gaussian IDs: {len(freq)}")
        lines.append("- Top active Gaussian IDs by logged event count:")
        for _, row in top_freq.iterrows():
            lines.append(
                f"  - gaussian_id {int(row['gaussian_id'])}: events {int(row['active_event_count'])}, trials {int(row['active_trial_count'])}, h_min {row['h_value_min']:.6g}"
            )
        lines.append("")
        if not attr_summary.empty and "attribute" in attr_summary.columns:
            lines.append("- Attribute summary is available in `active_gaussian_attribute_summary.csv`; it compares full-scene Gaussians with active logged Gaussians.")
    else:
        lines.append("- Active Gaussian IDs were not available; analysis is limited to active constraint counts.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `work/risk_aware_cbf/results/per_step_conservatism_summary.csv`")
    lines.append("- `work/risk_aware_cbf/results/high_intervention_steps.csv`")
    lines.append("- `work/risk_aware_cbf/results/active_gaussian_frequency.csv`")
    lines.append("- `work/risk_aware_cbf/results/active_gaussian_attribute_summary.csv`")
    lines.append(f"- `{plot_path}`")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- The active constraint log is a bounded diagnostic sample of selected constraints, not a full dense dump of every selected Gaussian at every step.")
    lines.append("- The results support baseline diagnosis and GO/NO-GO planning, but they are not a new method result.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    args.notes_dir.mkdir(parents=True, exist_ok=True)

    trials = read_csv(args.input_dir / "trials.csv")
    per_step_raw = read_csv(args.input_dir / "per_step_trajectory.csv")
    active_raw = read_csv(args.input_dir / "active_constraints.csv", required=False)
    attrs = read_csv(args.gaussian_attributes, required=False)

    per_step = prepare_per_step(per_step_raw, trials)
    active, active_ids_available = prepare_active(active_raw)

    summary = summarize_per_step(trials, per_step, active, active_ids_available)
    summary_path = args.output_dir / "per_step_conservatism_summary.csv"
    summary.to_csv(summary_path, index=False)

    high_steps = write_high_intervention_steps(
        per_step,
        args.output_dir / "high_intervention_steps.csv",
        args.top_k_steps,
    )
    freq = write_active_frequency(active, attrs, args.output_dir / "active_gaussian_frequency.csv")
    attr_summary = attribute_summary(
        active,
        attrs,
        freq,
        args.output_dir / "active_gaussian_attribute_summary.csv",
    )
    plot_path = args.figures_dir / "per_step_conservatism_plots.png"
    make_plots(per_step, plot_path, args.plot_sample)
    report_path = args.notes_dir / "PER_STEP_CONSERVATISM_ANALYSIS.md"
    write_markdown(
        output_path=report_path,
        input_dir=args.input_dir,
        summary=summary,
        high_steps=high_steps,
        freq=freq,
        attr_summary=attr_summary,
        plot_path=plot_path,
    )

    manifest = {
        "summary": str(summary_path),
        "high_intervention_steps": str(args.output_dir / "high_intervention_steps.csv"),
        "active_gaussian_frequency": str(args.output_dir / "active_gaussian_frequency.csv"),
        "active_gaussian_attribute_summary": str(args.output_dir / "active_gaussian_attribute_summary.csv"),
        "figure": str(plot_path),
        "report": str(report_path),
    }
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
