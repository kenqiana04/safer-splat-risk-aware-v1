# Risk-Aware Top-K V0 Analysis

## Scope

This analysis compares the wrapper-level `risk_aware_topk_v0` prototype against `no_filter` and the unchanged `safer_splat_filter` baseline.
It does not modify the official SAFER-Splat baseline and does not claim a new CBF theorem.

## Smoke3 Result

- risk-aware collision_count: 0.0
- risk-aware min_safety_h_min: 0.0008069268660619
- risk-aware qp_infeasible_count_sum: 0.0
- risk-aware active_constraints_mean: 277.718126405758

## 20-Trial Result

- safer_splat_filter collision_count: 0.0
- risk_aware_topk_v0 collision_count: 0.0
- safer_splat_filter min_safety_h_min: 0.000333671021508
- risk_aware_topk_v0 min_safety_h_min: 0.000333671021508
- safer_splat_filter progress mean: 0.5711932642733182
- risk_aware_topk_v0 progress mean: 0.5711940388034845
- safer_splat_filter active constraints mean: 466.0328274167504
- risk_aware_topk_v0 active constraints mean: 289.56279464390497
- risk_aware_topk_v0 fallback_used_rate: 0.0

## 100-Trial Result

- no_filter collision_count: 99.0
- safer_splat_filter collision_count: 0.0
- risk_aware_topk_v0 collision_count: 0.0
- safer_splat_filter min_safety_h_min: 0.0003172545402776
- risk_aware_topk_v0 min_safety_h_min: 0.0003172536671627
- safer_splat_filter progress mean: 0.324696751118169
- risk_aware_topk_v0 progress mean: 0.3247081815273468
- safer_splat_filter active constraints mean: 505.58664953518127
- risk_aware_topk_v0 active constraints mean: 295.71277631192885
- risk_aware_topk_v0 fallback_used_rate: 0.0

## Interpretation

The V0 wrapper stayed collision-free and had no QP infeasible cases in smoke3 and 20-trial tests.
It substantially reduced the selected constraint count, but did not materially improve progress or reduce intervention on the 20-trial set.
Runtime did not improve in this implementation because the wrapper is inserted after baseline distance querying and minimal-polytope construction.

## Next Steps

1. Run a 100-trial stability check only if the goal is to validate safety and constraint-count reduction.
2. Sweep `topk`, `h_critical`, and `risk_score` before claiming any progress benefit.
3. A cleaner future insertion point should reduce candidate work before minimal-polytope construction; that requires a separate wrapper API, not editing official core files.
