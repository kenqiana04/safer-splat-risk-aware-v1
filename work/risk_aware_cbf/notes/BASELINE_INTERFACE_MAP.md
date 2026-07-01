# Baseline Interface Map

This map identifies safe and risky insertion points for a future risk-aware CBF wrapper. It is based on read-only inspection of the official SAFER-Splat code and the reproduction wrapper.

The raw keyword search is saved at:

```text
work/risk_aware_cbf/notes/interface_keyword_search.txt
```

| Functionality | SAFER-Splat file | function/class | inputs | outputs | how baseline uses it | possible risk-aware insertion point | risk level |
|---|---|---|---|---|---|---|---|
| Official checkpoint loading | `splat/gsplat_utils.py`, `run.py` | `GSplatLoader(Path(...), device)` | Nerfstudio config path, device | loader with means, scales, rotations, opacity, colors | Loads official Gaussian splat checkpoint before rollout | Read-only feature extraction or wrapper-side cache | Low |
| Gaussian mean extraction | `splat/gsplat_utils.py` | `GSplatLoader.means` | loaded checkpoint | tensor `[N, 3]` | Used inside distance query | Read-only geometry feature, proximity ranking | Low |
| Gaussian scale extraction | `splat/gsplat_utils.py` | `GSplatLoader.scales` | loaded checkpoint | tensor `[N, 3]` | Used to build ellipsoids and distance constraints | Risk score geometry term, adaptive candidate ranking | Low |
| Gaussian rotation extraction | `splat/gsplat_utils.py` | `GSplatLoader.rots` | loaded checkpoint | quaternion tensor | Used to rotate points into ellipsoid frame | Risk score anisotropy/orientation feature | Low |
| Opacity extraction | `splat/gsplat_utils.py` | `GSplatLoader.opacities` | loaded checkpoint | opacity tensor | Not directly used by CBF in current code | Confidence/risk cue for ranking only | Low |
| GSplat distance query | `splat/gsplat_utils.py` | `GSplatLoader.query_distance` | state/point, robot radius, distance type | `h`, gradient, Hessian, info | Computes safety values and CBF derivatives against all Gaussians | Logging, near-critical forced-include mask before ranking | Medium |
| CBF matrix construction | `cbf/cbf_utils.py` | `CBF.get_QP_matrices` | state, desired control, minimal flag | QP matrices `A`, `l`, `P`, `q` | Builds one CBF constraint set and prunes it | Future wrapper could rank candidate constraints before final QP | High |
| CBF solve wrapper | `cbf/cbf_utils.py` | `CBF.solve_QP` | state, desired control | filtered control | Calls matrix builder and Clarabel solver | Wrapper can instrument or compare before/after controls | Medium |
| QP solver | `cbf/cbf_utils.py` | `optimize_QP_clarabel` | `A`, `l`, `P`, `q` | solution, success flag | Solves CBF-QP | Avoid changing first; only log solver status/runtime | High |
| Pruning | `ellipsoids/polytopes_utils.py`, `cbf/cbf_utils.py` | `h_rep_minimal` | half-space constraints, feasible point | reduced `A`, `l` | Reduces collision-free constraints before QP | Candidate ranking could be compared against this pruning stage | High |
| Ellipsoid distance primitive | `splat/distances.py` | `distance_point_ellipsoid` | ellipsoid scales, local point | distance, Hessian, closest point | Core geometric distance solver | Do not modify; use only for read-only analysis | High |
| Dynamics | `dynamics/systems.py` | `DoubleIntegrator`, `double_integrator_dynamics` | state, acceleration | state derivative/system matrices | Rollout and CBF derivative model | Do not modify; keep evaluation aligned | Medium |
| Nominal PD controller | `run.py`, `reproduction/scripts/run_official_checkpoint_filter_comparison.py` | inline `nominal_control` | state, goal | desired acceleration | Produces capped command before filtering | Future baseline sensitivity can vary it separately, not in risk-aware CBF stage | Medium |
| Rollout loop | `run.py`, reproduction wrapper | rollout loop | start, goal, method, max steps | trajectory metrics | Evaluates no-filter and filter behavior | Safe wrapper-level place to compare risk-aware method | Low |
| Safety/collision evaluator | `GSplatLoader.query_distance`, reproduction wrapper | `min_safety_h < 0` | rollout state, checkpoint | collision flag, min safety value | Classifies collision by official safety value | Keep identical across methods | Low |
| Progress metrics | reproduction wrapper | `final_goal_distance`, `closest_goal_distance`, progress ratio | trajectory row data | progress summary | Reports safety-progress trade-off | Use unchanged for risk-aware comparison | Low |

## Recommended Safe Insertion Hierarchy

1. Risk-aware logging only.
2. Risk-aware candidate ranking before CBF.
3. Risk-aware top-k active constraint selection with hard safety fallback.
4. Adaptive inflation / margin.
5. QP slack / penalty changes.
6. Direct CBF formula modification.

The first implementation should avoid direct CBF formula modification.

The safest next implementation target is an independent wrapper under `work/risk_aware_cbf/` that logs and ranks candidate constraints while preserving hard near-critical fallback rules.
