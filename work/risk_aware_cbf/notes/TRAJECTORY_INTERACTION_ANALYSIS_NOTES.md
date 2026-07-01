# Trajectory Interaction Analysis Notes

```json
{
  "input_trials": "reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trials.csv",
  "input_trajectory_samples": "reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trajectory_samples.csv",
  "gaussian_attributes": "work/risk_aware_cbf/results/stonehenge_gaussian_attributes.csv",
  "sampled_trajectory_keys": [
    "safer_splat_filter:0"
  ],
  "limitation": "Gaussian-neighborhood trajectory features are computed only where trajectory_samples.csv provides sampled path points. Other rows retain trial-level metrics only.",
  "outputs": [
    "work/risk_aware_cbf/results/trajectory_interaction_features.csv",
    "work/risk_aware_cbf/results/trajectory_interaction_feature_summary.csv",
    "work/risk_aware_cbf/figures/trajectory_interaction_feature_plots.png"
  ]
}
```

No synthetic trajectory points were generated. Missing sampled trajectories are left without Gaussian-neighborhood features.
