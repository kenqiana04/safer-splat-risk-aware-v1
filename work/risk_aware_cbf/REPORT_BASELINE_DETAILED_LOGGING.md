# Baseline Detailed Logging Report

## Scope

This report covers the `stonehenge` SAFER-Splat baseline detailed logging task.
It uses the official checkpoint and the existing `safer_splat_filter` rollout configuration.
It does not implement a risk-aware CBF controller, does not modify the official SAFER-Splat baseline, and does not change `run.py`.

The logged safety value `min_safety_h` / `min_safety_h_step` is the official GSplat safety h value from the baseline distance query. It is not reported as meter clearance.

## Logging Coverage

| item | value |
|---|---:|
| logged scene | stonehenge |
| logged method | safer_splat_filter |
| trial rows | 100 |
| per-step rows | 14,988 |
| active-constraint rows | 749,400 |
| active Gaussian IDs available | yes |
| active constraint logging scope | lowest-h selected baseline constraints, capped at 50 rows per step |

Official 100-trial baseline summary from the detailed logging run:

| metric | value |
|---|---:|
| collision_count | 0 |
| collision_free_count | 100 |
| success_count | 0 |
| stopped_before_goal_count | 100 |
| min_safety_h_min | 0.000317254540277645 |
| min_safety_h_mean | 0.0008604969101725146 |
| goal_distance_reduction_ratio_mean | 0.324696751118169 |
| intervention_rate_mean | 0.9254504193236854 |
| control_deviation_mean_mean | 0.06909715477600109 |
| active_constraints_mean_mean | 505.58664953518127 |
| qp_infeasible_count_sum | 0 |

## Per-Step Findings

The per-step log supports the earlier observation that this baseline is safe but conservative in this wrapper.

| metric | value |
|---|---:|
| control_deviation_mean | 0.05428364145976845 |
| control_deviation_p95 | 0.10920556113123892 |
| control_deviation_max | 0.1272549033164978 |
| active_constraints_count_mean | 477.1283693621564 |
| active_constraints_count_p95 | 913.6499999999996 |
| active_constraints_count_max | 1524 |
| runtime_step_mean_s | 0.0608856976091909 |
| runtime_step_p95_s | 0.07201514476910227 |
| min_safety_h_step_min | 0.0003172545402776 |
| min_safety_h_step_mean | 0.0022751637146298364 |
| goal_progress_delta_mean | 0.0016987105376955777 |
| goal_progress_delta_min | -0.0015969498199411001 |

Associations measured on the logged per-step rows:

| relationship | correlation |
|---|---:|
| control_deviation vs goal_progress_delta | -0.5748204172791247 |
| control_deviation vs min_safety_h_step | -0.34471966598880743 |
| active_constraints_count vs runtime_step | 0.4084494834512958 |
| active_constraints_count vs control_deviation | -0.09493917592169067 |

The top logged intervention step was trial 92, step 194, with `control_deviation = 0.1272549033164978` and `min_safety_h_step = 0.0003469045332167`.

These numbers are evidence for a safety-progress trade-off and for stepwise conservatism. They are not causal proof that any single Gaussian causes the slowdown.

## Active Gaussian Findings

The diagnostic wrapper recovered global Gaussian IDs for active constraints through `HalfspaceIntersection.dual_vertices`. This makes Gaussian-level analysis possible without modifying the official `cbf/`, `splat/`, or `ellipsoids/` source directories.

Most frequent logged active Gaussians:

| gaussian_id | active events | active trials | min h |
|---:|---:|---:|---:|
| 25806 | 639 | 22 | 0.0024335028138011 |
| 36521 | 572 | 19 | 0.0007525332039222 |
| 26971 | 568 | 19 | 0.0007413298590108 |
| 18540 | 529 | 20 | 0.0007903926307335 |
| 41785 | 515 | 20 | 0.0007255856180563 |

Attribute comparison between full-scene Gaussians and active logged Gaussians:

| attribute | full-scene mean | active unique mean | active event weighted mean | top100 active mean |
|---|---:|---:|---:|---:|
| opacity | 0.6362844037819716 | 0.632329152105611 | 0.6325953056500523 | 0.7328838613629342 |
| max_scale | 0.026693237931033717 | 0.003026403957825356 | 0.0041459039426244345 | 0.003118749998975497 |
| mean_scale | 0.025328736238134412 | 0.001248412054523113 | 0.0016809004243417654 | 0.001347064206488622 |
| anisotropy | 25027.4422093587 | 57568.27643649723 | 73743.26641460301 | 10344.399963582917 |
| volume_proxy | 0.0010649254315496682 | 5.781277883595844e-10 | 2.6639684516480124e-09 | 1.888513336173125e-08 |
| distance_to_scene_center | 1.0634303903112161 | 0.5383584824694069 | 0.5128133558251161 | 0.4755565191404189 |

The logged active Gaussians differ from full-scene averages on scale, anisotropy, and scene-center distance, and their logged `distance_to_robot` values show that they are near the executed trajectory at active steps. This supports designing a future risk score, provided that near-critical constraints remain protected.

## Updated Decision

Decision:

```text
GO
```

The prior decision was `WEAK GO` because Gaussian-level interaction evidence was incomplete. The detailed logging run removes that specific blocker: active Gaussian IDs are available, per-step intervention/progress relationships are measurable, and active Gaussian attributes can be analyzed.

This is a GO only for the next separate-wrapper experiment under `work/risk_aware_cbf/`. It does not authorize changes to the official controller or baseline code.

## Recommended Next Task

Implement a separate risk-aware top-k constraint ranking wrapper under `work/risk_aware_cbf/` with a hard safety fallback:

1. Always keep near-critical low-h constraints.
2. Always keep near-field constraints.
3. Apply ranking only to non-critical candidate constraints.
4. Compare against the unchanged `safer_splat_filter` baseline with the same 100-trial checkpoint protocol.
5. Report collision, min safety h, progress, intervention, runtime, active constraints, and QP infeasibility.

## Output Files

```text
work/risk_aware_cbf/notes/BASELINE_LOGGING_SCHEMA.md
work/risk_aware_cbf/scripts/run_baseline_with_detailed_logging.py
work/risk_aware_cbf/scripts/analyze_per_step_conservatism.py
work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100/trials.csv
work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100/per_step_trajectory.csv
work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100/active_constraints.csv
work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100/summary.csv
work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100/metrics.json
work/risk_aware_cbf/results/per_step_conservatism_summary.csv
work/risk_aware_cbf/results/high_intervention_steps.csv
work/risk_aware_cbf/results/active_gaussian_frequency.csv
work/risk_aware_cbf/results/active_gaussian_attribute_summary.csv
work/risk_aware_cbf/figures/per_step_conservatism_plots.png
work/risk_aware_cbf/notes/PER_STEP_CONSERVATISM_ANALYSIS.md
work/risk_aware_cbf/notes/GO_NO_GO_CRITERIA.md
work/risk_aware_cbf/REPORT_BASELINE_DETAILED_LOGGING.md
```

## Environment

| item | value |
|---|---|
| repository | `/disk1/zlab/projects/safer-splat` |
| git commit | `adfeba258f34aa949011638b54243cfb595568d2` |
| conda environment | `/disk1/zlab/conda_envs/safer_splat_official` |
| python | `Python 3.10.20` |
| GPU selector | `CUDA_VISIBLE_DEVICES=1` |

## Self-Review

- Core-source modification: no intended modification to `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, or `run.py`.
- Method claim: this is baseline logging and analysis only, not a new controller.
- Safety claim: all 100 logged baseline trials are collision-free under the official h metric, but all stop before the goal.
- Evidence limit: active-constraint logging is bounded to the lowest-h selected constraints per step, not a full dump of every selected constraint.
