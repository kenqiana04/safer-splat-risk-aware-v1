#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "risk_aware_cbf"
RESULTS = BASE / "results"
FIGURES = BASE / "figures"
NOTES = BASE / "notes"

BESTD_DIR = RESULTS / "risk_aware_v1_pre_cbf_stonehenge_100_bestD"
DEFAULT_V1_DIR = RESULTS / "risk_aware_v1_pre_cbf_stonehenge_100"
TOPK_V0_DIR = RESULTS / "risk_aware_topk_stonehenge_100"
BASELINE_DIR = RESULTS / "baseline_detailed_logging_stonehenge_100"
ABLATION_DIR = RESULTS / "risk_aware_v1_ablation_stonehenge_20"

SUMMARY_OUT = RESULTS / "risk_aware_v1_best_config_100_analysis_summary.csv"
METRICS_OUT = RESULTS / "risk_aware_v1_best_config_100_analysis_metrics.json"
PLOT_OUT = FIGURES / "risk_aware_v1_best_config_100_plots.png"
NOTE_OUT = NOTES / "RISK_AWARE_V1_BEST_CONFIG_100_ANALYSIS.md"
REPORT_OUT = BASE / "REPORT_RISK_AWARE_V1_BEST_CONFIG_100_TRIAL.md"

BEST_CONFIG = {
    "ablation_id": "D_budget2000_near005_hybrid",
    "candidate_budget": 2000,
    "near_distance_threshold": 0.05,
    "heading_distance_threshold": 0.25,
    "heading_cos_threshold": 0.5,
    "risk_score": "risk_v2_hybrid",
    "actual_insertion_level": "partial_pre_cbf",
}

OUT_COLUMNS = [
    "comparison_label",
    "scene",
    "method",
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
    "actual_insertion_level",
    "source_dir",
]


def num(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def bool_mean(series: pd.Series) -> float | str:
    if series.empty:
        return ""
    values = series.astype(str).str.lower().isin(["true", "1", "yes"])
    return float(values.mean())


def quantile(values: pd.Series, q: float) -> float | str:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return ""
    return float(values.quantile(q))


def read_summary(path: Path) -> pd.DataFrame:
    summary = path / "summary.csv"
    if not summary.exists():
        raise FileNotFoundError(f"missing summary: {summary}")
    return pd.read_csv(summary)


def summary_row(path: Path, method: str, label: str) -> dict[str, Any]:
    table = read_summary(path)
    hit = table[table["method"] == method]
    if hit.empty:
        raise ValueError(f"method {method!r} not found in {path / 'summary.csv'}")
    row = hit.iloc[0]
    return {
        "comparison_label": label,
        "scene": row.get("scene", ""),
        "method": method,
        "rows": row.get("rows", ""),
        "collision_count": row.get("collision_count", ""),
        "collision_free_count": row.get("collision_free_count", ""),
        "min_safety_h_min": row.get("min_safety_h_min", ""),
        "min_safety_h_mean": row.get("min_safety_h_mean", ""),
        "progress_mean": row.get("goal_distance_reduction_ratio_mean", ""),
        "intervention_rate_mean": row.get("intervention_rate_mean", ""),
        "control_deviation_mean": row.get("control_deviation_mean_mean", ""),
        "active_constraints_mean": row.get("active_constraints_mean_mean", ""),
        "runtime_mean": row.get("runtime_mean_mean", ""),
        "runtime_p95": row.get("runtime_p95_mean", ""),
        "qp_infeasible_count": row.get("qp_infeasible_count_sum", ""),
        "fallback_used_rate": "",
        "candidate_count_final_mean": "",
        "candidate_count_final_p95": "",
        "actual_insertion_level": "",
        "source_dir": str(path),
    }


def add_v1_debug(row: dict[str, Any], path: Path) -> dict[str, Any]:
    debug = path / "v1_candidate_debug.csv"
    if not debug.exists():
        return row
    table = pd.read_csv(debug)
    if table.empty:
        return row
    row = dict(row)
    row["fallback_used_rate"] = bool_mean(table.get("fallback_used", pd.Series(dtype=object)))
    row["candidate_count_final_mean"] = float(pd.to_numeric(table["candidate_count_final"], errors="coerce").mean())
    row["candidate_count_final_p95"] = quantile(table["candidate_count_final"], 0.95)
    levels = table.get("v1_insertion_level", pd.Series(dtype=object)).dropna().astype(str)
    row["actual_insertion_level"] = levels.mode().iloc[0] if not levels.empty else ""
    return row


def add_topk_debug(row: dict[str, Any], path: Path) -> dict[str, Any]:
    debug = path / "risk_aware_selection_debug.csv"
    if not debug.exists():
        return row
    table = pd.read_csv(debug)
    if table.empty:
        return row
    row = dict(row)
    row["fallback_used_rate"] = bool_mean(table.get("fallback_used", pd.Series(dtype=object)))
    row["candidate_count_final_mean"] = float(pd.to_numeric(table["risk_aware_selected_count"], errors="coerce").mean())
    row["candidate_count_final_p95"] = quantile(table["risk_aware_selected_count"], 0.95)
    row["actual_insertion_level"] = "risk_aware_topk_v0"
    return row


def load_rows() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.append(summary_row(BESTD_DIR, "no_filter", "no_filter"))
    rows.append(summary_row(BESTD_DIR, "safer_splat_filter", "safer_splat_filter"))
    rows.append(add_topk_debug(summary_row(TOPK_V0_DIR, "risk_aware_topk_v0", "risk_aware_topk_v0"), TOPK_V0_DIR))
    rows.append(
        add_v1_debug(
            summary_row(DEFAULT_V1_DIR, "risk_aware_v1_pre_cbf", "risk_aware_v1_pre_cbf_default"),
            DEFAULT_V1_DIR,
        )
    )
    rows.append(
        add_v1_debug(
            summary_row(BESTD_DIR, "risk_aware_v1_pre_cbf", "risk_aware_v1_pre_cbf_bestD"),
            BESTD_DIR,
        )
    )
    return pd.DataFrame(rows, columns=OUT_COLUMNS)


def get_row(df: pd.DataFrame, label: str) -> pd.Series:
    hit = df[df["comparison_label"] == label]
    if hit.empty:
        raise ValueError(f"missing comparison row: {label}")
    return hit.iloc[0]


def flag_checks(df: pd.DataFrame) -> dict[str, Any]:
    baseline = get_row(df, "safer_splat_filter")
    default_v1 = get_row(df, "risk_aware_v1_pre_cbf_default")
    best = get_row(df, "risk_aware_v1_pre_cbf_bestD")
    base_progress = num(baseline["progress_mean"]) or 0.0
    best_progress = num(best["progress_mean"]) or 0.0
    checks = {
        "safety_preserved": (num(best["collision_count"]) == 0 and (num(best["min_safety_h_min"]) or -1) > 0),
        "progress_preserved": best_progress >= 0.99 * base_progress,
        "progress_improved": best_progress > 1.01 * base_progress,
        "active_constraints_reduced": (num(best["active_constraints_mean"]) or math.inf)
        < (num(baseline["active_constraints_mean"]) or -math.inf),
        "runtime_improved": (num(best["runtime_mean"]) or math.inf) < (num(baseline["runtime_mean"]) or -math.inf)
        and (num(best["runtime_p95"]) or math.inf) < (num(baseline["runtime_p95"]) or -math.inf),
        "qp_stability_preserved": num(best["qp_infeasible_count"]) == 0,
        "fallback_low": (num(best["fallback_used_rate"]) or 0.0) <= 0.05,
        "active_constraints_lower_than_default_v1": (num(best["active_constraints_mean"]) or math.inf)
        < (num(default_v1["active_constraints_mean"]) or -math.inf),
        "runtime_lower_than_default_v1": (num(best["runtime_mean"]) or math.inf)
        < (num(default_v1["runtime_mean"]) or -math.inf)
        and (num(best["runtime_p95"]) or math.inf) < (num(default_v1["runtime_p95"]) or -math.inf),
    }
    if checks["safety_preserved"] and checks["progress_preserved"] and checks["runtime_improved"] and checks["qp_stability_preserved"]:
        decision = "PROCEED_TO_SECOND_SCENE"
        reason = "bestD preserves safety and progress while reducing runtime versus the SAFER-Splat baseline."
    elif not checks["safety_preserved"] or not checks["qp_stability_preserved"]:
        decision = "ABANDON_BESTD_KEEP_DEFAULT_V1"
        reason = "bestD failed a safety or QP stability gate."
    else:
        decision = "TUNE_MORE_ON_STONEHENGE"
        reason = "bestD did not satisfy all progress/runtime validation gates."
    return {
        **checks,
        "recommended_decision": decision,
        "decision_reason": reason,
        "baseline_progress_mean": base_progress,
        "bestD_progress_mean": best_progress,
        "default_v1_runtime_mean": num(default_v1["runtime_mean"]),
        "bestD_runtime_mean": num(best["runtime_mean"]),
        "default_v1_active_constraints_mean": num(default_v1["active_constraints_mean"]),
        "bestD_active_constraints_mean": num(best["active_constraints_mean"]),
    }


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = f"{value:.10g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_plot(df: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = [
        "collision_count",
        "min_safety_h_min",
        "progress_mean",
        "active_constraints_mean",
        "runtime_mean",
        "runtime_p95",
        "candidate_count_final_mean",
        "fallback_used_rate",
    ]
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        values = pd.to_numeric(df[metric], errors="coerce").fillna(0.0)
        ax.bar(df["comparison_label"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=35, labelsize=8)
    fig.tight_layout()
    PLOT_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT_OUT, dpi=180)
    plt.close(fig)


def write_note(df: pd.DataFrame, checks: dict[str, Any]) -> None:
    cols = [
        "comparison_label",
        "collision_count",
        "min_safety_h_min",
        "progress_mean",
        "active_constraints_mean",
        "runtime_mean",
        "runtime_p95",
        "qp_infeasible_count",
        "fallback_used_rate",
        "candidate_count_final_mean",
        "actual_insertion_level",
    ]
    lines = [
        "# Risk-Aware V1 Best Config 100-Trial Analysis",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "This analysis validates `D_budget2000_near005_hybrid` on stonehenge 100-trial and compares it against existing same-scale baselines.",
        "It does not modify the official SAFER-Splat baseline and does not claim a new CBF theorem.",
        "",
        "## 100-Trial Comparison",
        "",
        markdown_table(df, cols),
        "",
        "## Validation Checks",
        "",
    ]
    for key in [
        "safety_preserved",
        "progress_preserved",
        "progress_improved",
        "active_constraints_reduced",
        "runtime_improved",
        "qp_stability_preserved",
        "fallback_low",
        "active_constraints_lower_than_default_v1",
        "runtime_lower_than_default_v1",
    ]:
        lines.append(f"- {key}: {checks[key]}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_decision: {checks['recommended_decision']}",
            f"- reason: {checks['decision_reason']}",
            "",
            "## Claim Boundary",
            "",
            "`min_safety_h` is not meter clearance. This remains a wrapper-level prototype validated on stonehenge only.",
        ]
    )
    NOTE_OUT.parent.mkdir(parents=True, exist_ok=True)
    NOTE_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(df: pd.DataFrame, checks: dict[str, Any]) -> None:
    cols = [
        "comparison_label",
        "collision_count",
        "min_safety_h_min",
        "progress_mean",
        "intervention_rate_mean",
        "control_deviation_mean",
        "active_constraints_mean",
        "runtime_mean",
        "runtime_p95",
        "qp_infeasible_count",
        "fallback_used_rate",
        "candidate_count_final_mean",
    ]
    lines = [
        "# Risk-Aware V1 Best Config 100-Trial Report",
        "",
        "## Scope",
        "",
        "This report validates the best V1 ablation configuration on stonehenge 100-trial.",
        "It does not modify the official SAFER-Splat baseline.",
        "It does not claim a new CBF theorem.",
        "",
        "## Best Config",
        "",
    ]
    for key, value in BEST_CONFIG.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## 100-Trial Comparison",
            "",
            markdown_table(df, cols),
            "",
            "## What Improved",
            "",
            f"- safety preserved: {'yes' if checks['safety_preserved'] else 'no'}",
            f"- progress preserved: {'yes' if checks['progress_preserved'] else 'no'}",
            f"- progress improved: {'yes' if checks['progress_improved'] else 'no'}",
            f"- active constraints reduced: {'yes' if checks['active_constraints_reduced'] else 'no'}",
            f"- runtime improved: {'yes' if checks['runtime_improved'] else 'no'}",
            f"- QP stability preserved: {'yes' if checks['qp_stability_preserved'] else 'no'}",
            f"- active constraints lower than default V1: {'yes' if checks['active_constraints_lower_than_default_v1'] else 'no'}",
            f"- runtime lower than default V1: {'yes' if checks['runtime_lower_than_default_v1'] else 'no'}",
            "",
            "## Honest Interpretation",
            "",
            "If bestD preserves safety and reduces runtime, this supports V1 pre-CBF candidate budgeting as a computational-efficiency method.",
            "If progress remains unchanged, do not claim navigation progress improvement.",
            "In this run, bestD reduces active constraints relative to default V1, but default V1 remains slightly faster on runtime_mean and runtime_p95.",
            "Therefore, bestD is the lower-constraint configuration for next validation, while default V1 remains the fastest V1 setting observed here.",
            "If bestD causes collision or QP infeasible cases, do not proceed to second-scene validation.",
            "",
            "## Claim Boundary",
            "",
            "This is still a wrapper-level prototype.",
            "The reported min_safety_h is not meter clearance.",
            "The method does not prove a new CBF theorem.",
            "The method has only been validated on stonehenge so far.",
            "",
            "## Next Step Decision",
            "",
            f"{checks['recommended_decision']}: {checks['decision_reason']}",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    df = load_rows()
    df.to_csv(SUMMARY_OUT, index=False)
    write_plot(df)
    checks = flag_checks(df)
    METRICS_OUT.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_note(df, checks)
    write_report(df, checks)
    for path in [SUMMARY_OUT, METRICS_OUT, PLOT_OUT, NOTE_OUT, REPORT_OUT]:
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
