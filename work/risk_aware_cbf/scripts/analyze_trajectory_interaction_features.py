#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
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
SAMPLES = ROOT / "reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trajectory_samples.csv"
GAUSSIANS = RESULTS / "stonehenge_gaussian_attributes.csv"


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


def parse_bool(value: object) -> bool | None:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def load_gaussians() -> dict[str, np.ndarray] | None:
    if not GAUSSIANS.exists():
        return None
    rows = read_csv(GAUSSIANS)
    return {
        "means": np.asarray([[float(r["mean_x"]), float(r["mean_y"]), float(r["mean_z"])] for r in rows], dtype=float),
        "opacity": np.asarray([float(r["opacity"]) for r in rows], dtype=float),
        "max_scale": np.asarray([float(r["max_scale"]) for r in rows], dtype=float),
        "anisotropy": np.asarray([float(r["anisotropy"]) for r in rows], dtype=float),
        "volume_proxy": np.asarray([float(r["volume_proxy"]) for r in rows], dtype=float),
    }


def summarize_nearby(points: np.ndarray, gaussians: dict[str, np.ndarray]) -> dict[str, object]:
    means = gaussians["means"]
    nearest = []
    counts = {0.05: [], 0.10: [], 0.20: []}
    nearby_opacity = []
    nearby_max_scale = []
    nearby_anisotropy = []
    nearby_volume = []

    for point in points:
        dist = np.linalg.norm(means - point[None, :], axis=1)
        nearest.append(float(np.min(dist)))
        for radius in counts:
            mask = dist <= radius
            counts[radius].append(int(np.sum(mask)))
        mask = dist <= 0.10
        if np.any(mask):
            nearby_opacity.append(float(np.mean(gaussians["opacity"][mask])))
            nearby_max_scale.append(float(np.mean(gaussians["max_scale"][mask])))
            nearby_anisotropy.append(float(np.mean(gaussians["anisotropy"][mask])))
            nearby_volume.append(float(np.mean(gaussians["volume_proxy"][mask])))

    def mean_or_blank(values: list[float]) -> object:
        return float(np.mean(values)) if values else ""

    return {
        "nearest_gaussian_distance_mean": mean_or_blank(nearest),
        "nearest_gaussian_distance_min": float(np.min(nearest)) if nearest else "",
        "nearby_gaussian_count_r005": mean_or_blank(counts[0.05]),
        "nearby_gaussian_count_r010": mean_or_blank(counts[0.10]),
        "nearby_gaussian_count_r020": mean_or_blank(counts[0.20]),
        "nearby_opacity_mean": mean_or_blank(nearby_opacity),
        "nearby_max_scale_mean": mean_or_blank(nearby_max_scale),
        "nearby_anisotropy_mean": mean_or_blank(nearby_anisotropy),
        "nearby_volume_proxy_mean": mean_or_blank(nearby_volume),
    }


def group_label(row: dict[str, str], safer_low: float, safer_high: float) -> str:
    method = row["method"]
    progress = parse_float(row.get("goal_distance_reduction_ratio")) or 0.0
    collision = parse_bool(row.get("collision"))
    if method == "no_filter" and collision is True:
        return "no_filter_collision"
    if method == "safer_splat_filter" and collision is False and progress <= safer_low:
        return "safer_collision_free_low_progress"
    if method == "safer_splat_filter" and collision is False and progress >= safer_high:
        return "safer_collision_free_higher_progress"
    return "other"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)

    trials = read_csv(TRIALS)
    samples = read_csv(SAMPLES) if SAMPLES.exists() else []
    sample_map: dict[tuple[str, int], list[list[float]]] = defaultdict(list)
    for row in samples:
        sample_map[(row["method"], int(row["trial"]))].append([float(row["x"]), float(row["y"]), float(row["z"])])

    gaussians = load_gaussians()
    safer_progress = [
        parse_float(row.get("goal_distance_reduction_ratio"))
        for row in trials
        if row["method"] == "safer_splat_filter" and parse_float(row.get("goal_distance_reduction_ratio")) is not None
    ]
    safer_low = float(np.percentile(safer_progress, 25))
    safer_high = float(np.percentile(safer_progress, 75))

    feature_rows: list[dict[str, object]] = []
    for row in trials:
        method = row["method"]
        trial = int(row["trial"])
        num_steps = parse_float(row.get("num_steps")) or 0.0
        path_length = parse_float(row.get("path_length")) or 0.0
        dt = parse_float(row.get("dt")) or 0.05
        feature = {
            "trial": trial,
            "method": method,
            "group": group_label(row, safer_low, safer_high),
            "collision": row.get("collision", ""),
            "success": row.get("success", ""),
            "goal_distance_reduction_ratio": row.get("goal_distance_reduction_ratio", ""),
            "min_safety_h": row.get("min_safety_h", ""),
            "num_steps": row.get("num_steps", ""),
            "trajectory_length": path_length,
            "average_speed_proxy": path_length / max(num_steps * dt, 1e-12),
            "closest_goal_distance": row.get("closest_goal_distance", ""),
            "final_goal_distance": row.get("final_goal_distance", ""),
            "has_trajectory_samples": "False",
            "nearest_gaussian_distance_mean": "",
            "nearest_gaussian_distance_min": "",
            "nearby_gaussian_count_r005": "",
            "nearby_gaussian_count_r010": "",
            "nearby_gaussian_count_r020": "",
            "nearby_opacity_mean": "",
            "nearby_max_scale_mean": "",
            "nearby_anisotropy_mean": "",
            "nearby_volume_proxy_mean": "",
        }
        points = sample_map.get((method, trial), [])
        if points and gaussians is not None:
            feature["has_trajectory_samples"] = "True"
            feature.update(summarize_nearby(np.asarray(points, dtype=float), gaussians))
        feature_rows.append(feature)

    fieldnames = list(feature_rows[0].keys())
    out_csv = RESULTS / "trajectory_interaction_features.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(feature_rows)

    summary_rows = []
    for group in sorted({row["group"] for row in feature_rows}):
        rows = [row for row in feature_rows if row["group"] == group]
        for method in sorted({row["method"] for row in rows}):
            subset = [row for row in rows if row["method"] == method]
            progress = [parse_float(r["goal_distance_reduction_ratio"]) for r in subset]
            progress = [v for v in progress if v is not None]
            min_h = [parse_float(r["min_safety_h"]) for r in subset]
            min_h = [v for v in min_h if v is not None]
            summary_rows.append(
                {
                    "group": group,
                    "method": method,
                    "rows": len(subset),
                    "goal_distance_reduction_ratio_mean": float(np.mean(progress)) if progress else "",
                    "goal_distance_reduction_ratio_min": float(np.min(progress)) if progress else "",
                    "goal_distance_reduction_ratio_max": float(np.max(progress)) if progress else "",
                    "min_safety_h_mean": float(np.mean(min_h)) if min_h else "",
                    "sampled_trajectory_rows": sum(r["has_trajectory_samples"] == "True" for r in subset),
                }
            )

    summary_csv = RESULTS / "trajectory_interaction_feature_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    methods = ["no_filter", "safer_splat_filter"]
    colors = {"no_filter": "#d95f02", "safer_splat_filter": "#1b9e77"}
    for method in methods:
        rows = [r for r in feature_rows if r["method"] == method]
        progress = [parse_float(r["goal_distance_reduction_ratio"]) for r in rows]
        min_h = [parse_float(r["min_safety_h"]) for r in rows]
        steps = [parse_float(r["num_steps"]) for r in rows]
        final_goal = [parse_float(r["final_goal_distance"]) for r in rows]
        axes[0, 0].hist([v for v in progress if v is not None], bins=30, alpha=0.65, label=method, color=colors[method])
        axes[0, 1].scatter(progress, min_h, s=18, alpha=0.75, label=method, color=colors[method])
        axes[1, 0].scatter(steps, progress, s=18, alpha=0.75, label=method, color=colors[method])
        axes[1, 1].scatter(final_goal, progress, s=18, alpha=0.75, label=method, color=colors[method])
    axes[0, 0].set_title("Progress ratio distribution")
    axes[0, 1].set_title("min_safety_h vs progress")
    axes[1, 0].set_title("num_steps vs progress")
    axes[1, 1].set_title("final_goal_distance vs progress")
    for ax in axes.ravel():
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
    fig.tight_layout()
    plot_path = FIGURES / "trajectory_interaction_feature_plots.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    note = {
        "input_trials": str(TRIALS.relative_to(ROOT)),
        "input_trajectory_samples": str(SAMPLES.relative_to(ROOT)) if SAMPLES.exists() else "Not available",
        "gaussian_attributes": str(GAUSSIANS.relative_to(ROOT)) if GAUSSIANS.exists() else "Not available",
        "sampled_trajectory_keys": [f"{m}:{t}" for (m, t) in sorted(sample_map)],
        "limitation": "Gaussian-neighborhood trajectory features are computed only where trajectory_samples.csv provides sampled path points. Other rows retain trial-level metrics only.",
        "outputs": [str(out_csv.relative_to(ROOT)), str(summary_csv.relative_to(ROOT)), str(plot_path.relative_to(ROOT))],
    }
    (NOTES / "TRAJECTORY_INTERACTION_ANALYSIS_NOTES.md").write_text(
        "# Trajectory Interaction Analysis Notes\n\n"
        + "```json\n"
        + json.dumps(note, indent=2)
        + "\n```\n\n"
        + "No synthetic trajectory points were generated. Missing sampled trajectories are left without Gaussian-neighborhood features.\n",
        encoding="utf-8",
    )
    print(json.dumps(note, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
