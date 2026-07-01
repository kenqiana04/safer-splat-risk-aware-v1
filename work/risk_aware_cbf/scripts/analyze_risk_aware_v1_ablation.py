#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


SUMMARY_COLUMNS = [
    "ablation_id",
    "candidate_budget",
    "near_distance_threshold",
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
    "selection_tag",
]


def num(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_No rows available._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = f"{value:.10g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def load_baseline(metrics_path: Path, fallback_summary: Path) -> dict[str, Any]:
    if metrics_path.exists():
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
            baseline = payload.get("baseline_reference") or {}
            if baseline:
                return baseline
        except json.JSONDecodeError:
            pass
    if fallback_summary.exists():
        table = pd.read_csv(fallback_summary)
        row = table[table["method"] == "safer_splat_filter"]
        if not row.empty:
            r = row.iloc[0]
            return {
                "source": str(fallback_summary),
                "rows": r.get("rows", ""),
                "collision_count": r.get("collision_count", ""),
                "min_safety_h_min": r.get("min_safety_h_min", ""),
                "progress_mean": r.get("goal_distance_reduction_ratio_mean", ""),
                "active_constraints_mean": r.get("active_constraints_mean_mean", ""),
                "runtime_mean": r.get("runtime_mean_mean", ""),
                "runtime_p95": r.get("runtime_p95_mean", ""),
                "qp_infeasible_count": r.get("qp_infeasible_count_sum", ""),
            }
    return {}


def safe_mask(df: pd.DataFrame) -> pd.Series:
    return (
        (pd.to_numeric(df["collision_count"], errors="coerce").fillna(1) == 0)
        & (pd.to_numeric(df["qp_infeasible_count"], errors="coerce").fillna(1) == 0)
        & (pd.to_numeric(df["min_safety_h_min"], errors="coerce").fillna(-1) > 0)
    )


def pick_config(df: pd.DataFrame, kind: str, baseline: dict[str, Any]) -> str:
    safe = df[safe_mask(df)].copy()
    if safe.empty:
        return "No valid safe config found"
    if kind == "safest":
        idx = pd.to_numeric(safe["min_safety_h_min"], errors="coerce").idxmax()
    elif kind == "fastest":
        idx = pd.to_numeric(safe["runtime_mean"], errors="coerce").idxmin()
    elif kind == "lowest_constraint":
        idx = pd.to_numeric(safe["active_constraints_mean"], errors="coerce").idxmin()
    elif kind == "balanced":
        baseline_runtime = num(baseline.get("runtime_mean"))
        baseline_progress = num(baseline.get("progress_mean"))
        runtime = pd.to_numeric(safe["runtime_mean"], errors="coerce")
        progress = pd.to_numeric(safe["progress_mean"], errors="coerce")
        fallback = pd.to_numeric(safe["fallback_used_rate"], errors="coerce").fillna(1.0)
        mask = fallback <= 0.25
        if baseline_runtime is not None:
            mask &= runtime < baseline_runtime
        if baseline_progress is not None:
            mask &= progress >= 0.99 * baseline_progress
        candidates = safe[mask].copy()
        if candidates.empty:
            return "No valid balanced config found"
        idx = pd.to_numeric(candidates["runtime_mean"], errors="coerce").idxmin()
    else:
        raise ValueError(kind)
    return str(df.loc[idx, "ablation_id"])


def add_selection_tags(df: pd.DataFrame, selections: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    tags = []
    for _, row in out.iterrows():
        row_tags = [name for name, cfg in selections.items() if cfg == row["ablation_id"]]
        tags.append(",".join(row_tags))
    out["selection_tag"] = tags
    return out


def grouped_observation(df: pd.DataFrame, group_col: str) -> str:
    if df.empty or group_col not in df.columns:
        return "No data."
    grouped = (
        df.groupby(group_col)
        .agg(
            collision_count=("collision_count", lambda s: pd.to_numeric(s, errors="coerce").sum()),
            min_safety_h_min=("min_safety_h_min", lambda s: pd.to_numeric(s, errors="coerce").min()),
            runtime_mean=("runtime_mean", lambda s: pd.to_numeric(s, errors="coerce").mean()),
            active_constraints_mean=("active_constraints_mean", lambda s: pd.to_numeric(s, errors="coerce").mean()),
            progress_mean=("progress_mean", lambda s: pd.to_numeric(s, errors="coerce").mean()),
            candidate_count_final_mean=("candidate_count_final_mean", lambda s: pd.to_numeric(s, errors="coerce").mean()),
        )
        .reset_index()
    )
    return markdown_table(grouped, list(grouped.columns))


def write_plots(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

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
        values = pd.to_numeric(df[metric], errors="coerce").fillna(0.0)
        ax.bar(df["ablation_id"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def report_decision(df: pd.DataFrame, selections: dict[str, str], baseline: dict[str, Any]) -> tuple[str, str]:
    balanced = selections["best_balanced_config"]
    if balanced != "No valid balanced config found":
        default_id = "B_budget2000_near008_hybrid"
        if balanced == default_id:
            return (
                "PROCEED_TO_SECOND_SCENE_WITH_DEFAULT_V1",
                "The default V1 config remains safe, fast, and balanced; ablation did not justify changing it before second-scene validation.",
            )
        return (
            "PROCEED_TO_100_WITH_BEST_CONFIG",
            f"{balanced} satisfies the safe/runtime/progress/fallback criteria and should be validated at 100-trial scale.",
        )
    safe = df[safe_mask(df)]
    if not safe.empty:
        return ("TUNE_MORE", "Some configs are safe, but none satisfies the balanced selection rule.")
    return ("STOP_V1_AND_WRITE_CURRENT_RESULT", "No safe ablation config was found.")


def write_analysis(df: pd.DataFrame, baseline: dict[str, Any], selections: dict[str, str], output_path: Path) -> None:
    safe = df[safe_mask(df)]
    lines = [
        "# Risk-Aware V1 Ablation Analysis",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Baseline Reference",
        "",
        markdown_table(pd.DataFrame([baseline]) if baseline else pd.DataFrame(), list(baseline.keys()) if baseline else []),
        "",
        "## Ablation Table",
        "",
        markdown_table(df, SUMMARY_COLUMNS),
        "",
        "## Selected Configs",
        "",
        f"- safest_config: {selections['safest_config']}",
        f"- fastest_config: {selections['fastest_config']}",
        f"- lowest_constraint_config: {selections['lowest_constraint_config']}",
        f"- best_balanced_config: {selections['best_balanced_config']}",
        "",
        "## Observations",
        "",
        f"- configs with 0 collision and positive min_safety_h: {len(safe)} / {len(df)}",
        "",
        "### Candidate Budget Effect",
        "",
        grouped_observation(df, "candidate_budget"),
        "",
        "### Near-Distance Threshold Effect",
        "",
        grouped_observation(df, "near_distance_threshold"),
        "",
        "### Risk Score Effect",
        "",
        grouped_observation(df, "risk_score"),
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(
    df: pd.DataFrame,
    baseline: dict[str, Any],
    selections: dict[str, str],
    decision: tuple[str, str],
    output_path: Path,
) -> None:
    lines = [
        "# Risk-Aware V1 Ablation Report",
        "",
        "## Scope",
        "",
        "This report evaluates V1 pre-CBF candidate-budgeting ablations on stonehenge 20-trial.",
        "It does not modify the official SAFER-Splat baseline.",
        "It does not claim a new CBF theorem.",
        "",
        "## Baseline Reference",
        "",
        "SAFER-Splat baseline is reused from the existing V1 20-trial comparison to avoid rerunning an identical baseline per ablation config.",
        "",
        markdown_table(pd.DataFrame([baseline]) if baseline else pd.DataFrame(), list(baseline.keys()) if baseline else []),
        "",
        "## Ablation Table",
        "",
        markdown_table(
            df,
            [
                "ablation_id",
                "collision_count",
                "min_safety_h_min",
                "progress_mean",
                "active_constraints_mean",
                "runtime_mean",
                "runtime_p95",
                "qp_infeasible_count",
                "fallback_used_rate",
                "candidate_count_final_mean",
                "selection_tag",
            ],
        ),
        "",
        "## Main Observations",
        "",
        f"1. candidate_budget effect: see grouped analysis in `RISK_AWARE_V1_ABLATION_ANALYSIS.md`; fastest config is {selections['fastest_config']}.",
        "2. near_distance_threshold effect: higher thresholds tend to force more candidates; check runtime and candidate count together.",
        "3. risk_score effect: compare activefreq / geometry / hybrid rows at budget 2000 and near 0.08.",
        f"4. better-than-default candidate: best_balanced_config = {selections['best_balanced_config']}.",
        "5. a 100-trial rerun is justified only for a balanced config that remains safe and meaningfully faster than baseline.",
        "",
        "## Recommended Next Step",
        "",
        f"{decision[0]}: {decision[1]}",
        "",
        "## Claim Boundary",
        "",
        "The reported `min_safety_h` is not meter clearance.",
        "This is a wrapper-level prototype and does not prove a new CBF theorem.",
        "Only stonehenge 20-trial ablation is evaluated here.",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Risk-Aware V1 ablation outputs.")
    parser.add_argument("--root", type=Path, default=Path("work/risk_aware_cbf"))
    parser.add_argument(
        "--ablation-dir",
        type=Path,
        default=Path("work/risk_aware_cbf/results/risk_aware_v1_ablation_stonehenge_20"),
    )
    parser.add_argument(
        "--baseline-summary",
        type=Path,
        default=Path("work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20/summary.csv"),
    )
    args = parser.parse_args()

    summary_path = args.ablation_dir / "ablation_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing ablation summary: {summary_path}")
    df = pd.read_csv(summary_path)
    baseline = load_baseline(args.ablation_dir / "ablation_metrics.json", args.baseline_summary)
    selections = {
        "safest_config": pick_config(df, "safest", baseline),
        "fastest_config": pick_config(df, "fastest", baseline),
        "lowest_constraint_config": pick_config(df, "lowest_constraint", baseline),
        "best_balanced_config": pick_config(df, "balanced", baseline),
    }
    df = add_selection_tags(df, selections)
    decision = report_decision(df, selections, baseline)

    analysis_csv = args.root / "results/risk_aware_v1_ablation_analysis_summary.csv"
    analysis_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(analysis_csv, index=False)
    figure_path = args.root / "figures/risk_aware_v1_ablation_plots.png"
    write_plots(df, figure_path)
    write_analysis(df, baseline, selections, args.root / "notes/RISK_AWARE_V1_ABLATION_ANALYSIS.md")
    write_report(df, baseline, selections, decision, args.root / "REPORT_RISK_AWARE_V1_ABLATION.md")
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selections": selections,
        "decision": {"name": decision[0], "reason": decision[1]},
        "baseline_reference": baseline,
    }
    (args.root / "results/risk_aware_v1_ablation_analysis_metrics.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {analysis_csv}")
    print(f"wrote {figure_path}")
    print(f"wrote {args.root / 'notes/RISK_AWARE_V1_ABLATION_ANALYSIS.md'}")
    print(f"wrote {args.root / 'REPORT_RISK_AWARE_V1_ABLATION.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
