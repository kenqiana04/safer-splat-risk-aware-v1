# Per-Step Conservatism Analysis

## Scope

This analysis uses baseline detailed logging outputs only. It does not implement a risk-aware CBF controller and does not modify the official SAFER-Splat baseline.

## Inputs

- Input directory: `work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100`
- `min_safety_h_step` is the official GSplat safety h value, not a meter clearance.
- Active constraints are logged as the lowest-h selected baseline constraints up to the configured per-step limit.

## Logging Coverage

- trial_rows: 100
- per_step_rows: 14988
- active_constraint_rows: 749400
- methods: safer_splat_filter
- trial_min: 0
- trial_max: 99
- unique_trials: 100
- active_gaussian_ids_available: yes

## Per-Step Findings

- control_deviation_mean: 0.05428364145976845
- control_deviation_p95: 0.10920556113123892
- control_deviation_max: 0.1272549033164978
- active_constraints_count_mean: 477.1283693621564
- active_constraints_count_p95: 913.6499999999996
- active_constraints_count_max: 1524
- runtime_step_mean_s: 0.0608856976091909
- runtime_step_p95_s: 0.07201514476910227
- min_safety_h_step_min: 0.0003172545402776
- min_safety_h_step_mean: 0.0022751637146298364
- corr_control_deviation_vs_goal_progress_delta: -0.5748204172791247
- corr_control_deviation_vs_min_safety_h_step: -0.34471966598880743
- corr_active_constraints_count_vs_runtime_step: 0.4084494834512958
- corr_active_constraints_count_vs_control_deviation: -0.09493917592169067
- high_intervention_threshold_p95: 0.10920556113123892
- high_intervention_rows: 750
- high_intervention_goal_progress_delta_mean: 0.0007896448572476705
- high_intervention_min_safety_h_step_mean: 0.0010676928239020356
- Max intervention step: trial 92, step 194, control_deviation 0.127255, min_safety_h_step 0.000346905.

## Active Gaussian Findings

- Unique active Gaussian IDs: 35081
- Top active Gaussian IDs by logged event count:
  - gaussian_id 25806: events 639, trials 22, h_min 0.0024335
  - gaussian_id 36521: events 572, trials 19, h_min 0.000752533
  - gaussian_id 26971: events 568, trials 19, h_min 0.00074133
  - gaussian_id 18540: events 529, trials 20, h_min 0.000790393
  - gaussian_id 41785: events 515, trials 20, h_min 0.000725586
  - gaussian_id 46645: events 515, trials 20, h_min 0.00170888
  - gaussian_id 72266: events 485, trials 17, h_min 0.000420345
  - gaussian_id 83485: events 470, trials 17, h_min 0.00077231
  - gaussian_id 32490: events 467, trials 19, h_min 0.00072666
  - gaussian_id 30014: events 464, trials 19, h_min 0.000874833

- Attribute summary is available in `active_gaussian_attribute_summary.csv`; it compares full-scene Gaussians with active logged Gaussians.

## Output Files

- `work/risk_aware_cbf/results/per_step_conservatism_summary.csv`
- `work/risk_aware_cbf/results/high_intervention_steps.csv`
- `work/risk_aware_cbf/results/active_gaussian_frequency.csv`
- `work/risk_aware_cbf/results/active_gaussian_attribute_summary.csv`
- `work/risk_aware_cbf/figures/per_step_conservatism_plots.png`

## Limitations

- The active constraint log is a bounded diagnostic sample of selected constraints, not a full dense dump of every selected Gaussian at every step.
- The results support baseline diagnosis and GO/NO-GO planning, but they are not a new method result.
