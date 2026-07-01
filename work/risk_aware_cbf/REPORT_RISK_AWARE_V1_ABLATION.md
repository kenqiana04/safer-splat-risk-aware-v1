# Risk-Aware V1 Ablation Report

## Scope

This report evaluates V1 pre-CBF candidate-budgeting ablations on stonehenge 20-trial.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF theorem.

## Baseline Reference

SAFER-Splat baseline is reused from the existing V1 20-trial comparison to avoid rerunning an identical baseline per ablation config.

| source | rows | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20/summary.csv | 20 | 0 | 0.00033367102150805295 | 0.5711932642733182 | 466.03282741675037 | 0.059708194848023845 | 0.06894749828148632 | 0 |

## Ablation Table

| ablation_id | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean | selection_tag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_budget1000_near008_hybrid | 0 | 0.0003336716036 | 0.5711988556 | 294.7022154 | 0.03699288534 | 0.04064978197 | 0 | 0 | 10154.78341 |  |
| B_budget2000_near008_hybrid | 0 | 0.0003336731752 | 0.5712284434 | 296.3107912 | 0.03689062217 | 0.04080505588 | 0 | 0 | 10215.54632 | safest_config |
| C_budget5000_near008_hybrid | 0 | 0.0003336713125 | 0.5712086136 | 302.2785365 | 0.03734037826 | 0.04119884397 | 0 | 0 | 10385.44763 |  |
| D_budget2000_near005_hybrid | 0 | 0.0003336715454 | 0.5711407858 | 176.0924922 | 0.03478140152 | 0.03878582338 | 0 | 0 | 9443.668215 | fastest_config,lowest_constraint_config,best_balanced_config |
| E_budget2000_near012_hybrid | 0 | 0.0003336709633 | 0.5711932212 | 424.4587414 | 0.03956282292 | 0.04396540828 | 0 | 0 | 12495.28113 |  |
| F_budget2000_near008_activefreq | 0 | 0.0003336731752 | 0.5712284434 | 296.309818 | 0.03547658211 | 0.03924707359 | 0 | 0 | 10215.54632 |  |
| G_budget2000_near008_geometry | 0 | 0.0003336731752 | 0.5712284434 | 296.3172389 | 0.03635794634 | 0.04017464232 | 0 | 0 | 10215.54632 |  |

## Main Observations

1. candidate_budget effect: see grouped analysis in `RISK_AWARE_V1_ABLATION_ANALYSIS.md`; fastest config is D_budget2000_near005_hybrid.
2. near_distance_threshold effect: higher thresholds tend to force more candidates; check runtime and candidate count together.
3. risk_score effect: compare activefreq / geometry / hybrid rows at budget 2000 and near 0.08.
4. better-than-default candidate: best_balanced_config = D_budget2000_near005_hybrid.
5. a 100-trial rerun is justified only for a balanced config that remains safe and meaningfully faster than baseline.

## Recommended Next Step

PROCEED_TO_100_WITH_BEST_CONFIG: D_budget2000_near005_hybrid satisfies the safe/runtime/progress/fallback criteria and should be validated at 100-trial scale.

## Claim Boundary

The reported `min_safety_h` is not meter clearance.
This is a wrapper-level prototype and does not prove a new CBF theorem.
Only stonehenge 20-trial ablation is evaluated here.
