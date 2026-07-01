#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from splat.gsplat_utils import GSplatLoader
from cbf.cbf_utils import CBF
from dynamics.systems import DoubleIntegrator, double_integrator_dynamics


SCENES: dict[str, dict[str, Any]] = {
    "old_union2": {
        "radius_z": 0.01,
        "radius": 0.01,
        "radius_config": 1.35 / 2,
        "mean_config": np.array([0.14, 0.23, -0.15]),
        "path_to_gsplat": Path("outputs/old_union2/splatfacto/2024-09-02_151414/config.yml"),
    },
    "stonehenge": {
        "radius_z": 0.01,
        "radius": 0.015,
        "radius_config": 0.784 / 2,
        "mean_config": np.array([-0.08, -0.03, 0.05]),
        "path_to_gsplat": Path("outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml"),
    },
    "statues": {
        "radius_z": 0.03,
        "radius": 0.03,
        "radius_config": 0.475,
        "mean_config": np.array([-0.064, -0.0064, -0.025]),
        "path_to_gsplat": Path("outputs/statues/splatfacto/2024-09-11_095852/config.yml"),
    },
    "flight": {
        "radius_z": 0.06,
        "radius": 0.03,
        "radius_config": 0.545 / 2,
        "mean_config": np.array([0.19, 0.01, -0.02]),
        "path_to_gsplat": Path("outputs/flight/splatfacto/2024-09-12_172434/config.yml"),
    },
}

METHODS = ("no_filter", "safer_splat_filter")
SAFETY_H_NOTE = "official GSplatLoader.query_distance safety h value; not meters"

TRIAL_FIELDS = [
    "scene",
    "method",
    "trial",
    "checkpoint",
    "gaussian_count",
    "success",
    "feasible",
    "collision",
    "min_safety_h",
    "min_safety_h_note",
    "path_length",
    "num_steps",
    "stop_reason",
    "runtime_mean",
    "runtime_p95",
    "intervention_rate",
    "control_deviation_mean",
    "control_deviation_max",
    "active_constraints_mean",
    "active_constraints_p95",
    "qp_infeasible_count",
    "seconds_total",
    "error",
    "start_x",
    "start_y",
    "start_z",
    "goal_x",
    "goal_y",
    "goal_z",
    "final_x",
    "final_y",
    "final_z",
    "initial_goal_distance",
    "final_goal_distance",
    "goal_distance_reduction",
    "goal_distance_reduction_ratio",
    "closest_goal_distance",
    "closest_goal_step",
    "reached_goal_tolerance",
    "goal_distance_final",
    "max_steps",
    "goal_tolerance",
    "success_definition",
    "radius",
    "dt",
    "distance_type",
]

SUMMARY_FIELDS = [
    "scene",
    "method",
    "rows",
    "total_rows",
    "success_count",
    "feasible_count",
    "collision_count",
    "collision_free_count",
    "error_count",
    "stopped_before_goal_count",
    "max_steps_loose_success_count",
    "solver_failed_count",
    "qp_infeasible_count_sum",
    "min_safety_h_min",
    "min_safety_h_mean",
    "min_safety_h_median",
    "initial_goal_distance_mean",
    "final_goal_distance_mean",
    "closest_goal_distance_mean",
    "goal_distance_reduction_mean",
    "goal_distance_reduction_ratio_mean",
    "reached_goal_tolerance_count",
    "path_length_mean",
    "num_steps_mean",
    "runtime_mean_mean",
    "runtime_p95_mean",
    "intervention_rate_mean",
    "control_deviation_mean_mean",
    "control_deviation_max_max",
    "active_constraints_mean_mean",
    "active_constraints_p95_mean",
    "seconds_total_sum",
    "worst_trial",
    "worst_min_safety_h",
]


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def log(self, message: str) -> None:
        stamp = datetime.now().isoformat(timespec="seconds")
        line = f"[{stamp}] {message}"
        print(line, flush=True)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


class InstrumentedCBF(CBF):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.n_constraints: list[int] = []
        self.qp_infeasible_count = 0

    def get_QP_matrices(self, *args: Any, **kwargs: Any):
        A, l, P, q = super().get_QP_matrices(*args, **kwargs)
        self.n_constraints.append(int(A.shape[0]))
        return A, l, P, q

    def solve_QP(self, x: torch.Tensor, u_des: torch.Tensor) -> torch.Tensor:
        u = super().solve_QP(x, u_des)
        if not self.solver_success:
            self.qp_infeasible_count += 1
        return u


def bool_to_csv(value: bool | None) -> str:
    if value is None:
        return ""
    return "True" if value else "False"


def parse_bool(value: Any) -> bool | None:
    if value in (True, False):
        return bool(value)
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def percentile(values: list[float] | np.ndarray, q: float) -> float | None:
    if len(values) == 0:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q))


def mean_or_none(values: list[float]) -> float | None:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not clean:
        return None
    return float(np.mean(clean))


def median_or_none(values: list[float]) -> float | None:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not clean:
        return None
    return float(np.median(clean))


def max_or_none(values: list[float]) -> float | None:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not clean:
        return None
    return float(np.max(clean))


def make_start_goal_configs(scene_cfg: dict[str, Any], n_configs: int = 100) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, 2 * np.pi, n_configs)
    t_z = 10 * np.linspace(0, 2 * np.pi, n_configs)
    x0 = np.stack(
        [
            scene_cfg["radius_config"] * np.cos(t),
            scene_cfg["radius_config"] * np.sin(t),
            scene_cfg["radius_z"] * np.sin(t_z),
        ],
        axis=-1,
    ) + scene_cfg["mean_config"]
    xf = np.stack(
        [
            scene_cfg["radius_config"] * np.cos(t + np.pi),
            scene_cfg["radius_config"] * np.sin(t + np.pi),
            scene_cfg["radius_z"] * np.sin(t_z + np.pi),
        ],
        axis=-1,
    ) + scene_cfg["mean_config"]
    return x0, xf


def nominal_control(x: torch.Tensor, goal: torch.Tensor) -> torch.Tensor:
    vel_des = 5.0 * (goal[:3] - x[:3])
    vel_des = torch.clamp(vel_des, -0.1, 0.1)
    vel_des = vel_des + 1.0 * (goal[3:] - x[3:])
    u_des = 1.0 * (vel_des - x[3:])
    return torch.clamp(u_des, -0.1, 0.1)


def cuda_synchronize_if_needed(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def run_one_trial(
    *,
    scene_name: str,
    method_name: str,
    trial: int,
    scene_cfg: dict[str, Any],
    gsplat: GSplatLoader,
    dynamics: DoubleIntegrator,
    device: torch.device,
    max_steps: int,
    goal_tolerance: float,
    distance_type: str,
    alpha: float,
    beta: float,
    dt: float,
) -> dict[str, Any]:
    x0, xf = make_start_goal_configs(scene_cfg, n_configs=100)
    start = x0[trial]
    goal_pos = xf[trial]

    x = torch.tensor(start, device=device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=device, dtype=torch.float32)])
    goal = torch.tensor(goal_pos, device=device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=device, dtype=torch.float32)])

    cbf = None
    if method_name == "safer_splat_filter":
        cbf = InstrumentedCBF(
            gsplat,
            dynamics,
            alpha,
            beta,
            scene_cfg["radius"],
            distance_type=distance_type,
        )

    start_seconds = time.perf_counter()
    traj: list[np.ndarray] = [x.detach().cpu().numpy()]
    controls: list[np.ndarray] = []
    controls_des: list[np.ndarray] = []
    safety: list[float] = []
    step_times: list[float] = []
    success = False
    feasible = True
    stop_reason = "max_steps"
    qp_infeasible_count = 0
    active_constraints: list[int] = []

    for step_idx in range(max_steps):
        x_prev = x.clone()
        u_des = nominal_control(x, goal)

        cuda_synchronize_if_needed(device)
        method_start = time.perf_counter()
        if method_name == "no_filter":
            u = u_des
        elif method_name == "safer_splat_filter":
            assert cbf is not None
            u = cbf.solve_QP(x, u_des)
            active_constraints = cbf.n_constraints
        else:
            raise ValueError(f"Unknown method: {method_name}")
        cuda_synchronize_if_needed(device)
        step_times.append(time.perf_counter() - method_start)

        if cbf is not None and not cbf.solver_success:
            success = False
            feasible = False
            qp_infeasible_count = cbf.qp_infeasible_count
            stop_reason = "solver_failed"
            break

        x = double_integrator_dynamics(x, u) * dt + x
        h, _, _, _ = gsplat.query_distance(
            x,
            radius=scene_cfg["radius"],
            distance_type=distance_type,
        )
        safety.append(float(torch.min(h).detach().cpu().item()))

        controls.append(u.detach().cpu().numpy())
        controls_des.append(u_des.detach().cpu().numpy())
        traj.append(x.detach().cpu().numpy())

        if torch.norm(x - x_prev) < goal_tolerance:
            success = bool(torch.norm(x_prev - goal) < goal_tolerance)
            feasible = True
            stop_reason = "reached_goal" if success else "stopped_before_goal"
            break

        if step_idx >= max_steps - 1:
            success = True
            feasible = True
            stop_reason = "max_steps_loose_success"

    seconds_total = time.perf_counter() - start_seconds
    traj_np = np.stack(traj)
    controls_np = np.asarray(controls, dtype=float) if controls else np.zeros((0, 3))
    controls_des_np = np.asarray(controls_des, dtype=float) if controls_des else np.zeros((0, 3))
    deviations = np.linalg.norm(controls_np - controls_des_np, axis=1) if len(controls_np) else np.array([])
    path_length = float(np.sum(np.linalg.norm(np.diff(traj_np[:, :3], axis=0), axis=1))) if len(traj_np) > 1 else 0.0
    goal_pos_np = np.asarray(goal_pos, dtype=float)
    start_np = np.asarray(start, dtype=float)
    final_pos_np = np.asarray(traj_np[-1, :3], dtype=float)
    goal_distances = np.linalg.norm(traj_np[:, :3] - goal_pos_np[None, :], axis=1)
    initial_goal_distance = float(np.linalg.norm(start_np - goal_pos_np))
    final_goal_distance = float(np.linalg.norm(final_pos_np - goal_pos_np))
    goal_distance_reduction = float(initial_goal_distance - final_goal_distance)
    goal_distance_reduction_ratio = (
        float(goal_distance_reduction / initial_goal_distance)
        if initial_goal_distance > 0.0
        else ""
    )
    closest_goal_step = int(np.argmin(goal_distances)) if len(goal_distances) else 0
    closest_goal_distance = float(goal_distances[closest_goal_step]) if len(goal_distances) else ""
    reached_goal_tolerance = (
        bool(closest_goal_distance <= goal_tolerance)
        if closest_goal_distance != ""
        else None
    )

    if cbf is not None:
        qp_infeasible_count = cbf.qp_infeasible_count

    collision = bool(min(safety) < 0.0) if safety else None
    row = {
        "scene": scene_name,
        "method": method_name,
        "trial": trial,
        "checkpoint": str(scene_cfg["path_to_gsplat"]),
        "gaussian_count": int(gsplat.means.shape[0]),
        "success": bool_to_csv(success),
        "feasible": bool_to_csv(feasible),
        "collision": bool_to_csv(collision),
        "min_safety_h": float(min(safety)) if safety else "",
        "min_safety_h_note": SAFETY_H_NOTE,
        "path_length": path_length,
        "num_steps": len(safety),
        "stop_reason": stop_reason,
        "runtime_mean": float(np.mean(step_times)) if step_times else "",
        "runtime_p95": percentile(step_times, 95),
        "intervention_rate": float(np.mean(deviations > 1e-5)) if deviations.size else (0.0 if method_name == "no_filter" else ""),
        "control_deviation_mean": float(np.mean(deviations)) if deviations.size else 0.0,
        "control_deviation_max": float(np.max(deviations)) if deviations.size else 0.0,
        "active_constraints_mean": float(np.mean(active_constraints)) if active_constraints else (0.0 if method_name == "no_filter" else ""),
        "active_constraints_p95": percentile(active_constraints, 95) if active_constraints else (0.0 if method_name == "no_filter" else ""),
        "qp_infeasible_count": int(qp_infeasible_count),
        "seconds_total": seconds_total,
        "error": "",
        "start_x": float(start_np[0]),
        "start_y": float(start_np[1]),
        "start_z": float(start_np[2]),
        "goal_x": float(goal_pos_np[0]),
        "goal_y": float(goal_pos_np[1]),
        "goal_z": float(goal_pos_np[2]),
        "final_x": float(final_pos_np[0]),
        "final_y": float(final_pos_np[1]),
        "final_z": float(final_pos_np[2]),
        "initial_goal_distance": initial_goal_distance,
        "final_goal_distance": final_goal_distance,
        "goal_distance_reduction": goal_distance_reduction,
        "goal_distance_reduction_ratio": goal_distance_reduction_ratio,
        "closest_goal_distance": closest_goal_distance,
        "closest_goal_step": closest_goal_step,
        "reached_goal_tolerance": bool_to_csv(reached_goal_tolerance),
        "goal_distance_final": final_goal_distance,
        "max_steps": max_steps,
        "goal_tolerance": goal_tolerance,
        "success_definition": "strict stopped-motion goal condition from run.py; stopped_before_goal remains success=False; max_steps timeout follows run.py loose success behavior",
        "radius": scene_cfg["radius"],
        "dt": dt,
        "distance_type": distance_type,
    }
    if trial == 0:
        sample_stride = max(1, len(traj_np) // 250)
        row["_trajectory_sample"] = [
            {
                "scene": scene_name,
                "method": method_name,
                "trial": trial,
                "step": int(step),
                "x": float(point[0]),
                "y": float(point[1]),
                "z": float(point[2]),
                "goal_x": float(goal_pos_np[0]),
                "goal_y": float(goal_pos_np[1]),
                "goal_z": float(goal_pos_np[2]),
                "start_x": float(start_np[0]),
                "start_y": float(start_np[1]),
                "start_z": float(start_np[2]),
            }
            for step, point in enumerate(traj_np[:, :3])
            if step % sample_stride == 0 or step == len(traj_np) - 1
        ]
    return row


def error_row(
    *,
    scene_name: str,
    method_name: str,
    trial: int,
    scene_cfg: dict[str, Any],
    gaussian_count: int | str,
    max_steps: int,
    goal_tolerance: float,
    dt: float,
    distance_type: str,
    exc: BaseException,
) -> dict[str, Any]:
    row = {field: "" for field in TRIAL_FIELDS}
    row.update(
        {
            "scene": scene_name,
            "method": method_name,
            "trial": trial,
            "checkpoint": str(scene_cfg["path_to_gsplat"]),
            "gaussian_count": gaussian_count,
            "success": "False",
            "feasible": "False",
            "collision": "",
            "min_safety_h_note": SAFETY_H_NOTE,
            "stop_reason": "error",
            "qp_infeasible_count": 0,
            "error": repr(exc),
            "max_steps": max_steps,
            "goal_tolerance": goal_tolerance,
            "success_definition": "strict stopped-motion goal condition from run.py; stopped_before_goal remains success=False; max_steps timeout follows run.py loose success behavior",
            "radius": scene_cfg["radius"],
            "dt": dt,
            "distance_type": distance_type,
        }
    )
    return row


def load_existing_trials(path: Path, resume: bool) -> list[dict[str, Any]]:
    if not resume or not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_trials(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def sort_key(row: dict[str, Any]) -> tuple[str, str, int]:
        try:
            trial = int(row.get("trial", 0))
        except (TypeError, ValueError):
            trial = 0
        return (str(row.get("scene", "")), str(row.get("method", "")), trial)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRIAL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(rows, key=sort_key):
            writer.writerow({field: row.get(field, "") for field in TRIAL_FIELDS})


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    keys = sorted({(str(row.get("scene", "")), str(row.get("method", ""))) for row in rows if row.get("method")})
    for scene_name, method_name in keys:
        group = [row for row in rows if row.get("scene") == scene_name and row.get("method") == method_name]
        safety_values = [parse_float(row.get("min_safety_h")) for row in group]
        safety_clean = [v for v in safety_values if v is not None]
        initial_goal_distances = [parse_float(row.get("initial_goal_distance")) for row in group]
        final_goal_distances = [parse_float(row.get("final_goal_distance", row.get("goal_distance_final"))) for row in group]
        closest_goal_distances = [parse_float(row.get("closest_goal_distance")) for row in group]
        goal_distance_reductions = [parse_float(row.get("goal_distance_reduction")) for row in group]
        goal_distance_reduction_ratios = [parse_float(row.get("goal_distance_reduction_ratio")) for row in group]
        path_lengths = [parse_float(row.get("path_length")) for row in group]
        num_steps = [parse_float(row.get("num_steps")) for row in group]
        runtime_mean = [parse_float(row.get("runtime_mean")) for row in group]
        runtime_p95 = [parse_float(row.get("runtime_p95")) for row in group]
        intervention = [parse_float(row.get("intervention_rate")) for row in group]
        control_dev = [parse_float(row.get("control_deviation_mean")) for row in group]
        control_dev_max = [parse_float(row.get("control_deviation_max")) for row in group]
        active_mean = [parse_float(row.get("active_constraints_mean")) for row in group]
        active_p95 = [parse_float(row.get("active_constraints_p95")) for row in group]
        seconds_total = [parse_float(row.get("seconds_total")) for row in group]
        worst_trial = ""
        worst_min = ""
        if safety_clean:
            min_value = min(safety_clean)
            for row, value in zip(group, safety_values):
                if value == min_value:
                    worst_trial = row.get("trial", "")
                    worst_min = value
                    break

        summaries.append(
            {
                "scene": scene_name,
                "method": method_name,
                "rows": len(group),
                "total_rows": len(group),
                "success_count": sum(parse_bool(row.get("success")) is True for row in group),
                "feasible_count": sum(parse_bool(row.get("feasible")) is True for row in group),
                "collision_count": sum(parse_bool(row.get("collision")) is True for row in group),
                "collision_free_count": sum(parse_bool(row.get("collision")) is False for row in group),
                "error_count": sum(bool(str(row.get("error", "")).strip()) for row in group),
                "stopped_before_goal_count": sum(row.get("stop_reason") == "stopped_before_goal" for row in group),
                "max_steps_loose_success_count": sum(row.get("stop_reason") == "max_steps_loose_success" for row in group),
                "solver_failed_count": sum(row.get("stop_reason") == "solver_failed" for row in group),
                "qp_infeasible_count_sum": sum(int(float(row.get("qp_infeasible_count") or 0)) for row in group),
                "min_safety_h_min": min(safety_clean) if safety_clean else "",
                "min_safety_h_mean": mean_or_none(safety_clean),
                "min_safety_h_median": median_or_none(safety_clean),
                "initial_goal_distance_mean": mean_or_none([v for v in initial_goal_distances if v is not None]),
                "final_goal_distance_mean": mean_or_none([v for v in final_goal_distances if v is not None]),
                "closest_goal_distance_mean": mean_or_none([v for v in closest_goal_distances if v is not None]),
                "goal_distance_reduction_mean": mean_or_none([v for v in goal_distance_reductions if v is not None]),
                "goal_distance_reduction_ratio_mean": mean_or_none([v for v in goal_distance_reduction_ratios if v is not None]),
                "reached_goal_tolerance_count": sum(parse_bool(row.get("reached_goal_tolerance")) is True for row in group),
                "path_length_mean": mean_or_none([v for v in path_lengths if v is not None]),
                "num_steps_mean": mean_or_none([v for v in num_steps if v is not None]),
                "runtime_mean_mean": mean_or_none([v for v in runtime_mean if v is not None]),
                "runtime_p95_mean": mean_or_none([v for v in runtime_p95 if v is not None]),
                "intervention_rate_mean": mean_or_none([v for v in intervention if v is not None]),
                "control_deviation_mean_mean": mean_or_none([v for v in control_dev if v is not None]),
                "control_deviation_max_max": max_or_none([v for v in control_dev_max if v is not None]),
                "active_constraints_mean_mean": mean_or_none([v for v in active_mean if v is not None]),
                "active_constraints_p95_mean": mean_or_none([v for v in active_p95 if v is not None]),
                "seconds_total_sum": sum(v for v in seconds_total if v is not None),
                "worst_trial": worst_trial,
                "worst_min_safety_h": worst_min,
            }
        )
    return summaries


def write_summary(path: Path, summaries: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in summaries:
            writer.writerow({field: row.get(field, "") for field in SUMMARY_FIELDS})


def write_metrics(path: Path, args: argparse.Namespace, summaries: list[dict[str, Any]], total_rows: int) -> None:
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "script": str(Path(__file__).resolve()),
        "config": {
            "scene": args.scene,
            "methods": args.methods,
            "trial_start": args.trial_start,
            "trial_end": args.trial_end,
            "max_steps": args.max_steps,
            "goal_tolerance": args.goal_tolerance,
            "device": args.device,
            "seed": args.seed,
            "resume": args.resume,
            "skip_existing": args.skip_existing,
        },
        "total_trial_rows": total_rows,
        "min_safety_h_note": SAFETY_H_NOTE,
        "summary": summaries,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_trajectory_samples(path: Path, rows: list[dict[str, Any]]) -> None:
    samples: list[dict[str, Any]] = []
    for row in rows:
        samples.extend(row.get("_trajectory_sample", []))
    if not samples:
        return
    fields = [
        "scene",
        "method",
        "trial",
        "step",
        "x",
        "y",
        "z",
        "goal_x",
        "goal_y",
        "goal_z",
        "start_x",
        "start_y",
        "start_z",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for sample in samples:
            writer.writerow({field: sample.get(field, "") for field in fields})


def write_plot(path: Path, rows: list[dict[str, Any]]) -> None:
    plot_rows = [row for row in rows if parse_float(row.get("min_safety_h")) is not None]
    if not plot_rows:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No completed trial rows", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(path, dpi=160)
        plt.close(fig)
        return

    methods = [m for m in METHODS if any(row.get("method") == m for row in plot_rows)]
    colors = {"no_filter": "#d95f02", "safer_splat_filter": "#1b9e77"}
    trials = sorted({int(row["trial"]) for row in plot_rows})

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ax_traj, ax_safety, ax_final, ax_progress = axes.ravel()

    # Typical trajectory panel. Full sampled trajectories are available for trial 0
    # in fresh runs. If a resumed CSV lacks samples, fall back to start-final-goal
    # segments so the plot remains useful.
    drew_sample = False
    for method_name in methods:
        samples = []
        for row in rows:
            if row.get("method") == method_name and int(row.get("trial", -1)) == 0:
                samples = row.get("_trajectory_sample", [])
                break
        if samples:
            xs = [float(sample["x"]) for sample in samples]
            ys = [float(sample["y"]) for sample in samples]
            ax_traj.plot(xs, ys, label=f"{method_name} trajectory", color=colors.get(method_name))
            drew_sample = True
        else:
            row = next((r for r in plot_rows if r.get("method") == method_name and int(r.get("trial", -1)) == 0), None)
            if row:
                xs = [parse_float(row.get("start_x")), parse_float(row.get("final_x")), parse_float(row.get("goal_x"))]
                ys = [parse_float(row.get("start_y")), parse_float(row.get("final_y")), parse_float(row.get("goal_y"))]
                if all(v is not None for v in xs + ys):
                    ax_traj.plot(xs, ys, marker="o", label=f"{method_name} start-final-goal", color=colors.get(method_name))
    trial0 = next((r for r in plot_rows if int(r.get("trial", -1)) == 0), None)
    if trial0:
        sx, sy = parse_float(trial0.get("start_x")), parse_float(trial0.get("start_y"))
        gx, gy = parse_float(trial0.get("goal_x")), parse_float(trial0.get("goal_y"))
        if sx is not None and sy is not None:
            ax_traj.scatter([sx], [sy], marker="o", color="black", label="start")
        if gx is not None and gy is not None:
            ax_traj.scatter([gx], [gy], marker="*", color="black", label="goal")
    ax_traj.set_title("Trial 0 trajectory" if drew_sample else "Trial 0 start-final-goal")
    ax_traj.set_xlabel("x")
    ax_traj.set_ylabel("y")
    ax_traj.axis("equal")
    ax_traj.legend(fontsize=8)

    safety_data = [
        [parse_float(row.get("min_safety_h")) for row in plot_rows if row.get("method") == method_name]
        for method_name in methods
    ]
    safety_data = [[v for v in values if v is not None] for values in safety_data]
    if any(safety_data):
        ax_safety.boxplot(safety_data, tick_labels=methods, showfliers=True)
    ax_safety.axhline(0.0, color="black", linewidth=1, linestyle="--")
    ax_safety.set_title("min_safety_h distribution")
    ax_safety.set_ylabel("official safety h; not meters")

    width = 0.8 / max(1, len(methods))
    x = np.arange(len(trials), dtype=float)
    for idx, method_name in enumerate(methods):
        by_trial = {int(row["trial"]): row for row in plot_rows if row.get("method") == method_name}
        finals = []
        ratios = []
        for trial in trials:
            row = by_trial.get(trial)
            finals.append(np.nan if row is None else parse_float(row.get("final_goal_distance")) or np.nan)
            ratios.append(np.nan if row is None else parse_float(row.get("goal_distance_reduction_ratio")) or np.nan)
        offset = (idx - (len(methods) - 1) / 2) * width
        ax_final.bar(x + offset, finals, width=width, label=method_name, color=colors.get(method_name), alpha=0.82)
        ax_progress.bar(x + offset, ratios, width=width, label=method_name, color=colors.get(method_name), alpha=0.82)

    ax_final.set_title("final_goal_distance by trial")
    ax_final.set_xlabel("trial")
    ax_final.set_ylabel("distance to goal")
    ax_final.set_xticks(x[:: max(1, len(x) // 20)])
    ax_final.set_xticklabels([str(t) for t in trials[:: max(1, len(trials) // 20)]], rotation=45)
    ax_final.legend(fontsize=8)

    ax_progress.set_title("goal_distance_reduction_ratio by trial")
    ax_progress.set_xlabel("trial")
    ax_progress.set_ylabel("progress ratio")
    ax_progress.set_xticks(x[:: max(1, len(x) // 20)])
    ax_progress.set_xticklabels([str(t) for t in trials[:: max(1, len(trials) // 20)]], rotation=45)
    ax_progress.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def refresh_outputs(output_dir: Path, rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    trials_csv = output_dir / "trials.csv"
    summary_csv = output_dir / "summary.csv"
    metrics_json = output_dir / "metrics.json"
    plot_png = output_dir / "comparison_plot.png"

    write_trials(trials_csv, rows)
    summaries = summarize_rows(rows)
    write_summary(summary_csv, summaries)
    write_metrics(metrics_json, args, summaries, len(rows))
    write_trajectory_samples(output_dir / "trajectory_samples.csv", rows)
    write_plot(plot_png, rows)
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Official checkpoint no-filter vs SAFER-Splat filter comparison.")
    parser.add_argument("--scene", choices=sorted(SCENES), default="stonehenge")
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=list(METHODS))
    parser.add_argument("--trial-start", type=int, default=0)
    parser.add_argument("--trial-end", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=600)
    parser.add_argument("--goal-tolerance", type=float, default=0.001)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.trial_start < 0 or args.trial_end < args.trial_start or args.trial_end >= 100:
        raise ValueError("--trial-start/--trial-end must define an inclusive range within [0, 99]")

    output_dir = args.output_dir or Path(f"reproduction/results/official_checkpoint_filter_comparison_{args.scene}")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = Logger(output_dir / "run_log.txt")

    alpha = 5.0
    beta = 1.0
    dt = 0.05
    distance_type = "ball-to-ellipsoid"

    try:
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but torch.cuda.is_available() is False")
        device = torch.device(args.device)
        logger.log(f"script={Path(__file__).resolve()}")
        logger.log(f"scene={args.scene} methods={args.methods} trials={args.trial_start}-{args.trial_end}")
        logger.log(f"device={device} torch={torch.__version__} cuda_available={torch.cuda.is_available()}")
        logger.log(f"max_steps={args.max_steps} goal_tolerance={args.goal_tolerance}")
        logger.log(f"min_safety_h_note={SAFETY_H_NOTE}")

        scene_cfg = SCENES[args.scene]
        logger.log(f"checkpoint={scene_cfg['path_to_gsplat']}")
        if not scene_cfg["path_to_gsplat"].exists():
            raise FileNotFoundError(scene_cfg["path_to_gsplat"])

        trials_csv = output_dir / "trials.csv"
        rows = load_existing_trials(trials_csv, args.resume)
        existing_keys = {
            (str(row.get("scene")), str(row.get("method")), int(row.get("trial")))
            for row in rows
            if str(row.get("trial", "")).strip().isdigit()
        }

        load_start = time.perf_counter()
        gsplat = GSplatLoader(scene_cfg["path_to_gsplat"], device)
        cuda_synchronize_if_needed(device)
        load_seconds = time.perf_counter() - load_start
        gaussian_count = int(gsplat.means.shape[0])
        logger.log(f"loaded_gsplat_seconds={load_seconds:.6f} gaussian_count={gaussian_count}")
        dynamics = DoubleIntegrator(device=device, ndim=3)

        for method_name in args.methods:
            for trial in range(args.trial_start, args.trial_end + 1):
                key = (args.scene, method_name, trial)
                if args.resume and args.skip_existing and key in existing_keys:
                    logger.log(f"skip_existing method={method_name} trial={trial}")
                    continue
                logger.log(f"start method={method_name} trial={trial}")
                try:
                    row = run_one_trial(
                        scene_name=args.scene,
                        method_name=method_name,
                        trial=trial,
                        scene_cfg=scene_cfg,
                        gsplat=gsplat,
                        dynamics=dynamics,
                        device=device,
                        max_steps=args.max_steps,
                        goal_tolerance=args.goal_tolerance,
                        distance_type=distance_type,
                        alpha=alpha,
                        beta=beta,
                        dt=dt,
                    )
                    logger.log(
                        "done method={method} trial={trial} success={success} collision={collision} "
                        "min_safety_h={min_h} steps={steps} stop={stop}".format(
                            method=method_name,
                            trial=trial,
                            success=row["success"],
                            collision=row["collision"],
                            min_h=row["min_safety_h"],
                            steps=row["num_steps"],
                            stop=row["stop_reason"],
                        )
                    )
                except BaseException as exc:
                    logger.log(f"error method={method_name} trial={trial}: {exc!r}")
                    logger.log(traceback.format_exc())
                    row = error_row(
                        scene_name=args.scene,
                        method_name=method_name,
                        trial=trial,
                        scene_cfg=scene_cfg,
                        gaussian_count=gaussian_count,
                        max_steps=args.max_steps,
                        goal_tolerance=args.goal_tolerance,
                        dt=dt,
                        distance_type=distance_type,
                        exc=exc,
                    )
                rows = [r for r in rows if (str(r.get("scene")), str(r.get("method")), int(r.get("trial", -1))) != key]
                rows.append(row)
                existing_keys.add(key)
                summaries = refresh_outputs(output_dir, rows, args)
                logger.log(f"refreshed rows={len(rows)} summaries={len(summaries)}")

        summaries = refresh_outputs(output_dir, rows, args)
        logger.log("final_summary=" + json.dumps(summaries, ensure_ascii=True))
        logger.log(f"wrote={output_dir / 'trials.csv'}")
        logger.log(f"wrote={output_dir / 'summary.csv'}")
        logger.log(f"wrote={output_dir / 'metrics.json'}")
        logger.log(f"wrote={output_dir / 'comparison_plot.png'}")
        return 0
    finally:
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
