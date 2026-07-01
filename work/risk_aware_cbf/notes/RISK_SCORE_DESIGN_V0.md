# Risk Score Design V0

## 9.1 Design Principle

Risk-aware CBF should not simply weaken safety constraints.

The first version should use risk-aware constraint prioritization with hard safety fallback. This means risk ranking can decide which non-critical constraints receive computation budget, but it must not remove near-critical constraints that are likely to determine immediate safety.

## 9.2 Candidate Risk Scores

### risk_v1_geometry

Formula:

```text
risk_v1_geometry =
  normalize(max_scale) + normalize(volume_proxy) + normalize(anisotropy)
```

Required features:

- Gaussian scale vector;
- `max_scale`;
- `volume_proxy = scale_x * scale_y * scale_z`;
- `anisotropy = max_scale / max(min_scale, eps)`.

Intuition:

Large, volumetric, or highly anisotropic Gaussians can produce stronger or broader geometric constraints.

Expected effect:

Prioritize geometrically influential ellipsoids over very small or nearly irrelevant splats.

Failure mode:

Large Gaussians may be visually broad but not relevant to the current trajectory.

Whether it may weaken safety:

It can weaken safety if used without near-critical fallback. It should only rank non-critical candidates.

Implementation difficulty:

Low.

### risk_v2_confidence

Formula:

```text
risk_v2_confidence =
  normalize(opacity) + normalize(local_density) + normalize(active_frequency)
```

Required features:

- opacity;
- local Gaussian density;
- frequency with which a Gaussian or nearby region becomes active in baseline rollouts.

Intuition:

High-opacity or dense regions may represent stable surfaces or obstacles. Active-frequency can reveal repeatedly constraining geometry.

Expected effect:

Avoid spending constraint budget on low-confidence isolated splats unless they are near-critical.

Failure mode:

Low-opacity splats may still represent real obstacles; active-frequency requires trajectory history.

Whether it may weaken safety:

Yes, if confidence is used to drop near-field constraints. Use hard safety fallback.

Implementation difficulty:

Medium.

### risk_v3_interaction

Formula:

```text
risk_v3_interaction =
  normalize(trajectory_proximity) + normalize(heading_alignment) + normalize(TTC_proxy)
```

Required features:

- distance from Gaussian to current trajectory/state;
- relative heading alignment between robot velocity and Gaussian direction;
- time-to-contact proxy.

Intuition:

Risk should depend on how the robot interacts with geometry, not only on static Gaussian properties.

Expected effect:

Prioritize constraints that are near the current path or likely to become relevant soon.

Failure mode:

If heading/velocity is noisy near stopping points, interaction risk may be unstable.

Whether it may weaken safety:

Yes, if slow-moving near-critical obstacles are ignored. Use low-h and near-field fallback.

Implementation difficulty:

Medium to high.

### risk_v4_hybrid

Formula:

```text
risk_v4_hybrid =
  w_g * risk_geometry +
  w_c * risk_confidence +
  w_i * risk_interaction
```

Required features:

- geometry features;
- confidence/density features;
- interaction features.

Intuition:

Combines static geometry, reconstruction confidence, and trajectory interaction.

Expected effect:

More robust ranking than any single cue.

Failure mode:

Weights can become arbitrary if not validated with ablations.

Whether it may weaken safety:

The weighted score can weaken safety if used as a hard deletion rule. It should only order non-critical candidates.

Implementation difficulty:

Medium to high.

## 9.3 Hard Safety Fallback

Any Gaussian / constraint with low `h` value must always be included.

Any near-field Gaussian within a distance threshold must always be included.

Any Gaussian inside a heading cone or high TTC-risk zone must always be included.

Risk-aware ranking only affects the remaining candidate set.

Suggested first fallback rules:

```text
include if h <= h_critical_threshold
include if Euclidean distance to robot center <= near_field_radius
include if projected velocity toward Gaussian is positive and TTC_proxy <= ttc_threshold
```

## 9.4 Recommended First Method

Risk-Aware Top-K Constraint Ranking with Hard Safety Fallback.

Procedure:

1. Build baseline candidate constraints.
2. Force include all near-critical constraints.
3. Rank the remaining candidates by risk score.
4. Select top-k under runtime budget.
5. Solve the same CBF-QP as SAFER-Splat.
6. Compare with original SAFER-Splat under identical rollout and metrics.

The first implementation should not directly modify the CBF formula.
