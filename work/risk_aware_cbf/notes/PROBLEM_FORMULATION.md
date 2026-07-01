# Problem Formulation

## 4.1 Motivation

The reproduced official `stonehenge` 100-trial checkpoint comparison shows a clear safety-progress trade-off.

`no_filter` reaches high progress but collides in 99/100 trials. Its mean goal-distance reduction ratio is approximately 0.9915, but its mean `min_safety_h` is negative.

`safer_splat_filter` avoids collision in 100/100 trials, with positive `min_safety_h` across the evaluated trials. However, it significantly reduces progress: the mean goal-distance reduction ratio is approximately 0.3247, and every trial stops before the strict goal condition.

This indicates that the official SAFER-Splat CBF filter is effective for safety on this checkpoint, but conservative under the current wrapper and nominal controller. That motivates risk-aware constraint handling as a possible way to preserve hard near-field safety while reducing unnecessary intervention.

## 4.2 Research Question

Can risk-aware constraint selection or adaptive constraint handling reduce unnecessary conservatism in 3DGS-CBF safety filtering while preserving collision-free behavior?

## 4.3 Current Hypothesis

Hypothesis H1:

Some of SAFER-Splat's conservatism comes from treating many Gaussian constraints uniformly, without considering their relative relevance, uncertainty, trajectory interaction, or contribution to near-term collision risk.

Hypothesis H2:

A risk-aware ranking or scheduling mechanism can reduce unnecessary active constraints and intervention while preserving hard near-field safety constraints.

## 4.4 What This Project Should Not Claim Yet

1. We do not yet claim a new CBF theorem.
2. We do not yet claim full safety guarantee beyond the baseline.
3. We do not yet claim meter-scale clearance unless separately computed.
4. We do not yet claim full SAFER-Splat paper reproduction.
