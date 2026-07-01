# Risk-Aware V1 Ablation Analysis

Generated: 2026-06-30T18:11:47

## Baseline Reference

| source | rows | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20/summary.csv | 20 | 0 | 0.00033367102150805295 | 0.5711932642733182 | 466.03282741675037 | 0.059708194848023845 | 0.06894749828148632 | 0 |

## Ablation Table

| ablation_id | candidate_budget | near_distance_threshold | risk_score | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean | candidate_count_final_p95 | selection_tag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_budget1000_near008_hybrid | 1000 | 0.08 | risk_v2_hybrid | 20 | 0 | 20 | 0.0003336716036 | 0.0007634025416 | 0.5711988556 | 0.9073863079 | 0.05931234779 | 294.7022154 | 0.03699288534 | 0.04064978197 | 0 | 0 | 10154.78341 | 17693.2 |  |
| B_budget2000_near008_hybrid | 2000 | 0.08 | risk_v2_hybrid | 20 | 0 | 20 | 0.0003336731752 | 0.000763409608 | 0.5712284434 | 0.9090094445 | 0.05932401445 | 296.3107912 | 0.03689062217 | 0.04080505588 | 0 | 0 | 10215.54632 | 17746 | safest_config |
| C_budget5000_near008_hybrid | 5000 | 0.08 | risk_v2_hybrid | 20 | 0 | 20 | 0.0003336713125 | 0.0007634106674 | 0.5712086136 | 0.9091958198 | 0.05932952848 | 302.2785365 | 0.03734037826 | 0.04119884397 | 0 | 0 | 10385.44763 | 17884.1 |  |
| D_budget2000_near005_hybrid | 2000 | 0.05 | risk_v2_hybrid | 20 | 0 | 20 | 0.0003336715454 | 0.0007634574838 | 0.5711407858 | 0.9049045488 | 0.05930314239 | 176.0924922 | 0.03478140152 | 0.03878582338 | 0 | 0 | 9443.668215 | 17006.25 | fastest_config,lowest_constraint_config,best_balanced_config |
| E_budget2000_near012_hybrid | 2000 | 0.12 | risk_v2_hybrid | 20 | 0 | 20 | 0.0003336709633 | 0.000763113331 | 0.5711932212 | 0.9111354771 | 0.05933766929 | 424.4587414 | 0.03956282292 | 0.04396540828 | 0 | 0 | 12495.28113 | 19633.3 |  |
| F_budget2000_near008_activefreq | 2000 | 0.08 | risk_v0_active_frequency | 20 | 0 | 20 | 0.0003336731752 | 0.000763409608 | 0.5712284434 | 0.9090094445 | 0.05932401445 | 296.309818 | 0.03547658211 | 0.03924707359 | 0 | 0 | 10215.54632 | 17746 |  |
| G_budget2000_near008_geometry | 2000 | 0.08 | risk_v1_geometry | 20 | 0 | 20 | 0.0003336731752 | 0.000763409608 | 0.5712284434 | 0.9090094445 | 0.05932401445 | 296.3172389 | 0.03635794634 | 0.04017464232 | 0 | 0 | 10215.54632 | 17746 |  |

## Selected Configs

- safest_config: B_budget2000_near008_hybrid
- fastest_config: D_budget2000_near005_hybrid
- lowest_constraint_config: D_budget2000_near005_hybrid
- best_balanced_config: D_budget2000_near005_hybrid

## Observations

- configs with 0 collision and positive min_safety_h: 7 / 7

### Candidate Budget Effect

| candidate_budget | collision_count | min_safety_h_min | runtime_mean | active_constraints_mean | progress_mean | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- |
| 1000 | 0 | 0.0003336716036 | 0.03699288534 | 294.7022154 | 0.5711988556 | 10154.78341 |
| 2000 | 0 | 0.0003336709633 | 0.03661387501 | 297.8978163 | 0.5712038675 | 10517.11766 |
| 5000 | 0 | 0.0003336713125 | 0.03734037826 | 302.2785365 | 0.5712086136 | 10385.44763 |

### Near-Distance Threshold Effect

| near_distance_threshold | collision_count | min_safety_h_min | runtime_mean | active_constraints_mean | progress_mean | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0 | 0.0003336715454 | 0.03478140152 | 176.0924922 | 0.5711407858 | 9443.668215 |
| 0.08 | 0 | 0.0003336713125 | 0.03661168284 | 297.18372 | 0.5712185599 | 10237.374 |
| 0.12 | 0 | 0.0003336709633 | 0.03956282292 | 424.4587414 | 0.5711932212 | 12495.28113 |

### Risk Score Effect

| risk_score | collision_count | min_safety_h_min | runtime_mean | active_constraints_mean | progress_mean | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- |
| risk_v0_active_frequency | 0 | 0.0003336731752 | 0.03547658211 | 296.309818 | 0.5712284434 | 10215.54632 |
| risk_v1_geometry | 0 | 0.0003336731752 | 0.03635794634 | 296.3172389 | 0.5712284434 | 10215.54632 |
| risk_v2_hybrid | 0 | 0.0003336709633 | 0.03711362204 | 298.7685553 | 0.5711939839 | 10538.94534 |
