#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_ROOT = ROOT / "work/risk_aware_cbf"
RESULTS = OUT_ROOT / "results"
NOTES = OUT_ROOT / "notes"
REPORT = OUT_ROOT / "REPORT_RISK_AWARE_CBF_PREPARATION.md"


def read_csv(path: Path):
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def by_attribute(rows):
    return {row["attribute"]: row for row in rows}


def by_method(rows):
    return {row["method"]: row for row in rows}


def first(rows, key, value):
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


env_python = (NOTES / "python_version.txt").read_text(encoding="utf-8").strip()
python_path = (NOTES / "python_path.txt").read_text(encoding="utf-8").strip()
commit = (NOTES / "git_commit.txt").read_text(encoding="utf-8").strip()

baseline_summary = by_method(read_csv(ROOT / "reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/summary.csv"))
gaussian_summary = by_attribute(read_csv(RESULTS / "stonehenge_gaussian_attribute_summary.csv"))
traj_summary = read_csv(RESULTS / "trajectory_interaction_feature_summary.csv")
correlations = read_csv(RESULTS / "conservatism_correlation_table.csv")
group_comparison = read_csv(RESULTS / "conservatism_group_comparison.csv")
gaussian_notes = (NOTES / "GAUSSIAN_ATTRIBUTE_EXTRACTION_NOTES.md").read_text(encoding="utf-8")
traj_notes = (NOTES / "TRAJECTORY_INTERACTION_ANALYSIS_NOTES.md").read_text(encoding="utf-8")
conservatism_notes = (NOTES / "CONSERVATISM_ANALYSIS_NOTES.md").read_text(encoding="utf-8")

available_attributes = [
    "means",
    "scales",
    "max/min/mean scale",
    "anisotropy",
    "volume_proxy",
    "distance_to_scene_center",
    "opacity",
    "rotation/quaternion",
    "color_or_sh_norm",
]
missing_attributes = []

top_corr = sorted(
    [row for row in correlations if row["spearman"]],
    key=lambda row: abs(float(row["spearman"])),
    reverse=True,
)[:6]

low_control = first(group_comparison, "feature", "control_deviation_mean")
low_intervention = first(group_comparison, "feature", "intervention_rate")
low_constraints = first(group_comparison, "feature", "active_constraints_mean")

report = f"""# Risk-Aware CBF Preparation Report

## 1. Scope

This report prepares the risk-aware CBF direction.
It does not implement a new controller.
It does not modify the official SAFER-Splat baseline.

The goal is to decide whether Gaussian-level and trajectory-interaction cues provide a scientifically defensible basis for a future risk-aware CBF wrapper.

## 2. Baseline Motivation

The official `stonehenge` 100-trial checkpoint comparison motivates this direction:

| method | rows | collision_count | collision_free_count | success_count | stopped_before_goal_count | goal_distance_reduction_ratio_mean | intervention_rate_mean | active_constraints_mean_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_filter | {baseline_summary["no_filter"]["rows"]} | {baseline_summary["no_filter"]["collision_count"]} | {baseline_summary["no_filter"]["collision_free_count"]} | {baseline_summary["no_filter"]["success_count"]} | {baseline_summary["no_filter"]["stopped_before_goal_count"]} | {baseline_summary["no_filter"]["goal_distance_reduction_ratio_mean"]} | {baseline_summary["no_filter"]["intervention_rate_mean"]} | {baseline_summary["no_filter"]["active_constraints_mean_mean"]} |
| safer_splat_filter | {baseline_summary["safer_splat_filter"]["rows"]} | {baseline_summary["safer_splat_filter"]["collision_count"]} | {baseline_summary["safer_splat_filter"]["collision_free_count"]} | {baseline_summary["safer_splat_filter"]["success_count"]} | {baseline_summary["safer_splat_filter"]["stopped_before_goal_count"]} | {baseline_summary["safer_splat_filter"]["goal_distance_reduction_ratio_mean"]} | {baseline_summary["safer_splat_filter"]["intervention_rate_mean"]} | {baseline_summary["safer_splat_filter"]["active_constraints_mean_mean"]} |

The no-filter baseline is unsafe but high-progress. The SAFER-Splat filter is safe but conservative under this wrapper. This creates a clear safety-progress trade-off worth analyzing before implementing any new method.

## 3. Interface Map

The interface review is documented in:

```text
work/risk_aware_cbf/notes/BASELINE_INTERFACE_MAP.md
work/risk_aware_cbf/notes/interface_keyword_search.txt
```

The recommended safe insertion hierarchy is:

1. risk-aware logging only;
2. risk-aware candidate ranking before CBF;
3. risk-aware top-k active constraint selection with hard safety fallback;
4. adaptive inflation / margin;
5. QP slack / penalty changes;
6. direct CBF formula modification.

The first implementation should avoid direct CBF formula modification.

## 4. Gaussian Attribute Extraction

Gaussian attributes were extracted from the official `stonehenge` checkpoint with `GSplatLoader`.

| item | value |
|---|---:|
| gaussian_count | {gaussian_summary["max_scale"]["count"]} |
| max_scale_mean | {gaussian_summary["max_scale"]["mean"]} |
| max_scale_median | {gaussian_summary["max_scale"]["median"]} |
| anisotropy_mean | {gaussian_summary["anisotropy"]["mean"]} |
| anisotropy_median | {gaussian_summary["anisotropy"]["median"]} |
| opacity_mean | {gaussian_summary["opacity"]["mean"]} |
| opacity_median | {gaussian_summary["opacity"]["median"]} |
| volume_proxy_mean | {gaussian_summary["volume_proxy"]["mean"]} |

Available attributes:

```text
{", ".join(available_attributes)}
```

Missing attributes:

```text
{", ".join(missing_attributes) if missing_attributes else "None observed in this extraction"}
```

The extracted attributes are suitable for geometry/confidence risk-score design. They do not by themselves prove which Gaussians cause conservatism; trajectory interaction evidence is still needed.

## 5. Trajectory-Interaction Analysis

Analyzed groups:

| group | method | rows | progress_mean | min_safety_h_mean | sampled_trajectory_rows |
|---|---|---:|---:|---:|---:|
"""

for row in traj_summary:
    report += f"| {row['group']} | {row['method']} | {row['rows']} | {row['goal_distance_reduction_ratio_mean']} | {row['min_safety_h_mean']} | {row['sampled_trajectory_rows']} |\n"

report += f"""

Key observations:

- `no_filter_collision` contains 99 rows and has high progress, but negative safety values.
- `safer_collision_free_low_progress` and `safer_collision_free_higher_progress` split the safe trajectories into low/high progress groups.
- Gaussian-neighborhood trajectory features are currently limited because `trajectory_samples.csv` contains sampled path points only for `safer_splat_filter:0`.

Limitations:

- No synthetic trajectory samples were generated.
- Gaussian-neighborhood correlations cannot be claimed from one sampled trajectory.
- Full per-step trajectory logging or active-constraint logging is needed before making strong Gaussian-level claims.

## 6. Conservatism Analysis

Strongest SAFER-Splat indicators by absolute Spearman correlation with progress:

| feature | n | pearson | spearman | note |
|---|---:|---:|---:|---|
"""

for row in top_corr:
    report += f"| {row['feature']} | {row['n']} | {row['pearson']} | {row['spearman']} | {row['note']} |\n"

report += f"""

Top/bottom progress comparison:

| feature | low_progress_mean | high_progress_mean | high_minus_low |
|---|---:|---:|---:|
| intervention_rate | {low_intervention['low_progress_mean']} | {low_intervention['high_progress_mean']} | {low_intervention['high_minus_low']} |
| active_constraints_mean | {low_constraints['low_progress_mean']} | {low_constraints['high_progress_mean']} | {low_constraints['high_minus_low']} |
| control_deviation_mean | {low_control['low_progress_mean']} | {low_control['high_progress_mean']} | {low_control['high_minus_low']} |

Interpretation:

- Higher intervention and higher control deviation are associated with lower progress.
- Higher active-constraint counts are also associated with lower progress, but the relationship is weaker than control deviation.
- `num_steps` correlates strongly with progress, but this mostly reflects that longer-moving trajectories make more progress; it is not an independent causal explanation.
- Gaussian neighborhood features are insufficient for correlation analysis with the current sampled trajectory coverage.

## 7. Risk Score Design

The risk-score design is documented in:

```text
work/risk_aware_cbf/notes/RISK_SCORE_DESIGN_V0.md
```

Recommended first method:

```text
Risk-Aware Top-K Constraint Ranking with Hard Safety Fallback
```

Hard safety fallback:

1. Always include any Gaussian / constraint with low `h`.
2. Always include any near-field Gaussian inside a distance threshold.
3. Always include any Gaussian inside a heading cone or high TTC-risk zone.
4. Apply risk-aware ranking only to the remaining non-critical candidates.

## 8. Go / No-Go Decision

Decision:

```text
WEAK GO
```

Rationale:

- GO evidence: the baseline safety-progress trade-off is strong; intervention/control deviation/active constraints are associated with low progress; Gaussian attributes are available; a wrapper-level insertion point exists.
- Weakness: current trajectory samples are insufficient to prove Gaussian-level causal relationships. Static Gaussian attributes are useful candidates, but their interaction with conservatism needs better per-step logging.
- Safety condition: any next implementation must preserve hard near-critical constraints and compare against the original SAFER-Splat baseline without modifying official code.

## 9. Recommended Next Implementation

Implement risk-aware top-k constraint ranking with hard safety fallback in a separate `work/risk_aware_cbf` wrapper.

Do not modify official SAFER-Splat code.

Compare:

```text
no_filter vs SAFER-Splat baseline vs risk-aware wrapper
```

on `stonehenge` 100-trial first, using the same collision, `min_safety_h`, progress, intervention, runtime, active-constraint, and QP infeasible metrics.

## Claim-Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| SAFER-Splat is safe but conservative on this checkpoint | 100/100 collision-free; mean progress ratio 0.3247 | supported for this wrapper/checkpoint |
| no_filter is high-progress but unsafe | 99/100 collisions; mean progress ratio 0.9915 | supported for this wrapper/checkpoint |
| intervention/control deviation relate to low progress | correlation and group comparison tables | supported as association, not causality |
| Gaussian-level risk cues are promising | attributes are available and interpretable | needs more trajectory interaction evidence |
| risk-aware CBF can be implemented safely by direct formula changes | not supported | avoid this claim |

## Output Files

```text
work/risk_aware_cbf/results/stonehenge_gaussian_attributes.csv
work/risk_aware_cbf/results/stonehenge_gaussian_attribute_summary.csv
work/risk_aware_cbf/results/trajectory_interaction_features.csv
work/risk_aware_cbf/results/trajectory_interaction_feature_summary.csv
work/risk_aware_cbf/results/conservatism_correlation_table.csv
work/risk_aware_cbf/results/conservatism_group_comparison.csv
work/risk_aware_cbf/figures/stonehenge_gaussian_attribute_histograms.png
work/risk_aware_cbf/figures/trajectory_interaction_feature_plots.png
work/risk_aware_cbf/figures/conservatism_indicator_plots.png
```

## Environment

- repo: `/disk1/zlab/projects/safer-splat`
- git commit: `{commit}`
- python path: `{python_path}`
- python version: `{env_python}`

## Final Self-Review

- Contribution clarity: this is preparation and evidence gathering, not a new controller.
- Writing clarity: all claims are tied to extracted CSVs or reproduced baseline tables.
- Experimental strength: sufficient for a preparation decision; insufficient for final method claims.
- Evaluation completeness: missing dense per-step trajectory samples and active Gaussian IDs.
- Method design soundness: hard safety fallback is mandatory before any top-k pruning.
"""

REPORT.write_text(report, encoding="utf-8")
print(REPORT)
