#!/usr/bin/env python
"""Sanity checks for SAFER-Splat distance and CBF-QP behavior."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cbf.cbf_utils import CBF  # noqa: E402
from dynamics.systems import DoubleIntegrator  # noqa: E402
from ellipsoids.covariance_utils import quaternion_to_rotation_matrix, compute_cov  # noqa: E402
from splat.distances import distance_point_ellipsoid  # noqa: E402

OUT = ROOT / "reproduction" / "results" / "offline_smoke"
OUT.mkdir(parents=True, exist_ok=True)


class SingleEllipsoidMap:
    def __init__(self, device: torch.device) -> None:
        self.device = device
        self.means = torch.tensor([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float32, device=device)
        self.rots = torch.tensor([[0.9238795, 0.3826834, 0.0, 0.0], [0.9238795, 0.3826834, 0.0, 0.0]], dtype=torch.float32, device=device)
        self.scales = torch.tensor([[0.10, 0.10, 0.10], [0.10, 0.10, 0.10]], dtype=torch.float32, device=device)
        self.covs = compute_cov(self.rots, self.scales)
        self.covs_inv = compute_cov(self.rots, 1.0 / self.scales)

    def query_distance(self, x, distance_type=None, radius=0.0, R_robot=None, S_robot=None, epsilon=0.0):
        if x.dim() == 1:
            x = x.unsqueeze(0)
        rots = quaternion_to_rotation_matrix(self.rots)
        sorted_scales, sorted_inds = torch.sort(self.scales, dim=-1, descending=True)
        rots = torch.gather(rots, 2, sorted_inds[..., None, :].expand_as(rots))
        x_local = torch.bmm(torch.transpose(rots, 1, 2), (x[..., :3] - self.means).unsqueeze(-1)).squeeze() + 1e-8
        flip = torch.sign(x_local)
        x_local_abs = torch.abs(x_local)
        squared_dist, _, hess, yhat = distance_point_ellipsoid(sorted_scales + 1e-8, x_local_abs)
        y = torch.bmm(rots, (flip * yhat).unsqueeze(-1)).squeeze(-1) + self.means
        phi = torch.sign(torch.sum((1.0 / sorted_scales) ** 2 * (x_local_abs ** 2), dim=-1) - 1.0)
        h = phi * squared_dist - (radius + epsilon) ** 2
        grad_h = 2.0 * phi[..., None] * (x[..., :3] - y)
        hess_h = phi[..., None, None] * hess
        signed_clearance = phi * torch.sqrt(torch.clamp(squared_dist, min=0.0)) - (radius + epsilon)
        return h, grad_h, hess_h, {"signed_clearance": signed_clearance}

    def clearance(self, point, radius=0.02):
        _, _, _, info = self.query_distance(torch.tensor(point, dtype=torch.float32, device=self.device), radius=radius, distance_type="ball-to-ellipsoid")
        return float(info["signed_clearance"].min().detach().cpu())


def assert_cond(name: str, cond: bool, details: str) -> dict:
    print(f"[{ 'PASS' if cond else 'FAIL' }] {name}: {details}")
    if not cond:
        raise AssertionError(f"{name}: {details}")
    return {"name": name, "passed": cond, "details": details}


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    m = SingleEllipsoidMap(device)
    radius = 0.02
    results = []
    unit = [1.0 / (3.0 ** 0.5)] * 3
    far_pt = [0.45 * u for u in unit]
    touching_pt = [0.12 * u for u in unit]
    inside_pt = [0.05 * u for u in unit]
    far = m.clearance(far_pt, radius)
    touching = m.clearance(touching_pt, radius)
    inside = m.clearance(inside_pt, radius)
    results.append(assert_cond("far_positive", far > 0.20, f"clearance={far}"))
    results.append(assert_cond("touching_near_zero", abs(touching) < 5e-4, f"clearance={touching}"))
    results.append(assert_cond("inside_negative", inside < -0.02, f"clearance={inside}"))

    dynamics = DoubleIntegrator(device=device, ndim=3)
    cbf = CBF(m, dynamics, alpha=5.0, beta=1.0, radius=radius, distance_type="ball-to-ellipsoid")
    diag_pos = [0.14 * u for u in unit]
    diag_vel_toward = [-0.05 * u for u in unit]
    diag_u_toward = [-0.10 * u for u in unit]
    x_toward = torch.tensor(diag_pos + diag_vel_toward, dtype=torch.float32, device=device)
    u_des_toward = torch.tensor(diag_u_toward, dtype=torch.float32, device=device)
    u_toward = cbf.solve_QP(x_toward, u_des_toward)
    toward_delta = float(torch.norm(u_toward - u_des_toward).detach().cpu())
    results.append(assert_cond("moving_toward_filter_modifies", cbf.solver_success and toward_delta > 1e-4, f"u_des={u_des_toward.detach().cpu().tolist()} u={u_toward.detach().cpu().tolist()} delta={toward_delta}"))

    diag_vel_away = [0.05 * u for u in unit]
    diag_u_away = [0.02 * u for u in unit]
    x_away = torch.tensor(diag_pos + diag_vel_away, dtype=torch.float32, device=device)
    u_des_away = torch.tensor(diag_u_away, dtype=torch.float32, device=device)
    u_away = cbf.solve_QP(x_away, u_des_away)
    away_delta = float(torch.norm(u_away - u_des_away).detach().cpu())
    results.append(assert_cond("moving_away_minimal_intervention", cbf.solver_success and away_delta < 1e-3, f"u_des={u_des_away.detach().cpu().tolist()} u={u_away.detach().cpu().tolist()} delta={away_delta}"))

    (OUT / "distance_cbf_sanity.json").write_text(json.dumps({"results": results}, indent=2))
    print("all sanity checks passed")


if __name__ == "__main__":
    main()




