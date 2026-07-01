#!/usr/bin/env python
"""No-filter vs SAFER-Splat CBF-QP offline comparison.

This reproduction script does not edit core SAFER-Splat code. It reuses the
existing offline smoke adapter and calls the official CBF/QP/distance path for
`safer_splat_filter`; `no_filter` applies the same nominal controller directly.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from dynamics.systems import DoubleIntegrator, double_integrator_dynamics  # noqa: E402
from run_offline_safety_filter_smoke import (  # noqa: E402
    InstrumentedCBF,
    START_GOAL_JSON,
    SNAPSHOT,
    SnapshotGSplatAdapter,
    percentile,
)

OUT_DIR = ROOT / "reproduction" / "results" / "offline_filter_comparison"
FIELDS = [
    "method",
    "trial",
    "success",
    "collision",
    "minimum_clearance",
    "path_length",
    "num_steps",
    "runtime_mean",
    "runtime_p95",
    "intervention_rate",
    "control_deviation_mean",
    "control_deviation_max",
    "active_constraints_mean",
    "active_constraints_p95",
    "qp_infeasible_count",
    "wall_time_s",
    "gaussian_pool_size",
    "max_active_before_cbf_pruning",
]


def load_start_goal(trial_index: int = 53):
    data = json.loads(START_GOAL_JSON.read_text())
    trial = data["total_data"][trial_index]
    start = torch.tensor(trial["start"], dtype=torch.float32)
    goal = torch.tensor(trial["goal"], dtype=torch.float32)
    source = f"{START_GOAL_JSON}:trial{trial_index} start/goal only"
    return start, goal, source


def nominal_control(x: torch.Tensor, goal: torch.Tensor) -> torch.Tensor:
    vel_des = 3.0 * (goal[:3] - x[:3]) + 0.8 * (goal[3:] - x[3:])
    vel_des = torch.clamp(vel_des, -0.12, 0.12)
    u_des = torch.clamp(1.2 * (vel_des - x[3:]), -0.12, 0.12)
    return u_des


def run_rollout(method: str, trial_index: int = 53, n_steps: int = 220, dt: float = 0.05,
                radius: float = 0.02, max_pool: int = 2500, max_active: int = 96) -> Dict[str, object]:
    if method not in {"no_filter", "safer_splat_filter"}:
        raise ValueError(f"unknown method {method}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    start3, goal3, source = load_start_goal(trial_index)
    x = torch.cat([start3, torch.zeros(3)]).to(device)
    goal = torch.cat([goal3, torch.zeros(3)]).to(device)
    gsplat = SnapshotGSplatAdapter(SNAPSHOT, device, start3, goal3, max_pool=max_pool, max_active=max_active)
    dynamics = DoubleIntegrator(device=device, ndim=3)
    cbf = None
    if method == "safer_splat_filter":
        cbf = InstrumentedCBF(gsplat, dynamics, alpha=5.0, beta=1.0, radius=radius, distance_type="ball-to-ellipsoid")

    traj_rows: List[Dict[str, object]] = []
    controls = []
    controls_des = []
    filter_times = []
    signed_clearances = []
    qp_infeasible_count = 0
    collided = False
    success = False
    t0 = time.perf_counter()

    for step in range(n_steps + 1):
        clearance = gsplat.min_signed_clearance(x.detach(), radius=radius)
        signed_clearances.append(clearance)
        traj_rows.append({
            "method": method,
            "trial": trial_index,
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

        u_des = nominal_control(x, goal)
        if method == "safer_splat_filter":
            assert cbf is not None
            tf0 = time.perf_counter()
            u = cbf.solve_QP(x, u_des)
            filter_times.append(time.perf_counter() - tf0)
            if not cbf.solver_success:
                qp_infeasible_count += 1
                break
        else:
            u = u_des
            filter_times.append(0.0)

        controls.append(u.detach().cpu().numpy())
        controls_des.append(u_des.detach().cpu().numpy())
        x = x + double_integrator_dynamics(x, u) * dt

    wall_time = time.perf_counter() - t0
    controls_arr = np.asarray(controls, dtype=float) if controls else np.zeros((0, 3))
    controls_des_arr = np.asarray(controls_des, dtype=float) if controls_des else np.zeros((0, 3))
    deviations = np.linalg.norm(controls_arr - controls_des_arr, axis=1) if len(controls_arr) else np.asarray([])
    path = np.asarray([[float(r["x"]), float(r["y"]), float(r["z"])] for r in traj_rows], dtype=float)
    path_length = float(np.sum(np.linalg.norm(np.diff(path, axis=0), axis=1))) if len(path) > 1 else 0.0
    active_constraints = cbf.active_constraints if cbf is not None else []

    if method == "no_filter":
        intervention_rate = 0.0
        control_deviation_mean = 0.0
        control_deviation_max = 0.0
        active_constraints_mean = 0.0
        active_constraints_p95 = 0.0
    else:
        intervention_rate = float(np.mean(deviations > 1e-4)) if len(deviations) else None
        control_deviation_mean = float(np.mean(deviations)) if len(deviations) else None
        control_deviation_max = float(np.max(deviations)) if len(deviations) else None
        active_constraints_mean = float(np.mean(active_constraints)) if active_constraints else None
        active_constraints_p95 = percentile(active_constraints, 95)

    metrics = {
        "method": method,
        "trial": trial_index,
        "success": bool(success),
        "collision": bool(collided),
        "minimum_clearance": float(min(signed_clearances)) if signed_clearances else None,
        "path_length": path_length,
        "num_steps": int(len(traj_rows) - 1),
        "runtime_mean": float(np.mean(filter_times)) if filter_times else 0.0,
        "runtime_p95": percentile(filter_times, 95) if filter_times else 0.0,
        "intervention_rate": intervention_rate,
        "control_deviation_mean": control_deviation_mean,
        "control_deviation_max": control_deviation_max,
        "active_constraints_mean": active_constraints_mean,
        "active_constraints_p95": active_constraints_p95,
        "qp_infeasible_count": int(qp_infeasible_count),
        "wall_time_s": wall_time,
        "gaussian_snapshot": str(SNAPSHOT),
        "gaussian_pool_size": int(gsplat.pool_size),
        "max_active_before_cbf_pruning": int(gsplat.max_active),
        "start_goal_source": source,
        "distance_note": "same real GSplat ellipsoid clearance evaluator for no_filter and safer_splat_filter",
    }
    return {"metrics": metrics, "trajectory": traj_rows, "goal": goal3.tolist(), "start": start3.tolist()}


def write_trajectory(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, metric_rows: Iterable[Dict[str, object]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in metric_rows:
            writer.writerow({k: row.get(k) for k in FIELDS})


def plot_comparison(path: Path, results: Dict[str, Dict[str, object]]) -> None:
    fig = plt.figure(figsize=(12, 5), dpi=160)
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    axc = fig.add_subplot(1, 2, 2)
    colors = {"no_filter": "#d62728", "safer_splat_filter": "#1f77b4"}
    for method, result in results.items():
        traj = result["trajectory"]
        xyz = np.asarray([[r["x"], r["y"], r["z"]] for r in traj], dtype=float)
        t = np.asarray([r["time_s"] for r in traj], dtype=float)
        c = np.asarray([r["signed_clearance_m"] for r in traj], dtype=float)
        ax3d.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], color=colors[method], linewidth=2, label=method)
        axc.plot(t, c, color=colors[method], linewidth=2, label=method)
    start = results["no_filter"]["start"]
    goal = results["no_filter"]["goal"]
    ax3d.scatter(start[0], start[1], start[2], color="#2ca02c", s=55, label="start")
    ax3d.scatter(goal[0], goal[1], goal[2], color="#111111", marker="*", s=80, label="goal")
    ax3d.set_title("trajectory")
    ax3d.set_xlabel("x")
    ax3d.set_ylabel("y")
    ax3d.set_zlabel("z")
    ax3d.legend(fontsize=8)
    axc.axhline(0.0, color="#111111", linewidth=1, linestyle="--")
    axc.set_title("signed clearance over time")
    axc.set_xlabel("time [s]")
    axc.set_ylabel("clearance [m]")
    axc.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def run_comparison(trial_index: int, out_dir: Path = OUT_DIR) -> Dict[str, Dict[str, object]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {
        "no_filter": run_rollout("no_filter", trial_index=trial_index),
        "safer_splat_filter": run_rollout("safer_splat_filter", trial_index=trial_index),
    }
    write_trajectory(out_dir / "no_filter_trajectory.csv", results["no_filter"]["trajectory"])
    write_trajectory(out_dir / "safer_splat_filter_trajectory.csv", results["safer_splat_filter"]["trajectory"])
    metric_rows = [results["no_filter"]["metrics"], results["safer_splat_filter"]["metrics"]]
    write_summary(out_dir / "comparison_summary.csv", metric_rows)
    with (out_dir / "comparison_metrics.json").open("w") as f:
        json.dump({k: v["metrics"] for k, v in results.items()}, f, indent=2)
    plot_comparison(out_dir / "comparison_plot.png", results)
    log = ["offline no-filter vs SAFER-Splat comparison", f"trial={trial_index}"]
    for row in metric_rows:
        log.append(json.dumps(row, sort_keys=True))
    (out_dir / "run_log.txt").write_text("\n".join(log) + "\n")
    return results


def main() -> None:
    torch.manual_seed(0)
    results = run_comparison(trial_index=53)
    print(json.dumps({k: v["metrics"] for k, v in results.items()}, indent=2))


if __name__ == "__main__":
    main()
