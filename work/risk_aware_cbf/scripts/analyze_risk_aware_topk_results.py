#!/usr/bin/env python3
"""Analyze risk-aware top-k V0 smoke, 20-trial, and 100-trial outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "risk_aware_cbf"
RESULTS = BASE / "results"
FIGURES = BASE / "figures"
NOTES = BASE / "notes"

RUNS = {
    "smoke3": RESULTS / "risk_aware_topk_stonehenge_smoke3",
    "trial20": RESULTS / "risk_aware_topk_stonehenge_20",
    "trial100": RESULTS / "risk_aware_topk_stonehenge_100",
}


def read_summary(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path / "summary.csv")
    df["run"] = path.name
    return df


def read_debug(path: Path) -> pd.DataFrame:
    debug_path = path / "risk_aware_selection_debug.csv"
    if not debug_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(debug_path)
    df["run"] = path.name
    return df


def method_row(summary: pd.DataFrame, method: str) -> pd.Series | None:
    hit = summary[summary["method"] == method]
    if hit.empty:
        return None
    return hit.iloc[0]


def numeric(row: pd.Series | None, column: str) -> float:
    if row is None or column not in row:
        return float("nan")
    try:
        return float(row[column])
    except (TypeError, ValueError):
        return float("nan")


def analyze_run(label: str, path: Path) -> list[dict[str, Any]]:
    summary = read_summary(path)
    debug = read_debug(path)
    rows: list[dict[str, Any]] = []
    for _, row in summary.iterrows():
        out = {"run_label": label, "method": row["method"]}
        for metric in [
            "rows",
            "collision_count",
            "collision_free_count",
            "min_safety_h_min",
            "min_safety_h_mean",
            "goal_distance_reduction_ratio_mean",
            "final_goal_distance_mean",
            "closest_goal_distance_mean",
            "intervention_rate_mean",
            "control_deviation_mean_mean",
            "active_constraints_mean_mean",
            "runtime_mean_mean",
            "runtime_p95_mean",
            "qp_infeasible_count_sum",
        ]:
            out[metric] = row.get(metric, "")
        if row["method"] == "risk_aware_topk_v0" and not debug.empty:
            fallback = debug["fallback_used"].astype(str).str.lower().isin(["true", "1", "yes"])
            out["fallback_used_rate"] = float(fallback.mean())
            out["baseline_active_constraints_count_debug_mean"] = float(pd.to_numeric(debug["baseline_active_constraints_count"], errors="coerce").mean())
            out["risk_aware_selected_count_debug_mean"] = float(pd.to_numeric(debug["risk_aware_selected_count"], errors="coerce").mean())
            out["forced_low_h_count_mean"] = float(pd.to_numeric(debug["forced_low_h_count"], errors="coerce").mean())
            out["forced_near_count_mean"] = float(pd.to_numeric(debug["forced_near_count"], errors="coerce").mean())
            out["forced_heading_count_mean"] = float(pd.to_numeric(debug["forced_heading_count"], errors="coerce").mean())
        rows.append(out)

    baseline = method_row(summary, "safer_splat_filter")
    risk = method_row(summary, "risk_aware_topk_v0")
    if baseline is not None and risk is not None:
        for metric in [
            "collision_count",
            "min_safety_h_min",
            "goal_distance_reduction_ratio_mean",
            "intervention_rate_mean",
            "control_deviation_mean_mean",
            "active_constraints_mean_mean",
            "runtime_mean_mean",
            "runtime_p95_mean",
            "qp_infeasible_count_sum",
        ]:
            b = numeric(baseline, metric)
            r = numeric(risk, metric)
            rows.append(
                {
                    "run_label": label,
                    "method": "risk_minus_safer_splat_filter",
                    "metric": metric,
                    "delta": r - b,
                    "baseline": b,
                    "risk_aware": r,
                    "relative_delta": (r - b) / b if np.isfinite(b) and abs(b) > 1e-12 else "",
                }
            )
    return rows


def write_plot(summary: pd.DataFrame, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    run_label = "trial100" if (summary["run_label"] == "trial100").any() else "trial20"
    trial20 = summary[(summary["run_label"] == run_label) & summary["method"].isin(["safer_splat_filter", "risk_aware_topk_v0"])]
    metrics = [
        "collision_count",
        "min_safety_h_min",
        "goal_distance_reduction_ratio_mean",
        "intervention_rate_mean",
        "control_deviation_mean_mean",
        "active_constraints_mean_mean",
        "runtime_mean_mean",
        "qp_infeasible_count_sum",
    ]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        values = pd.to_numeric(trial20[metric], errors="coerce").fillna(0.0)
        ax.bar(trial20["method"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def summary_value(df: pd.DataFrame, run_label: str, method: str, metric: str) -> str:
    hit = df[(df["run_label"] == run_label) & (df["method"] == method)]
    if hit.empty or metric not in hit.columns:
        return ""
    return str(hit.iloc[0][metric])


def write_markdown(summary: pd.DataFrame, output: Path) -> None:
    lines = [
        "# Risk-Aware Top-K V0 Analysis",
        "",
        "## Scope",
        "",
        "This analysis compares the wrapper-level `risk_aware_topk_v0` prototype against `no_filter` and the unchanged `safer_splat_filter` baseline.",
        "It does not modify the official SAFER-Splat baseline and does not claim a new CBF theorem.",
        "",
        "## Smoke3 Result",
        "",
        f"- risk-aware collision_count: {summary_value(summary, 'smoke3', 'risk_aware_topk_v0', 'collision_count')}",
        f"- risk-aware min_safety_h_min: {summary_value(summary, 'smoke3', 'risk_aware_topk_v0', 'min_safety_h_min')}",
        f"- risk-aware qp_infeasible_count_sum: {summary_value(summary, 'smoke3', 'risk_aware_topk_v0', 'qp_infeasible_count_sum')}",
        f"- risk-aware active_constraints_mean: {summary_value(summary, 'smoke3', 'risk_aware_topk_v0', 'active_constraints_mean_mean')}",
        "",
        "## 20-Trial Result",
        "",
        f"- safer_splat_filter collision_count: {summary_value(summary, 'trial20', 'safer_splat_filter', 'collision_count')}",
        f"- risk_aware_topk_v0 collision_count: {summary_value(summary, 'trial20', 'risk_aware_topk_v0', 'collision_count')}",
        f"- safer_splat_filter min_safety_h_min: {summary_value(summary, 'trial20', 'safer_splat_filter', 'min_safety_h_min')}",
        f"- risk_aware_topk_v0 min_safety_h_min: {summary_value(summary, 'trial20', 'risk_aware_topk_v0', 'min_safety_h_min')}",
        f"- safer_splat_filter progress mean: {summary_value(summary, 'trial20', 'safer_splat_filter', 'goal_distance_reduction_ratio_mean')}",
        f"- risk_aware_topk_v0 progress mean: {summary_value(summary, 'trial20', 'risk_aware_topk_v0', 'goal_distance_reduction_ratio_mean')}",
        f"- safer_splat_filter active constraints mean: {summary_value(summary, 'trial20', 'safer_splat_filter', 'active_constraints_mean_mean')}",
        f"- risk_aware_topk_v0 active constraints mean: {summary_value(summary, 'trial20', 'risk_aware_topk_v0', 'active_constraints_mean_mean')}",
        f"- risk_aware_topk_v0 fallback_used_rate: {summary_value(summary, 'trial20', 'risk_aware_topk_v0', 'fallback_used_rate')}",
        "",
        "## 100-Trial Result",
        "",
        f"- no_filter collision_count: {summary_value(summary, 'trial100', 'no_filter', 'collision_count')}",
        f"- safer_splat_filter collision_count: {summary_value(summary, 'trial100', 'safer_splat_filter', 'collision_count')}",
        f"- risk_aware_topk_v0 collision_count: {summary_value(summary, 'trial100', 'risk_aware_topk_v0', 'collision_count')}",
        f"- safer_splat_filter min_safety_h_min: {summary_value(summary, 'trial100', 'safer_splat_filter', 'min_safety_h_min')}",
        f"- risk_aware_topk_v0 min_safety_h_min: {summary_value(summary, 'trial100', 'risk_aware_topk_v0', 'min_safety_h_min')}",
        f"- safer_splat_filter progress mean: {summary_value(summary, 'trial100', 'safer_splat_filter', 'goal_distance_reduction_ratio_mean')}",
        f"- risk_aware_topk_v0 progress mean: {summary_value(summary, 'trial100', 'risk_aware_topk_v0', 'goal_distance_reduction_ratio_mean')}",
        f"- safer_splat_filter active constraints mean: {summary_value(summary, 'trial100', 'safer_splat_filter', 'active_constraints_mean_mean')}",
        f"- risk_aware_topk_v0 active constraints mean: {summary_value(summary, 'trial100', 'risk_aware_topk_v0', 'active_constraints_mean_mean')}",
        f"- risk_aware_topk_v0 fallback_used_rate: {summary_value(summary, 'trial100', 'risk_aware_topk_v0', 'fallback_used_rate')}",
        "",
        "## Interpretation",
        "",
        "The V0 wrapper stayed collision-free and had no QP infeasible cases in smoke3 and 20-trial tests.",
        "It substantially reduced the selected constraint count, but did not materially improve progress or reduce intervention on the 20-trial set.",
        "Runtime did not improve in this implementation because the wrapper is inserted after baseline distance querying and minimal-polytope construction.",
        "",
        "## Next Steps",
        "",
        "1. Run a 100-trial stability check only if the goal is to validate safety and constraint-count reduction.",
        "2. Sweep `topk`, `h_critical`, and `risk_score` before claiming any progress benefit.",
        "3. A cleaner future insertion point should reduce candidate work before minimal-polytope construction; that requires a separate wrapper API, not editing official core files.",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for label, path in RUNS.items():
        if (path / "summary.csv").exists():
            rows.extend(analyze_run(label, path))
    out = pd.DataFrame(rows)
    output_csv = RESULTS / "risk_aware_topk_analysis_summary.csv"
    out.to_csv(output_csv, index=False)
    fig_path = FIGURES / "risk_aware_topk_comparison_plots.png"
    write_plot(out[out["method"].isin(["no_filter", "safer_splat_filter", "risk_aware_topk_v0"])], fig_path)
    md_path = NOTES / "RISK_AWARE_TOPK_V0_ANALYSIS.md"
    write_markdown(out, md_path)
    print({"summary": str(output_csv), "figure": str(fig_path), "report": str(md_path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
