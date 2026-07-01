#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


SUMMARY_COLUMNS = [
    "dataset",
    "scene",
    "method",
    "rows",
    "collision_count",
    "collision_free_count",
    "min_safety_h_min",
    "min_safety_h_mean",
    "goal_distance_reduction_ratio_mean",
    "intervention_rate_mean",
    "control_deviation_mean_mean",
    "active_constraints_mean_mean",
    "runtime_mean_mean",
    "runtime_p95_mean",
    "qp_infeasible_count_sum",
    "fallback_used_rate",
    "candidate_count_final_mean",
    "candidate_count_final_min",
    "candidate_count_final_p95",
    "candidate_count_final_max",
    "v1_insertion_level",
    "source_dir",
]


def parse_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def num(value: Any) -> float | None:
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


def read_summary_dir(path: Path, dataset: str) -> list[dict[str, Any]]:
    summary_path = path / "summary.csv"
    if not summary_path.exists():
        return []
    summary = pd.read_csv(summary_path)
    debug_stats = read_debug_stats(path / "v1_candidate_debug.csv")
    rows: list[dict[str, Any]] = []
    for _, row in summary.iterrows():
        method = str(row.get("method", ""))
        out = {
            "dataset": dataset,
            "scene": row.get("scene", ""),
            "method": method,
            "rows": row.get("rows", ""),
            "collision_count": row.get("collision_count", ""),
            "collision_free_count": row.get("collision_free_count", ""),
            "min_safety_h_min": row.get("min_safety_h_min", ""),
            "min_safety_h_mean": row.get("min_safety_h_mean", ""),
            "goal_distance_reduction_ratio_mean": row.get("goal_distance_reduction_ratio_mean", ""),
            "intervention_rate_mean": row.get("intervention_rate_mean", ""),
            "control_deviation_mean_mean": row.get("control_deviation_mean_mean", ""),
            "active_constraints_mean_mean": row.get("active_constraints_mean_mean", ""),
            "runtime_mean_mean": row.get("runtime_mean_mean", ""),
            "runtime_p95_mean": row.get("runtime_p95_mean", ""),
            "qp_infeasible_count_sum": row.get("qp_infeasible_count_sum", ""),
            "fallback_used_rate": "",
            "candidate_count_final_mean": "",
            "candidate_count_final_min": "",
            "candidate_count_final_p95": "",
            "candidate_count_final_max": "",
            "v1_insertion_level": "",
            "source_dir": str(path),
        }
        if method == "risk_aware_v1_pre_cbf":
            out.update(debug_stats)
        rows.append(out)
    return rows


def read_ablation(path: Path) -> list[dict[str, Any]]:
    ablation_path = path / "ablation_summary.csv"
    if not ablation_path.exists():
        return []
    table = pd.read_csv(ablation_path)
    rows: list[dict[str, Any]] = []
    for _, row in table.iterrows():
        method = str(row.get("ablation_id", row.get("config", row.get("method", "ablation"))))
        rows.append(
            {
                "dataset": "v0_ablation_20",
                "scene": row.get("scene", "stonehenge"),
                "method": method,
                "rows": row.get("rows", ""),
                "collision_count": row.get("collision_count", ""),
                "collision_free_count": row.get("collision_free_count", ""),
                "min_safety_h_min": row.get("min_safety_h_min", ""),
                "min_safety_h_mean": row.get("min_safety_h_mean", ""),
                "goal_distance_reduction_ratio_mean": row.get("goal_distance_reduction_ratio_mean", ""),
                "intervention_rate_mean": row.get("intervention_rate_mean", ""),
                "control_deviation_mean_mean": row.get("control_deviation_mean", row.get("control_deviation_mean_mean", "")),
                "active_constraints_mean_mean": row.get("active_constraints_mean", row.get("active_constraints_mean_mean", "")),
                "runtime_mean_mean": row.get("runtime_mean", row.get("runtime_mean_mean", "")),
                "runtime_p95_mean": row.get("runtime_p95", row.get("runtime_p95_mean", "")),
                "qp_infeasible_count_sum": row.get("qp_infeasible_count", row.get("qp_infeasible_count_sum", "")),
                "fallback_used_rate": row.get("fallback_used_rate", ""),
                "candidate_count_final_mean": "",
                "candidate_count_final_min": "",
                "candidate_count_final_p95": "",
                "candidate_count_final_max": "",
                "v1_insertion_level": "",
                "source_dir": str(path),
            }
        )
    return rows


def read_debug_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "fallback_used_rate": "",
            "candidate_count_final_mean": "",
            "candidate_count_final_min": "",
            "candidate_count_final_p95": "",
            "candidate_count_final_max": "",
            "v1_insertion_level": "",
        }
    rows = list(csv.DictReader(path.open("r", newline="", encoding="utf-8")))
    if not rows:
        return {
            "fallback_used_rate": "",
            "candidate_count_final_mean": "",
            "candidate_count_final_min": "",
            "candidate_count_final_p95": "",
            "candidate_count_final_max": "",
            "v1_insertion_level": "",
        }
    fallback = [parse_bool(r.get("fallback_used")) for r in rows]
    fallback_numeric = [1.0 if v is True else 0.0 for v in fallback if v is not None]
    candidates = [num(r.get("candidate_count_final")) for r in rows]
    candidates = [v for v in candidates if v is not None]
    levels = [str(r.get("v1_insertion_level", "")).strip() for r in rows if str(r.get("v1_insertion_level", "")).strip()]
    level = max(set(levels), key=levels.count) if levels else ""
    return {
        "fallback_used_rate": mean(fallback_numeric),
        "candidate_count_final_mean": mean(candidates),
        "candidate_count_final_min": min(candidates) if candidates else "",
        "candidate_count_final_p95": float(pd.Series(candidates).quantile(0.95)) if candidates else "",
        "candidate_count_final_max": max(candidates) if candidates else "",
        "v1_insertion_level": level,
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows available._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = f"{value:.10g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def pick(rows: list[dict[str, Any]], dataset: str, method: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("dataset") == dataset and row.get("method") == method:
            return row
    return None


def comparison_rows(rows: list[dict[str, Any]], dataset: str) -> list[dict[str, Any]]:
    if dataset == "v1_100":
        selected = []
        for method in ["no_filter", "safer_splat_filter", "risk_aware_v1_pre_cbf"]:
            row = pick(rows, "v1_100", method)
            if row:
                selected.append(row)
        v0 = pick(rows, "v0_100", "risk_aware_topk_v0")
        if v0:
            selected.append(v0)
        return selected
    return [r for r in rows if r.get("dataset") == dataset]


def write_plot(rows: list[dict[str, Any]], figure_path: Path, dataset: str = "v1_20") -> None:
    v1_rows = comparison_rows(rows, dataset)
    if not v1_rows:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = [
        "collision_count",
        "goal_distance_reduction_ratio_mean",
        "active_constraints_mean_mean",
        "runtime_mean_mean",
        "runtime_p95_mean",
        "candidate_count_final_mean",
        "fallback_used_rate",
    ]
    methods = [r["method"] for r in v1_rows]
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        values = [num(r.get(metric)) or 0.0 for r in v1_rows]
        ax.bar(methods, values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
    for ax in axes.ravel()[len(metrics) :]:
        ax.axis("off")
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def decision(rows: list[dict[str, Any]]) -> tuple[str, str]:
    v1 = pick(rows, "v1_20", "risk_aware_v1_pre_cbf") or pick(rows, "v1_smoke3", "risk_aware_v1_pre_cbf")
    baseline = pick(rows, "v1_20", "safer_splat_filter")
    if not v1:
        return "TUNE_V1", "No V1 result rows are available."
    collision = num(v1.get("collision_count")) or 0.0
    min_h = num(v1.get("min_safety_h_min"))
    qp = num(v1.get("qp_infeasible_count_sum")) or 0.0
    if collision > 0 or min_h is None or min_h <= 0.0 or qp > 0:
        return "TUNE_V1", "V1 did not satisfy smoke/20-trial safety gates."
    runtime = num(v1.get("runtime_mean_mean"))
    baseline_runtime = num(baseline.get("runtime_mean_mean")) if baseline else None
    progress = num(v1.get("goal_distance_reduction_ratio_mean"))
    baseline_progress = num(baseline.get("goal_distance_reduction_ratio_mean")) if baseline else None
    if runtime is not None and baseline_runtime is not None and runtime < baseline_runtime:
        return "PROCEED_TO_100", "V1 preserved safety and reduced mean step runtime against the 20-trial SAFER-Splat baseline."
    if progress is not None and baseline_progress is not None and progress > baseline_progress:
        return "PROCEED_TO_100", "V1 preserved safety and improved progress against the 20-trial SAFER-Splat baseline."
    return "TUNE_V1", "V1 preserved safety but did not clearly improve progress or runtime in the current 20-trial run."


def decision_for_100(rows: list[dict[str, Any]]) -> tuple[str, str]:
    v1 = pick(rows, "v1_100", "risk_aware_v1_pre_cbf")
    baseline = pick(rows, "v1_100", "safer_splat_filter") or pick(rows, "v0_100", "safer_splat_filter")
    if not v1:
        return "TUNE_V1", "No V1 100-trial result rows are available."
    collision = num(v1.get("collision_count")) or 0.0
    min_h = num(v1.get("min_safety_h_min"))
    qp = num(v1.get("qp_infeasible_count_sum")) or 0.0
    if collision > 0 or min_h is None or min_h <= 0.0 or qp > 0:
        return "TUNE_V1", "V1 failed at least one 100-trial safety gate."
    runtime = num(v1.get("runtime_mean_mean"))
    baseline_runtime = num(baseline.get("runtime_mean_mean")) if baseline else None
    if runtime is not None and baseline_runtime is not None and runtime < baseline_runtime:
        return "PROCEED_TO_ABLATION", "V1 preserved safety and reduced mean step runtime at 100-trial scale."
    return "TUNE_V1", "V1 preserved safety at 100-trial scale but did not clearly reduce mean step runtime."


def write_analysis(rows: list[dict[str, Any]], output_path: Path, figure_path: Path) -> None:
    v1 = pick(rows, "v1_20", "risk_aware_v1_pre_cbf") or pick(rows, "v1_smoke3", "risk_aware_v1_pre_cbf")
    baseline = pick(rows, "v1_20", "safer_splat_filter")
    decision_name, decision_reason = decision(rows)
    lines = [
        "# Risk-Aware V1 Analysis",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary Table",
        "",
        markdown_table(rows, SUMMARY_COLUMNS),
        "",
        "## Questions",
        "",
    ]
    if v1:
        collision = num(v1.get("collision_count")) or 0.0
        min_h = num(v1.get("min_safety_h_min"))
        qp = num(v1.get("qp_infeasible_count_sum")) or 0.0
        candidate_mean = v1.get("candidate_count_final_mean", "")
        fallback_rate = v1.get("fallback_used_rate", "")
        lines += [
            f"1. Collision-free: {'yes' if collision == 0 else 'no'}.",
            f"2. Positive `min_safety_h`: {'yes' if min_h is not None and min_h > 0 else 'no'}; value = {v1.get('min_safety_h_min', '')}.",
            f"3. QP infeasible: {'no' if qp == 0 else 'yes'}; count = {v1.get('qp_infeasible_count_sum', '')}.",
            f"4. Candidate count reduction: V1 candidate_count_final_mean = {candidate_mean}.",
            f"5. Active constraints: V1 = {v1.get('active_constraints_mean_mean', '')}; baseline = {baseline.get('active_constraints_mean_mean', '') if baseline else ''}.",
            f"6. Runtime: V1 = {v1.get('runtime_mean_mean', '')}; baseline = {baseline.get('runtime_mean_mean', '') if baseline else ''}.",
            f"7. Progress: V1 = {v1.get('goal_distance_reduction_ratio_mean', '')}; baseline = {baseline.get('goal_distance_reduction_ratio_mean', '') if baseline else ''}.",
            f"8. Fallback used rate: {fallback_rate}.",
            f"9. V1/V0 distinction: V1 uses a loader-level subset before distance query; V0 trims constraints after baseline CBF construction.",
        ]
    else:
        lines.append("No V1 rows were available for analysis.")
    lines += [
        "",
        "## Decision",
        "",
        f"{decision_name}: {decision_reason}",
        "",
        f"Figure: `{figure_path}`",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(rows: list[dict[str, Any]], report_path: Path) -> None:
    smoke = [r for r in rows if r.get("dataset") == "v1_smoke3"]
    twenty = [r for r in rows if r.get("dataset") == "v1_20"]
    v1 = pick(rows, "v1_20", "risk_aware_v1_pre_cbf") or pick(rows, "v1_smoke3", "risk_aware_v1_pre_cbf")
    decision_name, decision_reason = decision(rows)
    lines = [
        "# Risk-Aware V1 Pre-CBF Candidate-Budget Prototype",
        "",
        "## Scope",
        "",
        "This report evaluates a V1 pre-CBF candidate-budgeting prototype.",
        "It does not modify the official SAFER-Splat baseline.",
        "It does not claim a new CBF theorem.",
        "",
        "## Feasibility Conclusion",
        "",
        "`PARTIALLY_FEASIBLE`.",
        "",
        "The official loader has no native candidate-subset API, but a reproduction-only `SubsetGSplatLoader` can temporarily expose subset tensors before the official distance query and restore the full tensors after each query.",
        "",
        "## Method",
        "",
        "- candidate budget: 2000",
        "- near-distance threshold: 0.08",
        "- heading threshold: distance 0.25 and cosine 0.5",
        "- risk score: `risk_v2_hybrid`",
        "- hard fallback: full official baseline query if the candidate subset is too small or selector metadata fails",
        "- actual insertion level: `partial_pre_cbf`",
        "",
        "## Smoke3 Results",
        "",
        markdown_table(smoke, SUMMARY_COLUMNS),
        "",
        "## 20-Trial Results",
        "",
        markdown_table(twenty, SUMMARY_COLUMNS),
        "",
        "## Honest Interpretation",
        "",
        "If V1 only falls back to baseline most of the time, it is not a real V1 improvement.",
        "If V1 reduces candidates but causes collision, it is unsafe.",
        "If V1 reduces runtime without losing safety, it is promising.",
        "If V1 still does not improve progress, that should be reported directly.",
        "",
    ]
    if v1:
        lines += [
            f"Observed V1 fallback_used_rate: {v1.get('fallback_used_rate', '')}.",
            f"Observed V1 candidate_count_final_mean: {v1.get('candidate_count_final_mean', '')}.",
            f"Observed V1 collision_count: {v1.get('collision_count', '')}.",
            f"Observed V1 min_safety_h_min: {v1.get('min_safety_h_min', '')}.",
            f"Observed V1 runtime_mean_mean: {v1.get('runtime_mean_mean', '')}.",
            f"Observed V1 progress mean: {v1.get('goal_distance_reduction_ratio_mean', '')}.",
            "",
        ]
    lines += [
        "## Next Step Decision",
        "",
        f"{decision_name}: {decision_reason}",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_analysis_100(rows: list[dict[str, Any]], output_path: Path, figure_path: Path) -> None:
    table = comparison_rows(rows, "v1_100")
    v1 = pick(rows, "v1_100", "risk_aware_v1_pre_cbf")
    baseline = pick(rows, "v1_100", "safer_splat_filter") or pick(rows, "v0_100", "safer_splat_filter")
    decision_name, decision_reason = decision_for_100(rows)
    lines = [
        "# Risk-Aware V1 100-Trial Analysis",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 100-Trial Comparison",
        "",
        markdown_table(table, SUMMARY_COLUMNS),
        "",
        "## V1 Safety Check",
        "",
    ]
    if v1:
        collision = num(v1.get("collision_count")) or 0.0
        min_h = num(v1.get("min_safety_h_min"))
        qp = num(v1.get("qp_infeasible_count_sum")) or 0.0
        lines += [
            f"1. collision_count == 0: {'yes' if collision == 0 else 'NO'}; value = {v1.get('collision_count', '')}.",
            f"2. min_safety_h_min > 0: {'yes' if min_h is not None and min_h > 0 else 'NO'}; value = {v1.get('min_safety_h_min', '')}.",
            f"3. qp_infeasible_count == 0: {'yes' if qp == 0 else 'NO'}; value = {v1.get('qp_infeasible_count_sum', '')}.",
            f"4. fallback_used_rate: {v1.get('fallback_used_rate', '')}.",
            f"5. candidate_count_final: mean = {v1.get('candidate_count_final_mean', '')}, min = {v1.get('candidate_count_final_min', '')}, p95 = {v1.get('candidate_count_final_p95', '')}, max = {v1.get('candidate_count_final_max', '')}.",
        ]
        near_zero = num(v1.get("min_safety_h_min"))
        if near_zero is not None and near_zero < 1e-4:
            lines.append("6. min_safety_h_min is close to zero and should be treated as a tuning risk.")
        else:
            lines.append("6. No min_safety_h near-zero warning under the 1e-4 heuristic.")
    else:
        lines.append("No V1 100-trial rows were available.")
    lines += [
        "",
        "## What Improved",
        "",
    ]
    if v1 and baseline:
        v1_collision = num(v1.get("collision_count")) or 0.0
        v1_min_h = num(v1.get("min_safety_h_min"))
        v1_qp = num(v1.get("qp_infeasible_count_sum")) or 0.0
        v1_progress = num(v1.get("goal_distance_reduction_ratio_mean"))
        base_progress = num(baseline.get("goal_distance_reduction_ratio_mean"))
        v1_active = num(v1.get("active_constraints_mean_mean"))
        base_active = num(baseline.get("active_constraints_mean_mean"))
        v1_runtime = num(v1.get("runtime_mean_mean"))
        base_runtime = num(baseline.get("runtime_mean_mean"))
        lines += [
            f"- safety preserved: {'yes' if v1_collision == 0 and v1_min_h is not None and v1_min_h > 0 else 'no'}",
            f"- progress improved: {'yes' if v1_progress is not None and base_progress is not None and v1_progress > base_progress else 'no'}",
            f"- active constraints reduced: {'yes' if v1_active is not None and base_active is not None and v1_active < base_active else 'no'}",
            f"- runtime improved: {'yes' if v1_runtime is not None and base_runtime is not None and v1_runtime < base_runtime else 'no'}",
            f"- QP stability preserved: {'yes' if v1_qp == 0 else 'no'}",
        ]
    lines += [
        "",
        "## Decision",
        "",
        f"{decision_name}: {decision_reason}",
        "",
        f"Figure: `{figure_path}`",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report_100(rows: list[dict[str, Any]], report_path: Path) -> None:
    table = comparison_rows(rows, "v1_100")
    v1 = pick(rows, "v1_100", "risk_aware_v1_pre_cbf")
    baseline = pick(rows, "v1_100", "safer_splat_filter") or pick(rows, "v0_100", "safer_splat_filter")
    decision_name, decision_reason = decision_for_100(rows)
    lines = [
        "# Risk-Aware V1 Pre-CBF 100-Trial Validation",
        "",
        "## Scope",
        "",
        "This report validates Risk-Aware V1 pre-CBF candidate-budgeting on the stonehenge 100-trial official checkpoint.",
        "It does not modify the official SAFER-Splat baseline.",
        "It does not claim a new CBF safety theorem.",
        "",
        "## Method",
        "",
        "- candidate budget: 2000",
        "- near-distance threshold: 0.08",
        "- heading threshold: distance 0.25 and cosine 0.5",
        "- risk score: `risk_v2_hybrid`",
        "- hard fallback: full official baseline query if the candidate subset is too small or selector metadata fails",
        "- actual insertion level: `partial_pre_cbf`",
        "- uses SubsetGSplatLoader: yes, as a reproduction-only wrapper",
        "- modifies official source code: no",
        "",
        "## 100-Trial Comparison",
        "",
        markdown_table(table, SUMMARY_COLUMNS),
        "",
        "## What Improved",
        "",
    ]
    if v1 and baseline:
        v1_collision = num(v1.get("collision_count")) or 0.0
        v1_min_h = num(v1.get("min_safety_h_min"))
        v1_qp = num(v1.get("qp_infeasible_count_sum")) or 0.0
        v1_progress = num(v1.get("goal_distance_reduction_ratio_mean"))
        base_progress = num(baseline.get("goal_distance_reduction_ratio_mean"))
        v1_active = num(v1.get("active_constraints_mean_mean"))
        base_active = num(baseline.get("active_constraints_mean_mean"))
        v1_runtime = num(v1.get("runtime_mean_mean"))
        base_runtime = num(baseline.get("runtime_mean_mean"))
        lines += [
            f"- safety preserved: {'yes' if v1_collision == 0 and v1_min_h is not None and v1_min_h > 0 else 'no'}",
            f"- progress improved: {'yes' if v1_progress is not None and base_progress is not None and v1_progress > base_progress else 'no'}",
            f"- active constraints reduced: {'yes' if v1_active is not None and base_active is not None and v1_active < base_active else 'no'}",
            f"- runtime improved: {'yes' if v1_runtime is not None and base_runtime is not None and v1_runtime < base_runtime else 'no'}",
            f"- QP stability preserved: {'yes' if v1_qp == 0 else 'no'}",
            "",
        ]
    lines += [
        "## Honest Interpretation",
        "",
        "If V1 preserves safety and reduces runtime, this is promising preliminary evidence for pre-CBF candidate budgeting.",
        "If progress remains unchanged, do not claim navigation progress improvement.",
        "If V1 does not reduce runtime at 100-trial scale, do not claim computational improvement.",
        "If V1 causes collision or QP infeasible, do not proceed; V1 fallback is insufficient.",
        "",
        "## Claim Boundary",
        "",
        "This is still a wrapper-level prototype.",
        "The reported `min_safety_h` is not meter clearance.",
        "The method does not prove a new CBF theorem.",
        "The method has only been validated on stonehenge so far.",
        "",
        "## Next Step Decision",
        "",
        f"{decision_name}: {decision_reason}",
        "",
        "V1 ablation is prepared but not executed in this task unless explicitly requested.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Risk-Aware V1 pre-CBF prototype outputs.")
    parser.add_argument("--root", type=Path, default=Path("work/risk_aware_cbf"))
    args = parser.parse_args()

    root = args.root
    rows: list[dict[str, Any]] = []
    rows += read_summary_dir(root / "results/risk_aware_v1_pre_cbf_stonehenge_smoke3", "v1_smoke3")
    rows += read_summary_dir(root / "results/risk_aware_v1_pre_cbf_stonehenge_20", "v1_20")
    rows += read_summary_dir(root / "results/risk_aware_v1_pre_cbf_stonehenge_100", "v1_100")
    rows += read_summary_dir(root / "results/risk_aware_topk_stonehenge_100", "v0_100")
    rows += read_summary_dir(root / "results/baseline_detailed_logging_stonehenge_100", "baseline_detailed_100")
    rows += read_ablation(root / "results/risk_aware_topk_ablation_stonehenge_20")

    output_csv = root / "results/risk_aware_v1_analysis_summary.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=SUMMARY_COLUMNS).to_csv(output_csv, index=False)
    output_csv_100 = root / "results/risk_aware_v1_100_analysis_summary.csv"
    pd.DataFrame(comparison_rows(rows, "v1_100"), columns=SUMMARY_COLUMNS).to_csv(output_csv_100, index=False)

    figure_path = root / "figures/risk_aware_v1_comparison_plots.png"
    write_plot(rows, figure_path, dataset="v1_20")
    figure_path_100 = root / "figures/risk_aware_v1_100_comparison_plots.png"
    write_plot(rows, figure_path_100, dataset="v1_100")
    write_analysis(rows, root / "notes/RISK_AWARE_V1_ANALYSIS.md", figure_path)
    write_analysis_100(rows, root / "notes/RISK_AWARE_V1_100_ANALYSIS.md", figure_path_100)
    write_report(rows, root / "REPORT_RISK_AWARE_V1_PRE_CBF.md")
    write_report_100(rows, root / "REPORT_RISK_AWARE_V1_100_TRIAL.md")
    print(f"wrote {output_csv}")
    print(f"wrote {output_csv_100}")
    print(f"wrote {figure_path}")
    print(f"wrote {figure_path_100}")
    print(f"wrote {root / 'notes/RISK_AWARE_V1_ANALYSIS.md'}")
    print(f"wrote {root / 'notes/RISK_AWARE_V1_100_ANALYSIS.md'}")
    print(f"wrote {root / 'REPORT_RISK_AWARE_V1_PRE_CBF.md'}")
    print(f"wrote {root / 'REPORT_RISK_AWARE_V1_100_TRIAL.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
