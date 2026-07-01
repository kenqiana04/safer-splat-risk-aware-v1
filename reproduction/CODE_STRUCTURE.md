# SAFER-Splat Code Structure Mapping

| SAFER-Splat paper concept | code file | function/class | notes | verified? |
| --- | --- | --- | --- | --- |
| GSplat map loading | splat/gsplat_utils.py | GSplatLoader.load_gsplat_from_nerfstudio, load_gsplat_from_json | Official loader supports Nerfstudio config and JSON. Full import currently blocked by missing open3d/nerfstudio in minimal env; smoke uses reproduction adapter with real tensor snapshot. | partially |
| Gaussian mean / scale / rotation / covariance extraction | splat/gsplat_utils.py; ellipsoids/covariance_utils.py | GSplatLoader attributes; compute_cov; quaternion_to_rotation_matrix | Means/rots/scales/covs extracted in official loader. Smoke directly loads real tensor snapshot and calls official covariance utilities. | yes |
| sphere-to-ellipsoid distance | splat/distances.py; splat/gsplat_utils.py | distance_point_ellipsoid; GSplatLoader.query_distance | Official ball-to-ellipsoid squared distance used by smoke adapter. | yes |
| signed clearance / barrier h(x) | splat/gsplat_utils.py | GSplatLoader.query_distance | h = phi * squared_distance - radius^2. Smoke also reports signed Euclidean clearance for metrics. | yes |
| barrier gradient or derivative | cbf/cbf_utils.py | CBF.get_QP_matrices | Computes lfh, lflfh, lglfh for relative-degree-2 CBF constraints. | yes |
| Gaussian pruning / active constraint selection | cbf/cbf_utils.py; ellipsoids/polytopes_utils.py | h_rep_minimal; find_interior | Official minimal halfspace pruning is called by CBF. Smoke additionally caps nearest active candidates before CBF for tractability and reports active constraints. | yes |
| QP safety filter | cbf/cbf_utils.py | CBF.solve_QP; optimize_QP_clarabel | Clarabel QP solves minimally invasive control correction. | yes |
| nominal controller / desired action input | run.py; reproduction/scripts/run_offline_safety_filter_smoke.py | PD controller in rollout loop | Official run.py uses simple PD desired acceleration. Smoke mirrors this style. | yes |
| dynamics model | dynamics/systems.py | DoubleIntegrator; double_integrator_dynamics | 3D double integrator state [position, velocity], acceleration input. | yes |
| rollout / simulation loop | run.py; reproduction/scripts/run_offline_safety_filter_smoke.py | for-loop over time steps | Official run.py loops over circular configurations. Smoke runs one short start-goal rollout. | yes |
| metrics / plotting | run.py; visualize.py; reproduction/scripts/run_offline_safety_filter_smoke.py | JSON trajectory save; viser visualization; smoke metrics/plot outputs | Official code saves trajectory JSON and visualizes with viser. Smoke adds CSV/JSON/PNG metrics. | yes |

## Notes

- `reproduction/notes/core_keyword_search.txt` contains the keyword search output.
- `reproduction/logs/optional_loader_imports.log` records why the full loader was not used in the minimal offline smoke path.
- No core algorithm source file was edited for this checkpoint.
