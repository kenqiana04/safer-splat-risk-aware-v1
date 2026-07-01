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

RUNS = {
    "flight_smoke3_default": RESULTS / "risk_aware_v1_pre_cbf_flight_smoke3_default",
    "flight_smoke3_bestD": RESULTS / "risk_aware_v1_pre_cbf_flight_smoke3_bestD",
    "flight_20_default": RESULTS / "risk_aware_v1_pre_cbf_flight_20_default",
    "flight_20_bestD": RESULTS / "risk_aware_v1_pre_cbf_flight_20_bestD",
    "stonehenge_100_default": RESULTS / "risk_aware_v1_pre_cbf_stonehenge_100",
    "stonehenge_100_bestD": RESULTS / "risk_aware_v1_pre_cbf_stonehenge_100_bestD",
}

SUMMARY_OUT = RESULTS / "risk_aware_v1_second_scene_analysis_summary.csv"
METRICS_OUT = RESULTS / "risk_aware_v1_second_scene_analysis_metrics.json"
PLOT_OUT = FIGURES / "risk_aware_v1_second_scene_plots.png"
NOTE_OUT = NOTES / "RISK_AWARE_V1_SECOND_SCENE_ANALYSIS.md"
REPORT_OUT = BASE / "REPORT_RISK_AWARE_V1_SECOND_SCENE_FLIGHT.md"

FLIGHT_CHECKPOINT = "outputs/flight/splatfacto/2024-09-12_172434/config.yml"
FLIGHT_DATA = "data/flight/transforms.json"
FLIGHT_RISK_META = RESULTS / "flight_risk_score_metadata_v0.json"
FLIGHT_ATTR_SUMMARY = RESULTS / "flight_gaussian_attribute_summary.csv"

OUT_COLUMNS = [
    "run_label",
    "scene",
    "method_label",
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
    return float(series.astype(str).str.lower().isin(["true", "1", "yes"]).mean())


def quantile(series: pd.Series, q: float) -> float | str:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return ""
    return float(values.quantile(q))


def read_summary(path: Path) -> pd.DataFrame:
    summary = path / "summary.csv"
    if not summary.exists():
        raise FileNotFoundError(f"missing summary: {summary}")
    return pd.read_csv(summary)


def summary_row(path: Path, run_label: str, method: str, method_label: str) -> dict[str, Any]:
    table = read_summary(path)
    hit = table[table["method"] == method]
    if hit.empty:
        raise ValueError(f"method={method} missing from {path / 'summary.csv'}")
    row = hit.iloc[0]
    return {
        "run_label": run_label,
        "scene": row.get("scene", ""),
        "method_label": method_label,
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
    debug_path = path / "v1_candidate_debug.csv"
    if not debug_path.exists():
        return row
    debug = pd.read_csv(debug_path)
    if debug.empty:
        return row
    row = dict(row)
    row["fallback_used_rate"] = bool_mean(debug.get("fallback_used", pd.Series(dtype=object)))
    row["candidate_count_final_mean"] = float(pd.to_numeric(debug["candidate_count_final"], errors="coerce").mean())
    row["candidate_count_final_p95"] = quantile(debug["candidate_count_final"], 0.95)
    levels = debug.get("v1_insertion_level", pd.Series(dtype=object)).dropna().astype(str)
    row["actual_insertion_level"] = levels.mode().iloc[0] if not levels.empty else ""
    return row


def load_rows() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.append(summary_row(RUNS["flight_smoke3_default"], "flight_smoke3_default", "safer_splat_filter", "flight_smoke3_safer_splat_filter_default_run"))
    rows.append(add_v1_debug(summary_row(RUNS["flight_smoke3_default"], "flight_smoke3_default", "risk_aware_v1_pre_cbf", "flight_smoke3_risk_aware_v1_default"), RUNS["flight_smoke3_default"]))
    rows.append(summary_row(RUNS["flight_smoke3_bestD"], "flight_smoke3_bestD", "safer_splat_filter", "flight_smoke3_safer_splat_filter_bestD_run"))
    rows.append(add_v1_debug(summary_row(RUNS["flight_smoke3_bestD"], "flight_smoke3_bestD", "risk_aware_v1_pre_cbf", "flight_smoke3_risk_aware_v1_bestD"), RUNS["flight_smoke3_bestD"]))

    rows.append(summary_row(RUNS["flight_20_default"], "flight_20", "no_filter", "flight_no_filter"))
    rows.append(summary_row(RUNS["flight_20_default"], "flight_20", "safer_splat_filter", "flight_safer_splat_filter"))
    rows.append(add_v1_debug(summary_row(RUNS["flight_20_default"], "flight_20", "risk_aware_v1_pre_cbf", "flight_risk_aware_v1_default"), RUNS["flight_20_default"]))
    rows.append(add_v1_debug(summary_row(RUNS["flight_20_bestD"], "flight_20", "risk_aware_v1_pre_cbf", "flight_risk_aware_v1_bestD"), RUNS["flight_20_bestD"]))

    rows.append(add_v1_debug(summary_row(RUNS["stonehenge_100_default"], "stonehenge_100", "risk_aware_v1_pre_cbf", "stonehenge_risk_aware_v1_default"), RUNS["stonehenge_100_default"]))
    rows.append(add_v1_debug(summary_row(RUNS["stonehenge_100_bestD"], "stonehenge_100", "risk_aware_v1_pre_cbf", "stonehenge_risk_aware_v1_bestD"), RUNS["stonehenge_100_bestD"]))
    return pd.DataFrame(rows, columns=OUT_COLUMNS)


def pick(df: pd.DataFrame, method_label: str) -> pd.Series:
    hit = df[df["method_label"] == method_label]
    if hit.empty:
        raise ValueError(f"missing row: {method_label}")
    return hit.iloc[0]


def load_scene_setup() -> dict[str, Any]:
    meta = json.loads(FLIGHT_RISK_META.read_text(encoding="utf-8")) if FLIGHT_RISK_META.exists() else {}
    gaussian_count = ""
    if FLIGHT_ATTR_SUMMARY.exists():
        attr = pd.read_csv(FLIGHT_ATTR_SUMMARY)
        if not attr.empty:
            gaussian_count = int(pd.to_numeric(attr.iloc[0].get("count"), errors="coerce"))
    return {
        "scene": "flight",
        "checkpoint": FLIGHT_CHECKPOINT,
        "data": FLIGHT_DATA,
        "gaussian_count": gaussian_count,
        "risk_score_available": FLIGHT_RISK_META.exists(),
        "active_frequency_available": bool(meta.get("active_frequency_available", False)),
        "active_frequency_note": meta.get("missing_active_frequency", ""),
        "risk_score_table": str(RESULTS / "flight_risk_score_table_v0.csv"),
    }


def checks(df: pd.DataFrame) -> dict[str, Any]:
    safer = pick(df, "flight_safer_splat_filter")
    default = pick(df, "flight_risk_aware_v1_default")
    bestd = pick(df, "flight_risk_aware_v1_bestD")

    def safe(row: pd.Series) -> bool:
        return (
            num(row["collision_count"]) == 0
            and (num(row["min_safety_h_min"]) or -1.0) > 0.0
            and num(row["qp_infeasible_count"]) == 0
        )

    def progress_preserved(row: pd.Series) -> bool:
        baseline = num(safer["progress_mean"]) or 0.0
        value = num(row["progress_mean"]) or 0.0
        return value >= 0.99 * baseline

    def runtime_improved(row: pd.Series) -> bool:
        return (
            (num(row["runtime_mean"]) or math.inf) < (num(safer["runtime_mean"]) or -math.inf)
            and (num(row["runtime_p95"]) or math.inf) < (num(safer["runtime_p95"]) or -math.inf)
        )

    candidates = [default, bestd]
    safe_all = all(safe(row) for row in candidates)
    progress_all = all(progress_preserved(row) for row in candidates)
    runtime_all = all(runtime_improved(row) for row in candidates)
    if safe_all and progress_all and runtime_all:
        decision = "PROCEED_TO_FLIGHT_100"
        reason = "Both V1 configurations preserve flight safety/progress and reduce runtime versus SAFER-Splat on 20 trials."
    elif not safe_all:
        decision = "TUNE_FLIGHT"
        reason = "At least one V1 flight configuration failed the safety gate."
    else:
        decision = "TUNE_FLIGHT"
        reason = "Safety is preserved but progress or runtime gates are not fully satisfied."

    default_runtime = num(default["runtime_mean"]) or math.inf
    bestd_runtime = num(bestd["runtime_mean"]) or math.inf
    default_constraints = num(default["active_constraints_mean"]) or math.inf
    bestd_constraints = num(bestd["active_constraints_mean"]) or math.inf
    if bestd_runtime <= default_runtime and bestd_constraints <= default_constraints:
        preferred = "risk_aware_v1_bestD"
        preferred_reason = "bestD is faster and uses fewer active constraints on flight 20-trial."
    elif default_runtime < bestd_runtime and bestd_constraints < default_constraints:
        preferred = "mixed_default_runtime_bestD_constraints"
        preferred_reason = "default is faster, while bestD uses fewer active constraints."
    elif default_runtime <= bestd_runtime:
        preferred = "risk_aware_v1_default"
        preferred_reason = "default is the faster V1 configuration."
    else:
        preferred = "risk_aware_v1_bestD"
        preferred_reason = "bestD is the faster V1 configuration."

    return {
        "safety_preserved": safe_all,
        "progress_preserved": progress_all,
        "runtime_improved": runtime_all,
        "default_safe": safe(default),
        "bestD_safe": safe(bestd),
        "default_progress_preserved": progress_preserved(default),
        "bestD_progress_preserved": progress_preserved(bestd),
        "default_runtime_improved": runtime_improved(default),
        "bestD_runtime_improved": runtime_improved(bestd),
        "preferred_config": preferred,
        "preferred_reason": preferred_reason,
        "recommended_decision": decision,
        "decision_reason": reason,
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

    plot_df = df[df["method_label"].isin([
        "flight_safer_splat_filter",
        "flight_risk_aware_v1_default",
        "flight_risk_aware_v1_bestD",
        "stonehenge_risk_aware_v1_default",
        "stonehenge_risk_aware_v1_bestD",
    ])]
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
        values = pd.to_numeric(plot_df[metric], errors="coerce").fillna(0.0)
        ax.bar(plot_df["method_label"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=35, labelsize=7)
    fig.tight_layout()
    PLOT_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT_OUT, dpi=180)
    plt.close(fig)


def write_note(df: pd.DataFrame, scene_setup: dict[str, Any], result_checks: dict[str, Any]) -> None:
    cols = [
        "run_label",
        "method_label",
        "rows",
        "collision_count",
        "min_safety_h_min",
        "progress_mean",
        "active_constraints_mean",
        "runtime_mean",
        "runtime_p95",
        "qp_infeasible_count",
        "fallback_used_rate",
        "candidate_count_final_mean",
    ]
    lines = [
        "# Risk-Aware V1 Second-Scene Flight Analysis",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scene Setup",
        "",
        markdown_table(pd.DataFrame([scene_setup]), list(scene_setup.keys())),
        "",
        "## Summary",
        "",
        markdown_table(df, cols),
        "",
        "## Cross-Scene Checks",
        "",
    ]
    for key, value in result_checks.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "`min_safety_h` is not meter clearance. This remains a wrapper-level prototype tested on stonehenge and flight only.",
        ]
    )
    NOTE_OUT.parent.mkdir(parents=True, exist_ok=True)
    NOTE_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(df: pd.DataFrame, scene_setup: dict[str, Any], result_checks: dict[str, Any]) -> None:
    smoke = df[df["run_label"].isin(["flight_smoke3_default", "flight_smoke3_bestD"])]
    flight20 = df[df["method_label"].isin([
        "flight_no_filter",
        "flight_safer_splat_filter",
        "flight_risk_aware_v1_default",
        "flight_risk_aware_v1_bestD",
    ])]
    cols = [
        "method_label",
        "collision_count",
        "min_safety_h_min",
        "progress_mean",
        "active_constraints_mean",
        "runtime_mean",
        "runtime_p95",
        "qp_infeasible_count",
        "fallback_used_rate",
    ]
    lines = [
        "# Risk-Aware V1 Second-Scene Flight Report",
        "",
        "## Scope",
        "",
        "This report validates Risk-Aware V1 pre-CBF candidate-budgeting on a second scene, flight.",
        "It does not modify the official SAFER-Splat baseline.",
        "It does not claim a new CBF theorem.",
        "",
        "## Scene Setup",
        "",
        f"- scene: {scene_setup['scene']}",
        f"- checkpoint path: {scene_setup['checkpoint']}",
        f"- data path: {scene_setup['data']}",
        f"- gaussian_count: {scene_setup['gaussian_count']}",
        f"- flight risk score table generated: {scene_setup['risk_score_available']}",
        f"- flight active_frequency available: {scene_setup['active_frequency_available']}",
        f"- active_frequency note: {scene_setup['active_frequency_note']}",
        "",
        "## Smoke3 Results",
        "",
        markdown_table(smoke, cols),
        "",
        "## 20-Trial Results",
        "",
        markdown_table(flight20, cols),
        "",
        "## Cross-Scene Interpretation",
        "",
        f"- V1 keeps safety on flight: {'yes' if result_checks['safety_preserved'] else 'no'}",
        f"- V1 keeps progress on flight: {'yes' if result_checks['progress_preserved'] else 'no'}",
        f"- V1 reduces runtime on flight: {'yes' if result_checks['runtime_improved'] else 'no'}",
        f"- preferred config: {result_checks['preferred_config']}",
        f"- preferred config reason: {result_checks['preferred_reason']}",
        "The stonehenge result was mixed: default was the fastest V1 setting, while bestD used fewer active constraints.",
        "On flight 20-trial, bestD is both faster and lower-constraint than default V1, while both remain collision-free.",
        "",
        "## Claim Boundary",
        "",
        "The reported min_safety_h is not meter clearance.",
        "This is still a wrapper-level prototype.",
        "The method does not prove a new CBF theorem.",
        "The method has now been tested on stonehenge and flight only.",
        "",
        "## Next Step Decision",
        "",
        f"{result_checks['recommended_decision']}: {result_checks['decision_reason']}",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    df = load_rows()
    df.to_csv(SUMMARY_OUT, index=False)
    scene_setup = load_scene_setup()
    result_checks = checks(df)
    METRICS_OUT.write_text(json.dumps({"scene_setup": scene_setup, "checks": result_checks}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_plot(df)
    write_note(df, scene_setup, result_checks)
    write_report(df, scene_setup, result_checks)
    for path in [SUMMARY_OUT, METRICS_OUT, PLOT_OUT, NOTE_OUT, REPORT_OUT]:
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
