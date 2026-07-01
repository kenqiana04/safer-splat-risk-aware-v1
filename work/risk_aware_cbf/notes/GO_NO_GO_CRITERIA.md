# Go / No-Go Criteria

## GO Conditions

GO if:

1. Gaussian or trajectory-interaction features show interpretable relationship with low progress / high intervention / active constraints.
2. There is a plausible hard safety fallback that avoids weakening near-critical constraints.
3. A wrapper-level top-k ranking can be implemented without modifying official baseline code.
4. Expected evaluation metrics are available: collision, min_safety_h, progress, intervention, runtime, active constraints, QP infeasible.

## NO-GO Conditions

NO-GO if:

1. Gaussian attributes show no useful relationship with conservatism.
2. Only progress-aware controller tuning explains the behavior.
3. Risk-aware selection requires unsafe deletion of near-critical constraints.
4. The result would be indistinguishable from arbitrary top-k pruning.

## If NO-GO

If the risk-aware direction is not supported, turn toward:

1. progress-aware CBF scheduling;
2. adaptive nominal controller;
3. CBF parameter sensitivity study;
4. constraint budget vs safety-progress trade-off.

## Current Decision Template

Use `GO`, `WEAK GO`, or `NO-GO`.

`WEAK GO` is appropriate when the baseline trade-off is strong and a safe wrapper insertion point exists, but feature evidence is incomplete or only partly interpretable.

## Post-Logging Decision

Decision:

```text
GO
```

Evidence from the baseline detailed logging run:

1. Logging coverage is sufficient for a first wrapper implementation decision: 100 `stonehenge` `safer_splat_filter` trials, 14,988 per-step trajectory rows, and 749,400 bounded active-constraint rows.
2. Active Gaussian IDs are available through the diagnostic wrapper's `HalfspaceIntersection.dual_vertices` mapping, so Gaussian-level frequency and attribute analysis is no longer blocked.
3. High intervention is associated with weaker stepwise progress: `corr_control_deviation_vs_goal_progress_delta = -0.5748204172791247`.
4. Lower safety h is associated with stronger intervention: `corr_control_deviation_vs_min_safety_h_step = -0.34471966598880743`. This is an association in the logged baseline, not a meter-clearance claim.
5. Constraint count has a measurable runtime relationship: `corr_active_constraints_count_vs_runtime_step = 0.4084494834512958`.
6. The most frequent active Gaussians are concentrated near the trajectory region and have identifiable attributes, enabling a future risk score to be evaluated against actual active constraints rather than only static scene statistics.

GO means the next task may implement a separate risk-aware wrapper under `work/risk_aware_cbf/`, with a hard safety fallback that always preserves near-critical constraints. It does not justify modifying official SAFER-Splat baseline code, changing `run.py`, or replacing the official CBF formula.

WEAK GO would apply if the future implementation cannot preserve near-critical constraints or cannot compare against the original baseline with the same metrics.

NO-GO still applies if risk-aware ranking reduces safety, increases QP infeasibility, or cannot outperform arbitrary top-k pruning under the same official checkpoint evaluation.
