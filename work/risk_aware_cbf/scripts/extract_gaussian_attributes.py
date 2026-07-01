#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from splat.gsplat_utils import GSplatLoader  # noqa: E402


OUT_ROOT = ROOT / "work/risk_aware_cbf"
RESULTS = OUT_ROOT / "results"
FIGURES = OUT_ROOT / "figures"
NOTES = OUT_ROOT / "notes"
CHECKPOINT = ROOT / "outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml"
EPS = 1e-12

SCENE_CHECKPOINTS = {
    "stonehenge": ROOT / "outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml",
    "flight": ROOT / "outputs/flight/splatfacto/2024-09-12_172434/config.yml",
}


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def prefixed_path(prefix: Path, suffix: str) -> Path:
    return Path(f"{prefix}{suffix}")


def to_numpy(tensor):
    if tensor is None:
        return None
    if isinstance(tensor, torch.Tensor):
        return tensor.detach().cpu().numpy()
    return np.asarray(tensor)


def numeric_summary(name: str, values: np.ndarray) -> dict[str, object]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "attribute": name,
            "count": 0,
            "mean": "",
            "std": "",
            "min": "",
            "q25": "",
            "median": "",
            "q75": "",
            "max": "",
        }
    return {
        "attribute": name,
        "count": int(values.size),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "min": float(np.min(values)),
        "q25": float(np.percentile(values, 25)),
        "median": float(np.median(values)),
        "q75": float(np.percentile(values, 75)),
        "max": float(np.max(values)),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract static Gaussian attributes from a GSplat checkpoint.")
    parser.add_argument("--scene", choices=sorted(SCENE_CHECKPOINTS), default="stonehenge")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--output-prefix", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)

    checkpoint = resolve_repo_path(args.checkpoint) if args.checkpoint else SCENE_CHECKPOINTS[args.scene]
    output_prefix = resolve_repo_path(args.output_prefix) if args.output_prefix else RESULTS / args.scene

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"scene={args.scene}")
    print(f"checkpoint={checkpoint}")
    print(f"device={device}")
    loader = GSplatLoader(checkpoint, device)

    means = to_numpy(loader.means).astype(float)
    scales = to_numpy(loader.scales).astype(float)
    rots = to_numpy(getattr(loader, "rots", None))
    opacities = to_numpy(getattr(loader, "opacities", None))
    colors = to_numpy(getattr(loader, "colors", None))

    gaussian_count = int(means.shape[0])
    scene_center = np.mean(means, axis=0)
    max_scale = np.max(scales, axis=1)
    min_scale = np.min(scales, axis=1)
    mean_scale = np.mean(scales, axis=1)
    anisotropy = max_scale / np.maximum(min_scale, EPS)
    volume_proxy = np.prod(scales, axis=1)
    distance_to_scene_center = np.linalg.norm(means - scene_center[None, :], axis=1)

    if opacities is not None:
        opacities = np.asarray(opacities).reshape(-1)
    if colors is not None:
        colors = np.asarray(colors)
        color_or_sh_norm = np.linalg.norm(colors.reshape(gaussian_count, -1), axis=1)
    else:
        color_or_sh_norm = None

    rows: list[dict[str, object]] = []
    for idx in range(gaussian_count):
        row: dict[str, object] = {
            "gaussian_id": idx,
            "mean_x": float(means[idx, 0]),
            "mean_y": float(means[idx, 1]),
            "mean_z": float(means[idx, 2]),
            "scale_x": float(scales[idx, 0]),
            "scale_y": float(scales[idx, 1]),
            "scale_z": float(scales[idx, 2]),
            "max_scale": float(max_scale[idx]),
            "min_scale": float(min_scale[idx]),
            "mean_scale": float(mean_scale[idx]),
            "anisotropy": float(anisotropy[idx]),
            "volume_proxy": float(volume_proxy[idx]),
            "opacity": float(opacities[idx]) if opacities is not None else "Not available",
            "distance_to_scene_center": float(distance_to_scene_center[idx]),
            "color_or_sh_norm": float(color_or_sh_norm[idx]) if color_or_sh_norm is not None else "Not available",
        }
        if rots is not None:
            for q_idx, value in enumerate(np.asarray(rots[idx]).reshape(-1)):
                row[f"rotation_q{q_idx}"] = float(value)
        else:
            row["rotation"] = "Not available"
        rows.append(row)

    fieldnames = list(rows[0].keys())
    full_csv = prefixed_path(output_prefix, "_gaussian_attributes.csv")
    sample_csv = prefixed_path(output_prefix, "_gaussian_attributes_sample.csv")
    write_csv(full_csv, rows, fieldnames)
    write_csv(sample_csv, rows[:200], fieldnames)

    summary_rows = [
        numeric_summary("mean_x", means[:, 0]),
        numeric_summary("mean_y", means[:, 1]),
        numeric_summary("mean_z", means[:, 2]),
        numeric_summary("scale_x", scales[:, 0]),
        numeric_summary("scale_y", scales[:, 1]),
        numeric_summary("scale_z", scales[:, 2]),
        numeric_summary("max_scale", max_scale),
        numeric_summary("min_scale", min_scale),
        numeric_summary("mean_scale", mean_scale),
        numeric_summary("anisotropy", anisotropy),
        numeric_summary("volume_proxy", volume_proxy),
        numeric_summary("distance_to_scene_center", distance_to_scene_center),
    ]
    if opacities is not None:
        summary_rows.append(numeric_summary("opacity", opacities))
    if color_or_sh_norm is not None:
        summary_rows.append(numeric_summary("color_or_sh_norm", color_or_sh_norm))
    if rots is not None:
        rots_flat = np.asarray(rots).reshape(gaussian_count, -1)
        for q_idx in range(rots_flat.shape[1]):
            summary_rows.append(numeric_summary(f"rotation_q{q_idx}", rots_flat[:, q_idx]))

    summary_csv = prefixed_path(output_prefix, "_gaussian_attribute_summary.csv")
    write_csv(
        summary_csv,
        summary_rows,
        ["attribute", "count", "mean", "std", "min", "q25", "median", "q75", "max"],
    )

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    plot_items = [
        ("max_scale", max_scale),
        ("mean_scale", mean_scale),
        ("anisotropy", anisotropy),
        ("volume_proxy", volume_proxy),
        ("opacity", opacities if opacities is not None else np.array([])),
        ("distance_to_scene_center", distance_to_scene_center),
    ]
    for ax, (name, values) in zip(axes.ravel(), plot_items):
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        if values.size:
            ax.hist(values, bins=80, color="#406c8a", alpha=0.88)
        else:
            ax.text(0.5, 0.5, "Not available", ha="center", va="center")
        ax.set_title(name)
        ax.set_ylabel("count")
    fig.tight_layout()
    hist_path = FIGURES / f"{args.scene}_gaussian_attribute_histograms.png"
    fig.savefig(hist_path, dpi=160)
    plt.close(fig)

    available = ["means", "scales", "max/min/mean scale", "anisotropy", "volume_proxy", "distance_to_scene_center"]
    missing = []
    if opacities is not None:
        available.append("opacity")
    else:
        missing.append("opacity")
    if rots is not None:
        available.append("rotation/quaternion")
    else:
        missing.append("rotation/quaternion")
    if color_or_sh_norm is not None:
        available.append("color_or_sh_norm")
    else:
        missing.append("color_or_sh_norm")

    notes = {
        "scene": args.scene,
        "checkpoint": str(checkpoint.relative_to(ROOT) if checkpoint.is_relative_to(ROOT) else checkpoint),
        "gaussian_count": gaussian_count,
        "device": str(device),
        "available_attributes": available,
        "missing_attributes": missing,
        "outputs": {
            "full_csv": str(full_csv.relative_to(ROOT)),
            "sample_csv": str(sample_csv.relative_to(ROOT)),
            "summary_csv": str(summary_csv.relative_to(ROOT)),
            "histograms": str(hist_path.relative_to(ROOT)),
        },
    }
    (NOTES / f"{args.scene.upper()}_GAUSSIAN_ATTRIBUTE_EXTRACTION_NOTES.md").write_text(
        f"# Gaussian Attribute Extraction Notes: {args.scene}\n\n"
        + "```json\n"
        + json.dumps(notes, indent=2)
        + "\n```\n\n"
        + "All attributes were extracted from the official `GSplatLoader` without modifying SAFER-Splat source code.\n"
        + "`volume_proxy` is a scale-product proxy, not a physical occupancy volume guarantee.\n",
        encoding="utf-8",
    )

    print(json.dumps(notes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
