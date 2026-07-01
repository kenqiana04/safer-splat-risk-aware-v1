# Risk-Aware V1 Pre-CBF Feasibility Review

## Scope

This note reviews whether risk-aware candidate selection can be moved before CBF matrix construction without modifying official SAFER-Splat source files. The review is based on `work/risk_aware_cbf/notes/v1_keyword_search.txt` and direct inspection of:

- `splat/gsplat_utils.py`
- `cbf/cbf_utils.py`
- `ellipsoids/polytopes_utils.py`
- `work/risk_aware_cbf/scripts/run_baseline_with_detailed_logging.py`
- `work/risk_aware_cbf/scripts/run_risk_aware_topk_comparison.py`

## Findings

1. `GSplatLoader.query_distance` does not expose a native candidate selector. For `ball-to-ellipsoid`, it uses the current loader tensors `self.means`, `self.rots`, and `self.scales`, converts quaternions to rotation matrices, sorts scales per Gaussian, evaluates `distance_point_ellipsoid`, and returns one safety value and derivatives per Gaussian.

2. `CBF.get_QP_matrices` calls `self.gsplat.query_distance(...)` at the start of CBF matrix construction. The returned `h`, gradient, and Hessian are then transformed into CBF inequalities before the QP is solved.

3. Minimal-polytope construction occurs inside `CBF.get_QP_matrices` after the full CBF inequalities are built. The official code calls `h_rep_minimal` from `ellipsoids/polytopes_utils.py` on collisionless constraints, then appends collision constraints.

4. Official source does not provide an argument for subset Gaussian tensors. However, a reproduction-only wrapper can temporarily expose subset tensors to the official `GSplatLoader.query_distance` call, then restore the full tensors immediately after the query.

5. A `SubsetGSplatLoader` wrapper is feasible without editing official source. It can wrap the official loader, set a per-step subset of global Gaussian ids, temporarily swap `means`, `rots`, `scales`, `opacities`, `covs`, and `covs_inv`, delegate to official `query_distance`, and restore full tensors in a `finally` block.

6. Candidate subsets can be generated from robot position, nominal control direction, and the risk table already produced by V0. The available data are full Gaussian means, opacity/scale/risk columns in `work/risk_aware_cbf/results/risk_score_table_v0.csv`, current robot state, and nominal control.

7. Near-critical fallback must preserve at least these sets: near-field Gaussians around the robot, heading-cone Gaussians along nominal motion, locally relevant high-active-frequency Gaussians, and enough risk-ranked candidates to meet the candidate budget. If the subset is too small or metadata fails, the wrapper must fall back to the original full baseline query.

8. V1 can reduce distance-query, minimal-polytope, and QP construction work when the subset is active, because the official distance call sees fewer tensors before CBF inequalities are formed. It can also reduce final QP constraints indirectly. If fallback is used, it reduces none of those steps for that iteration.

9. The main safety risk is missing a Gaussian whose full-baseline CBF constraint would have been active or near-critical. That can yield negative `min_safety_h` or QP infeasibility. This is why smoke testing must stop before 20-trial if V1 collides, has non-positive minimum safety value, or has QP infeasible steps.

10. Full source-level pre-CBF selection is not possible without editing official `GSplatLoader` or `CBF`. Reproduction-only wrapper insertion is possible and is enough to prototype V1 behavior.

## Conclusion

`PARTIALLY_FEASIBLE`

Reason: V1 candidate selection can be moved before distance query and CBF matrix construction in an external wrapper, but official source has no first-class subset API. The implementation is therefore a reproduction-only partial pre-CBF wrapper, not a modification of the official SAFER-Splat baseline.
