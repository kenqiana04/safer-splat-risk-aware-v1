# Risk-Aware V1 Analysis

Generated: 2026-06-30T17:04:03

## Summary Table

| dataset | scene | method | rows | collision_count | collision_free_count | min_safety_h_min | min_safety_h_mean | goal_distance_reduction_ratio_mean | intervention_rate_mean | control_deviation_mean_mean | active_constraints_mean_mean | runtime_mean_mean | runtime_p95_mean | qp_infeasible_count_sum | fallback_used_rate | candidate_count_final_mean | candidate_count_final_min | candidate_count_final_p95 | candidate_count_final_max | v1_insertion_level | source_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_smoke3 | stonehenge | no_filter | 3 | 3 | 0 | -0.0002270187251 | -0.0002258824 | 0.9913371756 | 0 | 0 | 0 | 1.845290025e-05 | 2.016955987e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_smoke3 |
| v1_smoke3 | stonehenge | risk_aware_v1_pre_cbf | 3 | 0 | 3 | 0.0008069268661 | 0.0009905818151 | 0.4018284973 | 0.9581264058 | 0.05253257815 | 255.2240508 | 0.03497561287 | 0.03830439753 | 0 | 0 | 10315.26703 | 3614 | 20146.3 | 24337 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_smoke3 |
| v1_smoke3 | stonehenge | safer_splat_filter | 3 | 0 | 3 | 0.0008069269825 | 0.0009905836002 | 0.4018082982 | 0.9591520468 | 0.05253575513 | 416.4105893 | 0.05770104615 | 0.06662259223 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_smoke3 |
| v1_20 | stonehenge | no_filter | 20 | 20 | 0 | -0.0002317183244 | -0.0002260564281 | 0.9917401775 | 0 | 0 | 0 | 1.951412285e-05 | 2.42393231e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20 |
| v1_20 | stonehenge | risk_aware_v1_pre_cbf | 20 | 0 | 20 | 0.0003336731752 | 0.000763409608 | 0.5712284434 | 0.9090094445 | 0.05932401445 | 296.3107912 | 0.03665814935 | 0.04024592503 | 0 | 0 | 10215.54632 | 2000 | 17746 | 25421 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20 |
| v1_20 | stonehenge | safer_splat_filter | 20 | 0 | 20 | 0.0003336710215 | 0.0007631153654 | 0.5711932643 | 0.9114099913 | 0.05933765727 | 466.0328274 | 0.05970819485 | 0.06894749828 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_20 |
| v1_100 | stonehenge | no_filter | 100 | 99 | 1 | -0.000236183696 | -0.0002136282125 | 0.9915018247 | 0 | 0 | 0 | 1.96243231e-05 | 2.51446031e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v1_100 | stonehenge | risk_aware_v1_pre_cbf | 100 | 0 | 100 | 0.0003172539582 | 0.0008605107386 | 0.3246946944 | 0.9203294458 | 0.06905307731 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 | 2000 | 20437.2 | 25421 | partial_pre_cbf | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v1_100 | stonehenge | safer_splat_filter | 100 | 0 | 100 | 0.0003172545403 | 0.0008604969102 | 0.3246967511 | 0.9254504193 | 0.06909715478 | 505.5866495 | 0.06214337873 | 0.07051209185 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100 |
| v0_100 | stonehenge | no_filter | 100 | 99 | 1 | -0.000236183696 | -0.0002136282125 | 0.9915018247 | 0 | 0 | 0 | 1.920392498e-05 | 2.43140813e-05 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_stonehenge_100 |
| v0_100 | stonehenge | risk_aware_topk_v0 | 100 | 0 | 100 | 0.0003172536672 | 0.000860599968 | 0.3247081815 | 0.923859098 | 0.06907969636 | 295.7127763 | 0.06135442953 | 0.06913961265 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_stonehenge_100 |
| v0_100 | stonehenge | safer_splat_filter | 100 | 0 | 100 | 0.0003172545403 | 0.0008604969102 | 0.3246967511 | 0.9254504193 | 0.06909715478 | 505.5866495 | 0.06125752391 | 0.06958187261 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_stonehenge_100 |
| baseline_detailed_100 | stonehenge | safer_splat_filter | 100 | 0 | 100 | 0.0003172545403 | 0.0008604969102 | 0.3246967511 | 0.9254504193 | 0.06909715478 | 505.5866495 | 0.0624509125 | 0.0714089942 | 0 |  |  |  |  |  |  | work/risk_aware_cbf/results/baseline_detailed_logging_stonehenge_100 |
| v0_ablation_20 | stonehenge | A_topk150_h0006_hybrid | 20 | 0 | 20 | 0.0003336715454 | 0.000764515574 | 0.5711912209 | 0.9072577612 | 0.05931671025 | 156.8141809 | 0.06016848411 | 0.06904628172 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |
| v0_ablation_20 | stonehenge | B_topk300_h0006_hybrid | 20 | 0 | 20 | 0.0003336710215 | 0.0007631242042 | 0.5711940388 | 0.9110555508 | 0.05933771614 | 289.5627946 | 0.06063681191 | 0.0695648435 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |
| v0_ablation_20 | stonehenge | C_topk500_h0006_hybrid | 20 | 0 | 20 | 0.0003336713708 | 0.0007631149783 | 0.5711932858 | 0.9112865345 | 0.05933767454 | 397.3462027 | 0.06029937587 | 0.06927199523 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |
| v0_ablation_20 | stonehenge | D_topk300_h0004_hybrid | 20 | 0 | 20 | 0.0003336710215 | 0.0007631242042 | 0.5711940388 | 0.9110555508 | 0.05933771614 | 289.5627946 | 0.06016792865 | 0.06887905675 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |
| v0_ablation_20 | stonehenge | E_topk300_h0010_hybrid | 20 | 0 | 20 | 0.0003336710215 | 0.0007631242042 | 0.5711940388 | 0.9110555508 | 0.05933771614 | 289.5627946 | 0.06018535587 | 0.06877633891 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |
| v0_ablation_20 | stonehenge | F_topk300_h0006_activefreq | 20 | 0 | 20 | 0.0003336713125 | 0.0007631136803 | 0.5711932778 | 0.9111630777 | 0.05933766065 | 289.5629313 | 0.05996628616 | 0.06892201172 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |
| v0_ablation_20 | stonehenge | G_topk300_h0006_geometry | 20 | 0 | 20 | 0.0003336713708 | 0.000764396679 | 0.5711655451 | 0.9084561164 | 0.0593150186 | 289.5305694 | 0.06076030855 | 0.06931113525 | 0 | 0 |  |  |  |  |  | work/risk_aware_cbf/results/risk_aware_topk_ablation_stonehenge_20 |

## Questions

1. Collision-free: yes.
2. Positive `min_safety_h`: yes; value = 0.0003336731751915.
3. QP infeasible: no; count = 0.
4. Candidate count reduction: V1 candidate_count_final_mean = 10215.546316851665.
5. Active constraints: V1 = 296.31079123650454; baseline = 466.0328274167504.
6. Runtime: V1 = 0.0366581493465829; baseline = 0.0597081948480238.
7. Progress: V1 = 0.5712284434302061; baseline = 0.5711932642733182.
8. Fallback used rate: 0.0.
9. V1/V0 distinction: V1 uses a loader-level subset before distance query; V0 trims constraints after baseline CBF construction.

## Decision

PROCEED_TO_100: V1 preserved safety and reduced mean step runtime against the 20-trial SAFER-Splat baseline.

Figure: `work/risk_aware_cbf/figures/risk_aware_v1_comparison_plots.png`
