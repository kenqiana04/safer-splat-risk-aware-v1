#!/usr/bin/env python3
"""Build static Gaussian risk-score tables for the risk-aware top-k wrapper."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "risk_aware_cbf"
RESULTS = BASE / "results"
FIGURES = BASE / "figures"
NOTES = BASE / "notes"

ATTR_PATH = RESULTS / "stonehenge_gaussian_attributes.csv"
FREQ_PATH = RESULTS / "active_gaussian_frequency.csv"
ACTIVE_PATH = RESULTS / "baseline_detailed_logging_stonehenge_100" / "active_constraints.csv"
OUT_TABLE = RESULTS / "risk_score_table_v0.csv"
OUT_SUMMARY = RESULTS / "risk_score_summary_v0.csv"
OUT_FIG = FIGURES / "risk_score_distribution_v0.png"
OUT_META = RESULTS / "risk_score_metadata_v0.json"


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def prefixed_path(prefix: Path, suffix: str) -> Path:
    return Path(f"{prefix}{suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static Gaussian risk-score tables for a scene.")
    parser.add_argument("--scene", default="stonehenge")
    parser.add_argument("--attributes-csv", type=Path, default=None)
    parser.add_argument("--active-frequency-csv", type=Path, default=None)
    parser.add_argument("--active-constraints-csv", type=Path, default=None)
    parser.add_argument("--output-prefix", type=Path, default=None)
    return parser.parse_args()


def robust_minmax(values: pd.Series, *, lower: float = 1.0, upper: float = 99.0, log1p: bool = False) -> tuple[pd.Series, dict[str, Any]]:
    numeric = pd.to_numeric(values, errors="coerce").astype(float)
    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    filled = numeric.fillna(0.0)
    transformed = np.log1p(np.clip(filled, a_min=0.0, a_max=None)) if log1p else filled
    lo = float(np.nanpercentile(transformed, lower))
    hi = float(np.nanpercentile(transformed, upper))
    if not np.isfinite(lo):
        lo = 0.0
    if not np.isfinite(hi) or hi <= lo:
        hi = lo + 1.0
    clipped = np.clip(transformed, lo, hi)
    norm = (clipped - lo) / (hi - lo)
    meta = {
        "lower_percentile": lower,
        "upper_percentile": upper,
        "clip_low": lo,
        "clip_high": hi,
        "log1p": log1p,
        "missing_filled_with": 0.0,
    }
    return pd.Series(norm, index=values.index), meta


def read_active_frequency(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["gaussian_id", "active_events", "active_trials"])
    columns = ["gaussian_id", "active_event_count", "active_trial_count"]
    freq = pd.read_csv(path, usecols=lambda c: c in columns)
    freq["gaussian_id"] = pd.to_numeric(freq["gaussian_id"], errors="coerce")
    freq = freq.dropna(subset=["gaussian_id"]).copy()
    freq["gaussian_id"] = freq["gaussian_id"].astype(np.int64)
    return freq.rename(
        columns={
            "active_event_count": "active_events",
            "active_trial_count": "active_trials",
        }
    )


def active_constraints_stats(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["gaussian_id", "logged_min_h", "logged_mean_h", "logged_mean_distance_to_robot"])
    usecols = ["gaussian_id", "h_value", "distance_to_robot", "heading_alignment_proxy"]
    active = pd.read_csv(path, usecols=lambda c: c in usecols)
    active["gaussian_id"] = pd.to_numeric(active["gaussian_id"], errors="coerce")
    active = active.dropna(subset=["gaussian_id"]).copy()
    if active.empty:
        return pd.DataFrame(columns=["gaussian_id", "logged_min_h", "logged_mean_h", "logged_mean_distance_to_robot"])
    active["gaussian_id"] = active["gaussian_id"].astype(np.int64)
    for col in ["h_value", "distance_to_robot", "heading_alignment_proxy"]:
        if col in active.columns:
            active[col] = pd.to_numeric(active[col], errors="coerce")
    return (
        active.groupby("gaussian_id")
        .agg(
            logged_min_h=("h_value", "min"),
            logged_mean_h=("h_value", "mean"),
            logged_mean_distance_to_robot=("distance_to_robot", "mean"),
            logged_mean_heading_alignment=("heading_alignment_proxy", "mean"),
        )
        .reset_index()
    )


def write_plot(table: pd.DataFrame, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "risk_v0_active_frequency",
        "risk_v1_geometry",
        "risk_v2_hybrid",
        "active_frequency_norm",
        "opacity_norm",
        "max_scale_norm",
        "anisotropy_norm",
    ]
    fig, axes = plt.subplots(2, 4, figsize=(15, 7))
    axes_flat = axes.ravel()
    for ax, col in zip(axes_flat, cols):
        ax.hist(pd.to_numeric(table[col], errors="coerce").fillna(0.0), bins=80)
        ax.set_title(col)
        ax.set_xlabel("score")
        ax.set_ylabel("count")
    axes_flat[-1].axis("off")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)

    output_prefix = resolve_repo_path(args.output_prefix) if args.output_prefix else RESULTS / args.scene
    attr_path = resolve_repo_path(args.attributes_csv) if args.attributes_csv else prefixed_path(output_prefix, "_gaussian_attributes.csv")
    freq_path = (
        resolve_repo_path(args.active_frequency_csv)
        if args.active_frequency_csv
        else RESULTS / f"{args.scene}_active_gaussian_frequency.csv"
    )
    if args.active_constraints_csv:
        active_path = resolve_repo_path(args.active_constraints_csv)
    elif args.scene == "stonehenge":
        active_path = ACTIVE_PATH
    else:
        active_path = RESULTS / f"baseline_detailed_logging_{args.scene}_100" / "active_constraints.csv"

    out_table = prefixed_path(output_prefix, "_risk_score_table_v0.csv")
    out_summary = prefixed_path(output_prefix, "_risk_score_summary_v0.csv")
    out_fig = FIGURES / f"{args.scene}_risk_score_distribution_v0.png"
    out_meta = prefixed_path(output_prefix, "_risk_score_metadata_v0.json")

    attrs = pd.read_csv(attr_path)
    attrs["gaussian_id"] = pd.to_numeric(attrs["gaussian_id"], errors="coerce")
    attrs = attrs.dropna(subset=["gaussian_id"]).copy()
    attrs["gaussian_id"] = attrs["gaussian_id"].astype(np.int64)

    active_frequency_available = freq_path.exists()
    active_constraints_available = active_path.exists()
    freq = read_active_frequency(freq_path)
    active_stats = active_constraints_stats(active_path)

    table = attrs.merge(freq, on="gaussian_id", how="left")
    table = table.merge(active_stats, on="gaussian_id", how="left")
    if "active_events" not in table.columns:
        table["active_events"] = 0
    if "active_trials" not in table.columns:
        table["active_trials"] = 0
    table["active_events"] = pd.to_numeric(table["active_events"], errors="coerce").fillna(0).astype(np.int64)
    table["active_trials"] = pd.to_numeric(table["active_trials"], errors="coerce").fillna(0).astype(np.int64)

    norm_meta: dict[str, Any] = {}
    table["active_frequency_norm"], norm_meta["active_frequency_norm"] = robust_minmax(table["active_events"], log1p=True)
    table["opacity_norm"], norm_meta["opacity_norm"] = robust_minmax(table["opacity"])
    table["max_scale_norm"], norm_meta["max_scale_norm"] = robust_minmax(table["max_scale"], log1p=True)
    table["anisotropy_norm"], norm_meta["anisotropy_norm"] = robust_minmax(table["anisotropy"], log1p=True)
    table["volume_proxy_norm"], norm_meta["volume_proxy_norm"] = robust_minmax(table["volume_proxy"], log1p=True)

    table["risk_v0_active_frequency"] = table["active_frequency_norm"]
    table["risk_v1_geometry"] = (
        0.34 * table["opacity_norm"]
        + 0.33 * table["anisotropy_norm"]
        + 0.33 * table["max_scale_norm"]
    )
    table["risk_v2_hybrid"] = (
        0.35 * table["active_frequency_norm"]
        + 0.20 * table["opacity_norm"]
        + 0.15 * table["anisotropy_norm"]
        + 0.15 * table["max_scale_norm"]
        + 0.15 * table["volume_proxy_norm"]
    )

    required_first = [
        "gaussian_id",
        "opacity",
        "max_scale",
        "anisotropy",
        "volume_proxy",
        "distance_to_scene_center",
        "active_events",
        "active_trials",
        "active_frequency_norm",
        "opacity_norm",
        "max_scale_norm",
        "anisotropy_norm",
        "risk_v0_active_frequency",
        "risk_v1_geometry",
        "risk_v2_hybrid",
    ]
    extra_cols = [c for c in table.columns if c not in required_first]
    table = table[required_first + extra_cols]
    table.to_csv(out_table, index=False)

    summary_rows = []
    for col in [
        "active_events",
        "active_frequency_norm",
        "opacity_norm",
        "max_scale_norm",
        "anisotropy_norm",
        "risk_v0_active_frequency",
        "risk_v1_geometry",
        "risk_v2_hybrid",
    ]:
        values = pd.to_numeric(table[col], errors="coerce")
        summary_rows.append(
            {
                "metric": col,
                "count": int(values.count()),
                "mean": float(values.mean()),
                "median": float(values.median()),
                "p95": float(values.quantile(0.95)),
                "max": float(values.max()),
            }
        )
    summary_rows.append(
        {
            "metric": "normalization_method",
            "count": len(table),
            "mean": "",
            "median": "",
            "p95": "",
            "max": "robust min-max with 1/99 percentile clipping; active frequency uses log1p",
        }
    )
    pd.DataFrame(summary_rows).to_csv(out_summary, index=False)
    write_plot(table, out_fig)
    out_meta.write_text(
        json.dumps(
            {
                "scene": args.scene,
                "inputs": {
                    "attributes": str(attr_path),
                    "active_frequency": str(freq_path),
                    "active_constraints": str(active_path),
                },
                "outputs": {
                    "table": str(out_table),
                    "summary": str(out_summary),
                    "figure": str(out_fig),
                },
                "normalization": norm_meta,
                "active_frequency_available": active_frequency_available,
                "active_constraints_available": active_constraints_available,
                "missing_active_frequency": "filled with zero" if not active_frequency_available else "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "scene": args.scene,
                "table": str(out_table),
                "summary": str(out_summary),
                "figure": str(out_fig),
                "active_frequency_available": active_frequency_available,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
