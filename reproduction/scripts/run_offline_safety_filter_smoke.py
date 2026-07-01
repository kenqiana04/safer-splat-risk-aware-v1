#!/usr/bin/env python
"""Offline SAFER-Splat safety-filter smoke test.

This is a reproduction harness, not a core algorithm change. It uses a real
GSplat tensor snapshot from the local Splat-Nav flight reproduction as geometry
input and calls SAFER-Splat's official CBF, distance, covariance, dynamics, and
Clarabel QP code. The adapter below mirrors the ball-to-ellipsoid query in
`splat/gsplat_utils.py` because importing GSplatLoader requires Nerfstudio and
open3d, which are not needed for this offline smoke checkpoint.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cbf.cbf_utils import CBF  # noqa: E402
from dynamics.systems import DoubleIntegrator, double_integrator_dynamics  # noqa: E402
from ellipsoids.covariance_utils import quaternion_to_rotation_matrix, compute_cov  # noqa: E402
from splat.distances import distance_point_ellipsoid  # noqa: E402

SNAPSHOT = Path("/disk1/zlab/projects/splatnav/reproduction/flight_gsplat_tensors.pt")
START_GOAL_JSON = Path("/disk1/zlab/projects/splatnav/trajs/flight_splatplan_official100.json")
OUT_DIR = ROOT / "reproduction" / "results" / "offline_smoke"


class SnapshotGSplatAdapter:
    """Small GSplat query adapter around a real tensor snapshot.

    The math in `query_distance` is the same ball-to-ellipsoid path as
    `splat/gsplat_utils.py::GSplatLoader.query_distance`, but dependency-heavy
    Nerfstudio loading is bypassed for this offline smoke run.
    """

    def __init__(self, snapshot: Path, device: torch.device, start: torch.Tensor, goal: torch.Tensor,
                 crop_margin: float = 0.09, max_pool: int = 2500, max_active: int = 96) -> None:
        obj = torch.load(snapshot, map_location="cpu")
        means = obj["means"].float()
        rots = obj["rots"].float()
        scales = obj["scales"].float().clamp_min(1e-8)
        finite = torch.isfinite(means).all(dim=1) & torch.isfinite(rots).all(dim=1) & torch.isfinite(scales).all(dim=1)
        means, rots, scales = means[finite], rots[finite], scales[finite]

        lo = torch.minimum(start[:3].cpu(), goal[:3].cpu()) - crop_margin
        hi = torch.maximum(start[:3].cpu(), goal[:3].cpu()) + crop_margin
        bbox = ((means >= lo) & (means <= hi)).all(dim=1)
        idx = torch.nonzero(bbox, as_tuple=False).flatten()
        if idx.numel() < min(max_pool, 128):
            center = (start[:3].cpu() + goal[:3].cpu()) / 2.0
            dist2 = torch.sum((means - center) ** 2, dim=1)
            idx = torch.topk(dist2, k=min(max_pool, len(dist2)), largest=False).indices
        elif idx.numel() > max_pool:
            center = (start[:3].cpu() + goal[:3].cpu()) / 2.0
            local_dist2 = torch.sum((means[idx] - center) ** 2, dim=1)
            idx = idx[torch.topk(local_dist2, k=max_pool, largest=False).indices]

        self.device = device
        self.means = means[idx].to(device)
        self.rots = rots[idx].to(device)
        self.scales = scales[idx].to(device)
        self.covs = compute_cov(self.rots, self.scales)
        self.covs_inv = compute_cov(self.rots, 1.0 / self.scales)
        self.max_active = min(max_active, self.means.shape[0])
        self.last_active_count = 0
        self.pool_size = int(self.means.shape[0])
        self.snapshot = str(snapshot)

    def _active_subset(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        pos = x[..., :3].reshape(-1, 3)[0]
        dist2 = torch.sum((self.means - pos) ** 2, dim=1)
        k = min(self.max_active, dist2.numel())
        active = torch.topk(dist2, k=k, largest=False).indices
        self.last_active_count = int(k)
        return self.means[active], self.rots[active], self.scales[active]

    def query_distance(self, x: torch.Tensor, distance_type: str | None = None, radius: float = 0.0,
                       R_robot=None, S_robot=None, epsilon: float = 0.0):
        if distance_type not in (None, "ball-to-ellipsoid"):
            raise ValueError("offline smoke adapter only implements ball-to-ellipsoid")
        if x.dim() == 1:
            x = x.unsqueeze(0)
        means, rots_q, scales = self._active_subset(x)
        rots = quaternion_to_rotation_matrix(rots_q)
        sorted_scales, sorted_inds = torch.sort(scales, dim=-1, descending=True)
        rots = torch.gather(rots, 2, sorted_inds[..., None, :].expand_as(rots))
        x_local_frame = torch.bmm(torch.transpose(rots, 1, 2), (x[..., :3] - means).unsqueeze(-1)).squeeze() + 1e-8
        flip = torch.sign(x_local_frame)
        x_local_frame = torch.abs(x_local_frame)
        squared_dist, _, hess, yhat = distance_point_ellipsoid(sorted_scales + 1e-8, x_local_frame)
        y = torch.bmm(rots, (flip * yhat).unsqueeze(-1)).squeeze(-1) + means
        phi = torch.sign(torch.sum((1.0 / sorted_scales) ** 2 * (x_local_frame ** 2), dim=-1) - 1.0)
        h = phi * squared_dist - (radius + epsilon) ** 2
        grad_h = 2.0 * phi[..., None] * (x[..., :3] - y)
        hess_h = phi[..., None, None] * hess
        signed_clearance = phi * torch.sqrt(torch.clamp(squared_dist, min=0.0)) - (radius + epsilon)
        info = {"y": y, "phi": phi, "signed_clearance": signed_clearance}
        return h, grad_h, hess_h, info

    def min_signed_clearance(self, x: torch.Tensor, radius: float) -> float:
        _, _, _, info = self.query_distance(x[:3], radius=radius, distance_type="ball-to-ellipsoid")
        return float(torch.min(info["signed_clearance"]).detach().cpu())


class InstrumentedCBF(CBF):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.active_constraints = []

    def get_QP_matrices(self, x, u_des, minimal=True):
        A, l, P, q = super().get_QP_matrices(x, u_des, minimal=minimal)
        self.active_constraints.append(int(A.shape[0]))
        return A, l, P, q


def load_start_goal() -> Tuple[torch.Tensor, torch.Tensor, str]:
    if START_GOAL_JSON.exists():
        data = json.loads(START_GOAL_JSON.read_text())
        trial = data["total_data"][53]
        start = torch.tensor(trial["start"], dtype=torch.float32)
        goal = torch.tensor(trial["goal"], dtype=torch.float32)
        return start, goal, f"{START_GOAL_JSON}:trial53 start/goal only"
    start = torch.tensor([-0.0758, -0.0550, 0.0257], dtype=torch.float32)
    goal = torch.tensor([0.4558, -0.0550, -0.0257], dtype=torch.float32)
    return start, goal, "hard-coded fallback from prior flight config"


def percentile(values, p: float):
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), p))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    radius = 0.02
    dt = 0.05
    n_steps = 220
    alpha = 5.0
    beta = 1.0
    start3, goal3, start_goal_source = load_start_goal()
    x = torch.cat([start3, torch.zeros(3)]).to(device)
    goal = torch.cat([goal3, torch.zeros(3)]).to(device)

    gsplat = SnapshotGSplatAdapter(SNAPSHOT, device, start3, goal3, max_pool=2500, max_active=96)
    dynamics = DoubleIntegrator(device=device, ndim=3)
    cbf = InstrumentedCBF(gsplat, dynamics, alpha, beta, radius, distance_type="ball-to-ellipsoid")

    traj_rows = []
    controls = []
    controls_des = []
    signed_clearances = []
    qp_infeasible_count = 0
    collided = False
    success = False
    start_time = time.perf_counter()

    for step in range(n_steps + 1):
        clearance = gsplat.min_signed_clearance(x.detach(), radius=radius)
        signed_clearances.append(clearance)
        traj_rows.append({
            "step": step,
            "time_s": step * dt,
            "x": float(x[0].detach().cpu()),
            "y": float(x[1].detach().cpu()),
            "z": float(x[2].detach().cpu()),
            "vx": float(x[3].detach().cpu()),
            "vy": float(x[4].detach().cpu()),
            "vz": float(x[5].detach().cpu()),
            "signed_clearance_m": clearance,
            "active_pool_size": gsplat.last_active_count,
        })
        if clearance <= 0.0:
            collided = True
            break
        if torch.norm(x[:3] - goal[:3]).item() < 0.05 and torch.norm(x[3:]).item() < 0.08:
            success = True
            break
        if step == n_steps:
            break

        vel_des = 3.0 * (goal[:3] - x[:3]) + 0.8 * (goal[3:] - x[3:])
        vel_des = torch.clamp(vel_des, -0.12, 0.12)
        u_des = torch.clamp(1.2 * (vel_des - x[3:]), -0.12, 0.12)

        t_qp0 = time.perf_counter()
        u = cbf.solve_QP(x, u_des)
        _ = time.perf_counter() - t_qp0
        if not cbf.solver_success:
            qp_infeasible_count += 1
            break
        controls.append(u.detach().cpu().numpy())
        controls_des.append(u_des.detach().cpu().numpy())
        x = x + double_integrator_dynamics(x, u) * dt

    elapsed = time.perf_counter() - start_time
    controls_arr = np.asarray(controls, dtype=float) if controls else np.zeros((0, 3))
    controls_des_arr = np.asarray(controls_des, dtype=float) if controls_des else np.zeros((0, 3))
    deviations = np.linalg.norm(controls_arr - controls_des_arr, axis=1) if len(controls_arr) else np.asarray([])
    path = np.asarray([[r["x"], r["y"], r["z"]] for r in traj_rows], dtype=float)
    path_length = float(np.sum(np.linalg.norm(np.diff(path, axis=0), axis=1))) if len(path) > 1 else 0.0
    qp_times = cbf.times_qp
    runtime_total = float(sum(qp_times))
    metrics: Dict[str, object] = {
        "success": bool(success),
        "collision": bool(collided),
        "minimum_clearance": float(min(signed_clearances)) if signed_clearances else None,
        "path_length": path_length,
        "runtime_mean": float(np.mean(qp_times)) if qp_times else None,
        "runtime_p95": percentile(qp_times, 95),
        "runtime_total_qp_s": runtime_total,
        "wall_time_s": elapsed,
        "intervention_rate": float(np.mean(deviations > 1e-4)) if len(deviations) else None,
        "control_deviation_mean": float(np.mean(deviations)) if len(deviations) else None,
        "control_deviation_max": float(np.max(deviations)) if len(deviations) else None,
        "active_constraints_mean": float(np.mean(cbf.active_constraints)) if cbf.active_constraints else None,
        "active_constraints_p95": percentile(cbf.active_constraints, 95),
        "qp_infeasible_count": int(qp_infeasible_count),
        "num_steps": int(len(traj_rows) - 1),
        "gaussian_snapshot": str(SNAPSHOT),
        "gaussian_pool_size": int(gsplat.pool_size),
        "max_active_before_cbf_pruning": int(gsplat.max_active),
        "start_goal_source": start_goal_source,
        "distance_note": "signed clearance computed from official ball-to-ellipsoid squared-distance query; ellipsoid surfaces are real GSplat geometry from snapshot",
    }

    with (OUT_DIR / "metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)
    with (OUT_DIR / "trajectory.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(traj_rows[0].keys()))
        writer.writeheader()
        writer.writerows(traj_rows)
    with (OUT_DIR / "summary.csv").open("w", newline="") as f:
        fields = ["success", "collision", "minimum_clearance", "path_length", "runtime_mean", "runtime_p95", "intervention_rate", "control_deviation_mean", "control_deviation_max", "active_constraints_mean", "active_constraints_p95", "qp_infeasible_count", "num_steps"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow({k: metrics[k] for k in fields})

    fig = plt.figure(figsize=(8, 6), dpi=160)
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(path[:, 0], path[:, 1], path[:, 2], color="#1f77b4", linewidth=2, label="filtered trajectory")
    ax.scatter(path[0, 0], path[0, 1], path[0, 2], color="#2ca02c", s=60, label="start")
    ax.scatter(float(goal3[0]), float(goal3[1]), float(goal3[2]), color="#111111", marker="*", s=80, label="goal")
    ax.set_title("SAFER-Splat offline smoke trajectory")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.legend(fontsize=8)
    text = "\n".join([
        f"success={metrics['success']}",
        f"collision={metrics['collision']}",
        f"min clearance={metrics['minimum_clearance']:.6g} m",
        f"steps={metrics['num_steps']}",
        f"pool={metrics['gaussian_pool_size']}, active<={metrics['max_active_before_cbf_pruning']}",
    ])
    ax.text2D(0.02, 0.02, text, transform=ax.transAxes, fontsize=8, bbox={"facecolor": "white", "alpha": 0.8})
    fig.tight_layout()
    fig.savefig(OUT_DIR / "trajectory_plot.png")
    plt.close(fig)

    log_lines = [f"{k}: {v}" for k, v in metrics.items()]
    (OUT_DIR / "run_log.txt").write_text("\n".join(log_lines) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

