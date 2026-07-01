# Risk-Aware CBF Preparation

This directory contains independent experimental analysis and preparation code for risk-aware CBF on top of the reproduced SAFER-Splat baseline.

It must not modify the official SAFER-Splat implementation.

Current goal:

1. Analyze why the baseline SAFER-Splat CBF filter is safe but conservative.
2. Extract Gaussian-level and trajectory-interaction features.
3. Design a risk-aware constraint selection strategy.
4. Decide whether to implement a risk-aware CBF wrapper in the next stage.

Allowed scope:

- read official checkpoints and reproduced baseline outputs;
- write scripts, notes, figures, and CSVs under `work/risk_aware_cbf/`;
- optionally reference read-only files under `reproduction/`.

Forbidden scope:

- modifying `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, or `run.py`;
- changing the official baseline results;
- implementing a final risk-aware controller in this preparation phase.
