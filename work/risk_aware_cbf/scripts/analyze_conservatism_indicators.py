#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT_ROOT = ROOT / "work/risk_aware_cbf"
RESULTS = OUT_ROOT / "results"
FIGURES = OUT_ROOT / "figures"
NOTES = OUT_ROOT / "notes"
TRIALS = ROOT / "reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trials.csv"
FEATURES = RESULTS / "trajectory_interaction_features.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values)
    ranks = np.empty_like(order, dtype=float)
    sorted_values = values[order]
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and sorted_values[j] == sorted_values[i]:
            j += 1
        ranks[order[i:j]] = (i + j - 1) / 2.0 + 1.0
        i = j
    return ranks


def corr(xs: list[float], ys: list[float]) -> tuple[object, object]:
    if len(xs) < 3:
        return "", ""
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if np.std(x) == 0 or np.std(y) == 0:
        pearson = ""
    else:
        pearson = float(np.corrcoef(x, y)[0, 1])
    rx = rankdata(x)
    ry = rankdata(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        spearman = ""
    else:
        spearman = float(np.corrcoef(rx, ry)[0, 1])
    return pearson, spearman


def merged_rows() -> list[dict[str, str]]:
    trials = read_csv(TRIALS)
    features = {(row["method"], row["trial"]): row for row in read_csv(FEATURES)}
    merged = []
    for row in trials:
        merged_row = dict(row)
        feature = features.get((row["method"], row["trial"]), {})
        for key, value in feature.items():
            if key not in merged_row:
                merged_row[key] = value
            else:
                merged_row[f"feature_{key}"] = value
        merged.append(merged_row)
    return merged


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    rows = merged_rows()
    safer = [row for row in rows if row["method"] == "safer_splat_filter"]

    target = "goal_distance_reduction_ratio"
    candidates = [
        "intervention_rate",
        "active_constraints_mean",
        "min_safety_h",
        "control_deviation_mean",
        "runtime_mean",
        "num_steps",
        "nearby_gaussian_count_r005",
        "nearby_gaussian_count_r010",
        "nearby_gaussian_count_r020",
        "nearby_opacity_mean",
        "nearby_max_scale_mean",
        "nearby_anisotropy_mean",
        "nearby_volume_proxy_mean",
        "nearest_gaussian_distance_mean",
        "nearest_gaussian_distance_min",
    ]

    corr_rows = []
    for feature in candidates:
        pairs = []
        for row in safer:
            x = parse_float(row.get(feature))
            y = parse_float(row.get(target))
            if x is not None and y is not None:
                pairs.append((x, y))
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        pearson, spearman = corr(xs, ys)
        corr_rows.append(
            {
                "method": "safer_splat_filter",
                "feature": feature,
                "target": target,
                "n": len(pairs),
                "pearson": pearson,
                "spearman": spearman,
                "note": "insufficient data" if len(pairs) < 3 else "",
            }
        )

    corr_csv = RESULTS / "conservatism_correlation_table.csv"
    with corr_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(corr_rows[0].keys()))
        writer.writeheader()
        writer.writerows(corr_rows)

    progress_values = np.asarray([parse_float(row[target]) for row in safer], dtype=float)
    low_cut = float(np.percentile(progress_values, 25))
    high_cut = float(np.percentile(progress_values, 75))
    low = [row for row in safer if (parse_float(row[target]) or 0.0) <= low_cut]
    high = [row for row in safer if (parse_float(row[target]) or 0.0) >= high_cut]

    group_rows = []
    for feature in candidates + [target, "final_goal_distance", "closest_goal_distance"]:
        low_values = [parse_float(row.get(feature)) for row in low]
        high_values = [parse_float(row.get(feature)) for row in high]
        low_values = [v for v in low_values if v is not None]
        high_values = [v for v in high_values if v is not None]
        group_rows.append(
            {
                "feature": feature,
                "low_progress_n": len(low_values),
                "high_progress_n": len(high_values),
                "low_progress_mean": float(np.mean(low_values)) if low_values else "",
                "high_progress_mean": float(np.mean(high_values)) if high_values else "",
                "high_minus_low": float(np.mean(high_values) - np.mean(low_values)) if low_values and high_values else "",
            }
        )

    group_csv = RESULTS / "conservatism_group_comparison.csv"
    with group_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()))
        writer.writeheader()
        writer.writerows(group_rows)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    plot_features = ["intervention_rate", "active_constraints_mean", "min_safety_h", "control_deviation_mean"]
    for ax, feature in zip(axes.ravel(), plot_features):
        xs = [parse_float(row.get(feature)) for row in safer]
        ys = [parse_float(row.get(target)) for row in safer]
        clean = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if clean:
            ax.scatter([p[0] for p in clean], [p[1] for p in clean], s=22, alpha=0.75, color="#1b9e77")
        ax.set_xlabel(feature)
        ax.set_ylabel(target)
        ax.set_title(f"{feature} vs progress")
        ax.grid(alpha=0.2)
    fig.tight_layout()
    plot_path = FIGURES / "conservatism_indicator_plots.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    ranked = sorted(
        [row for row in corr_rows if row["spearman"] not in ("", None)],
        key=lambda row: abs(float(row["spearman"])),
        reverse=True,
    )
    note = {
        "target": target,
        "safer_rows": len(safer),
        "low_progress_cutoff": low_cut,
        "high_progress_cutoff": high_cut,
        "strongest_abs_spearman": ranked[:5],
        "gaussian_neighborhood_limitation": "Most trajectory rows do not have sampled trajectory points, so nearby Gaussian correlations are often insufficient.",
        "outputs": [str(corr_csv.relative_to(ROOT)), str(group_csv.relative_to(ROOT)), str(plot_path.relative_to(ROOT))],
    }
    (NOTES / "CONSERVATISM_ANALYSIS_NOTES.md").write_text(
        "# Conservatism Analysis Notes\n\n"
        + "```json\n"
        + json.dumps(note, indent=2)
        + "\n```\n\n"
        + "The analysis uses simple correlations and top/bottom progress group comparisons only. It is not a causal model.\n",
        encoding="utf-8",
    )
    print(json.dumps(note, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
