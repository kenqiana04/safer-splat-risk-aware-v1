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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import scipy
import torch
import pandas as pd

from cbf.cbf_utils import CBF  # noqa: E402
from dynamics.systems import DoubleIntegrator, double_integrator_dynamics  # noqa: E402
from splat.gsplat_utils import GSplatLoader  # noqa: E402


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

METHODS = ("no_filter", "safer_splat_filter", "risk_aware_v1_pre_cbf")
SAFETY_H_NOTE = "official GSplatLoader.query_distance safety h value; not meters"
SUCCESS_DEFINITION = "strict stopped-motion goal condition from run.py; stopped_before_goal remains success=False"

TRIAL_FIELDS = [
    "scene",
    "method",
    "trial",
    "checkpoint",
    "gaussian_count",
    "success",
    "collision",
    "collision_free",
    "stop_reason",
    "min_safety_h",
    "min_safety_h_note",
    "goal_distance_reduction_ratio",
    "initial_goal_distance",
    "final_goal_distance",
    "closest_goal_distance",
    "closest_goal_step",
    "num_steps",
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
    "success_definition",
]

STEP_FIELDS = [
    "scene",
    "method",
    "trial",
    "step",
    "time",
    "x",
    "y",
    "z",
    "vx",
    "vy",
    "vz",
    "goal_x",
    "goal_y",
    "goal_z",
    "goal_distance",
    "nominal_u_x",
    "nominal_u_y",
    "nominal_u_z",
    "filtered_u_x",
    "filtered_u_y",
    "filtered_u_z",
    "control_deviation",
    "min_safety_h_step",
    "collision_step",
    "qp_feasible",
    "runtime_step",
    "active_constraints_count",
]

ACTIVE_FIELDS = [
    "scene",
    "method",
    "trial",
    "step",
    "gaussian_id",
    "candidate_local_id",
    "candidate_rank",
    "selected_by_baseline",
    "is_forced_near_critical",
    "h_value",
    "distance_or_safety_value",
    "mean_x",
    "mean_y",
    "mean_z",
    "scale_x",
    "scale_y",
    "scale_z",
    "max_scale",
    "anisotropy",
    "opacity",
    "volume_proxy",
    "distance_to_robot",
    "heading_alignment_proxy",
    "mapping_status",
    "logging_scope",
]

DEBUG_FIELDS = [
    "scene",
    "trial",
    "step",
    "candidate_budget",
    "candidate_count_total",
    "candidate_count_forced_near",
    "candidate_count_forced_heading",
    "candidate_count_risk_ranked",
    "candidate_count_final",
    "fallback_used",
    "v1_insertion_level",
    "near_distance_threshold",
    "heading_distance_threshold",
    "heading_cos_threshold",
    "risk_score_name",
    "fallback_reason",
    "min_safety_h_step",
    "runtime_step",
    "control_deviation",
    "active_constraints_count",
]

SUMMARY_FIELDS = [
    "scene",
    "method",
    "rows",
    "success_count",
    "collision_count",
    "collision_free_count",
    "stopped_before_goal_count",
    "solver_failed_count",
    "min_safety_h_min",
    "min_safety_h_mean",
    "goal_distance_reduction_ratio_mean",
    "final_goal_distance_mean",
    "closest_goal_distance_mean",
    "num_steps_mean",
    "runtime_mean_mean",
    "runtime_p95_mean",
    "intervention_rate_mean",
    "control_deviation_mean_mean",
    "active_constraints_mean_mean",
    "qp_infeasible_count_sum",
]


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def log(self, message: str) -> None:
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
        print(line, flush=True)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def bool_to_csv(value: bool | None) -> str:
    if value is None:
        return ""
    return "True" if value else "False"


def parse_bool(value: Any) -> bool | None:
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


def percentile(values: list[float] | np.ndarray, q: float) -> float | str:
    if len(values) == 0:
        return ""
    return float(np.percentile(np.asarray(values, dtype=float), q))


def mean_or_blank(values: list[float]) -> float | str:
    clean = [float(v) for v in values if v is not None and np.isfinite(float(v))]
    return float(np.mean(clean)) if clean else ""


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


def cuda_sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def h_rep_minimal_with_indices(A: np.ndarray, b: np.ndarray, pt: np.ndarray, ids: np.ndarray):
    halfspaces = np.concatenate([A, -b[..., None]], axis=-1)
    hs = scipy.spatial.HalfspaceIntersection(halfspaces, pt, incremental=False, qhull_options=None)
    try:
        selected = np.asarray(hs.dual_vertices, dtype=int)
        minimal_Ab = halfspaces[selected]
        selected_ids = ids[selected]
        mapping_status = "global_gaussian_id_from_dual_vertices"
    except Exception:
        qhull_pts = hs.intersections
        convex_hull = scipy.spatial.ConvexHull(qhull_pts, incremental=False, qhull_options=None)
        minimal_Ab = convex_hull.equations
        selected_ids = None
        mapping_status = "mapping_unavailable_convex_hull_fallback"
    minimal_A = minimal_Ab[:, :-1]
    minimal_b = -minimal_Ab[:, -1]
    return minimal_A, minimal_b, selected_ids, mapping_status


def minmax_current(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    if values.size == 0:
        return values
    lo = float(np.min(values))
    hi = float(np.max(values))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.zeros_like(values, dtype=float)
    return (values - lo) / (hi - lo)


class RiskScoreTable:
    def __init__(self, path: Path, gaussian_count: int):
        if not path.exists():
            raise FileNotFoundError(f"Missing risk score table: {path}")
        table = pd.read_csv(path)
        table["gaussian_id"] = pd.to_numeric(table["gaussian_id"], errors="coerce")
        table = table.dropna(subset=["gaussian_id"]).copy()
        table["gaussian_id"] = table["gaussian_id"].astype(np.int64)
        self.path = path
        self.gaussian_count = gaussian_count
        self.columns: dict[str, np.ndarray] = {}
        for column in [
            "active_frequency_norm",
            "opacity_norm",
            "max_scale_norm",
            "anisotropy_norm",
            "volume_proxy_norm",
            "risk_v0_active_frequency",
            "risk_v1_geometry",
            "risk_v2_hybrid",
        ]:
            values = np.zeros(gaussian_count, dtype=float)
            if column in table.columns:
                ids = table["gaussian_id"].to_numpy(dtype=int)
                valid = (ids >= 0) & (ids < gaussian_count)
                values[ids[valid]] = pd.to_numeric(table.loc[valid, column], errors="coerce").fillna(0.0).to_numpy(dtype=float)
            self.columns[column] = values

    def runtime_scores(
        self,
        *,
        ids: np.ndarray,
        risk_score_name: str,
        distance_to_robot: np.ndarray,
        heading_alignment: np.ndarray,
    ) -> np.ndarray:
        ids = np.asarray(ids, dtype=int)
        valid = (ids >= 0) & (ids < self.gaussian_count)
        safe_ids = np.where(valid, ids, 0)
        active = self.columns["active_frequency_norm"][safe_ids]
        opacity = self.columns["opacity_norm"][safe_ids]
        max_scale = self.columns["max_scale_norm"][safe_ids]
        anisotropy = self.columns["anisotropy_norm"][safe_ids]
        inv_distance = minmax_current(1.0 / np.maximum(np.asarray(distance_to_robot, dtype=float), 1e-9))
        heading = np.clip(np.nan_to_num(heading_alignment, nan=0.0), 0.0, 1.0)
        if risk_score_name == "risk_v0_active_frequency":
            scores = active
        elif risk_score_name == "risk_v1_geometry":
            scores = 0.25 * opacity + 0.25 * anisotropy + 0.25 * max_scale + 0.25 * inv_distance
        elif risk_score_name == "risk_v2_hybrid":
            scores = (
                0.35 * active
                + 0.20 * opacity
                + 0.15 * anisotropy
                + 0.15 * max_scale
                + 0.10 * inv_distance
                + 0.05 * heading
            )
        else:
            raise ValueError(f"Unsupported risk score: {risk_score_name}")
        scores = np.asarray(scores, dtype=float)
        scores[~valid] = 0.0
        return np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)


class DetailedCBF(CBF):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.last_h_values: np.ndarray | None = None
        self.last_active_gaussian_ids: np.ndarray | None = None
        self.last_active_constraints_count = 0
        self.last_mapping_status = "not_run"
        self.qp_infeasible_count = 0

    def get_QP_matrices(self, x, u_des, minimal=True):
        tnow = time.time()
        h, grad_h, hes_h, info = self.gsplat.query_distance(
            x[..., :3],
            radius=self.radius,
            distance_type=self.distance_type,
        )
        self.times_cbf.append(time.time() - tnow)
        self.last_h_values = h.detach().cpu().numpy().reshape(-1)

        h = h.unsqueeze(-1)
        grad_h = torch.cat((grad_h, torch.zeros(h.shape[0], 3).to(grad_h.device)), dim=-1)
        hes_h = torch.cat((hes_h, torch.zeros(h.shape[0], 3, 3).to(hes_h.device)), dim=2)
        hes_h = torch.cat((hes_h, torch.zeros(h.shape[0], 3, 6).to(hes_h.device)), dim=1)

        f, g, df = self.dynamics.system(x)
        f = f.unsqueeze(-1)
        lfh = torch.matmul(grad_h, f).squeeze()
        lflfh = torch.matmul(f.T, torch.matmul(hes_h, f)).squeeze() + torch.matmul(grad_h, torch.matmul(df, f)).squeeze()
        lglfh = torch.matmul(g.T, torch.matmul(hes_h, f)).squeeze() + torch.matmul(grad_h, torch.matmul(df, g)).squeeze()
        l = -lflfh - self.alpha(lfh) - self.beta(lfh + self.alpha(h.squeeze()))
        A = lglfh[None]
        P = np.eye(3)
        q = -1 * u_des.cpu().numpy()
        A = A.cpu().numpy().squeeze()
        l = l.cpu().numpy()

        norms = np.linalg.norm(A, axis=-1, keepdims=True)
        A = -A / norms
        l = -l / norms.squeeze()
        raw_ids = np.arange(A.shape[0], dtype=int)
        final_ids: np.ndarray | None = raw_ids
        mapping_status = "all_constraints_no_minimal_pruning"

        tnow = time.time()
        if minimal:
            collisionless = (h.cpu().numpy() > 0).squeeze()
            collisionless_A = A[collisionless]
            collisionless_l = l[collisionless]
            collisionless_ids = raw_ids[collisionless]
            collision_A = A[~collisionless]
            collision_l = l[~collisionless]
            collision_ids = raw_ids[~collisionless]
            try:
                try:
                    feasible_pt = -(self.alpha_constant + self.beta_constant) * x[..., 3:6].cpu().numpy()
                    Aminimal, lminimal, minimal_ids, mapping_status = h_rep_minimal_with_indices(
                        collisionless_A,
                        collisionless_l,
                        feasible_pt,
                        collisionless_ids,
                    )
                except Exception:
                    raise ValueError("Failed to find an interior point for the minimal polytope.")
                A = np.concatenate([Aminimal, collision_A], axis=0)
                l = np.concatenate([lminimal, collision_l], axis=0)
                if minimal_ids is None:
                    final_ids = None
                else:
                    final_ids = np.concatenate([minimal_ids, collision_ids], axis=0)
            except Exception:
                mapping_status = "minimal_pruning_failed_kept_all_constraints"
                final_ids = raw_ids
        self.times_prune.append(time.time() - tnow)

        self.last_active_constraints_count = int(A.shape[0])
        self.last_active_gaussian_ids = final_ids
        self.last_mapping_status = mapping_status
        return A, l, P, q

    def solve_QP(self, x, u_des):
        u = super().solve_QP(x, u_des)
        if not self.solver_success:
            self.qp_infeasible_count += 1
        return u


class RiskAwareTopKCBF(DetailedCBF):
    def __init__(
        self,
        *args: Any,
        risk_table: RiskScoreTable,
        topk: int,
        h_critical: float,
        near_distance_threshold: float,
        risk_score_name: str,
        min_required_constraints: int,
        heading_force_threshold: float,
        heading_force_distance: float,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.risk_table = risk_table
        self.topk = int(topk)
        self.h_critical = float(h_critical)
        self.near_distance_threshold = float(near_distance_threshold)
        self.risk_score_name = risk_score_name
        self.min_required_constraints = int(min_required_constraints)
        self.heading_force_threshold = float(heading_force_threshold)
        self.heading_force_distance = float(heading_force_distance)
        self.last_selection_debug: dict[str, Any] = {}

    def get_QP_matrices(self, x, u_des, minimal=True):
        A, l, P, q = super().get_QP_matrices(x, u_des, minimal=minimal)
        baseline_count = int(A.shape[0])
        debug = {
            "topk": self.topk,
            "h_critical": self.h_critical,
            "near_distance_threshold": self.near_distance_threshold,
            "risk_score_name": self.risk_score_name,
            "baseline_active_constraints_count": baseline_count,
            "risk_aware_selected_count": baseline_count,
            "forced_low_h_count": "",
            "forced_near_count": "",
            "forced_heading_count": "",
            "risk_ranked_count": "",
            "fallback_used": "True",
            "fallback_reason": "",
            "min_selected_h": "",
        }

        ids = self.last_active_gaussian_ids
        h_values = self.last_h_values
        if baseline_count == 0:
            debug["fallback_reason"] = "no_constraints"
            self.last_selection_debug = debug
            return A, l, P, q
        if ids is None or h_values is None:
            debug["fallback_reason"] = "missing_ids_or_h_values"
            self.last_selection_debug = debug
            return A, l, P, q
        ids = np.asarray(ids, dtype=int)
        if ids.shape[0] != baseline_count:
            debug["fallback_reason"] = "id_constraint_count_mismatch"
            self.last_selection_debug = debug
            return A, l, P, q
        if self.topk <= 0:
            debug["fallback_reason"] = "invalid_topk"
            self.last_selection_debug = debug
            return A, l, P, q

        try:
            h_selected = np.asarray(h_values, dtype=float)[ids]
            means = self.gsplat.means.detach().cpu().numpy()[ids]
            robot = x[:3].detach().cpu().numpy()
            vectors = means - robot[None, :]
            distances = np.linalg.norm(vectors, axis=1)
            heading = u_des.detach().cpu().numpy()
            heading_norm = float(np.linalg.norm(heading))
            vector_norms = np.maximum(distances, 1e-12)
            if heading_norm > 1e-12:
                heading_alignment = np.sum(vectors * heading[None, :], axis=1) / (heading_norm * vector_norms)
            else:
                heading_alignment = np.zeros_like(distances)

            forced_low_h = h_selected <= self.h_critical
            forced_near = distances <= self.near_distance_threshold
            forced_heading = (heading_alignment >= self.heading_force_threshold) & (distances <= self.heading_force_distance)
            forced = forced_low_h | forced_near | forced_heading

            scores = self.risk_table.runtime_scores(
                ids=ids,
                risk_score_name=self.risk_score_name,
                distance_to_robot=distances,
                heading_alignment=heading_alignment,
            )
            selected = np.zeros(baseline_count, dtype=bool)
            selected[forced] = True
            forced_count = int(np.sum(forced))
            if forced_count < self.topk:
                budget = self.topk - forced_count
                remaining = np.where(~forced)[0]
                ranked_remaining = remaining[np.argsort(scores[remaining])[::-1]]
                selected[ranked_remaining[:budget]] = True
            selected_indices = np.where(selected)[0]
            if selected_indices.shape[0] < min(self.min_required_constraints, baseline_count):
                debug["fallback_reason"] = "below_min_required_constraints"
                self.last_selection_debug = debug
                return A, l, P, q
            if selected_indices.shape[0] == 0:
                debug["fallback_reason"] = "empty_selection"
                self.last_selection_debug = debug
                return A, l, P, q

            A = A[selected_indices]
            l = l[selected_indices]
            selected_ids = ids[selected_indices]
            self.last_active_gaussian_ids = selected_ids
            self.last_active_constraints_count = int(A.shape[0])
            self.last_mapping_status = f"{self.last_mapping_status}_risk_aware_topk"
            debug.update(
                {
                    "risk_aware_selected_count": int(A.shape[0]),
                    "forced_low_h_count": int(np.sum(forced_low_h)),
                    "forced_near_count": int(np.sum(forced_near)),
                    "forced_heading_count": int(np.sum(forced_heading)),
                    "risk_ranked_count": int(max(0, A.shape[0] - forced_count)),
                    "fallback_used": "False",
                    "fallback_reason": "",
                    "min_selected_h": float(np.min(h_selected[selected_indices])),
                }
            )
            self.last_selection_debug = debug
            return A, l, P, q
        except Exception as exc:
            debug["fallback_reason"] = f"selection_exception:{type(exc).__name__}"
            self.last_selection_debug = debug
            return A, l, P, q


class SubsetGSplatLoader:
    """Reproduction-only loader wrapper that queries a per-step Gaussian subset."""

    def __init__(self, base: GSplatLoader):
        self.base = base
        self._subset_ids: np.ndarray | None = None

    def set_subset(self, ids: np.ndarray | None) -> None:
        if ids is None:
            self._subset_ids = None
            return
        ids = np.asarray(ids, dtype=np.int64)
        if ids.size == 0:
            self._subset_ids = None
        else:
            self._subset_ids = ids

    def query_distance(self, *args: Any, **kwargs: Any):
        if self._subset_ids is None:
            return self.base.query_distance(*args, **kwargs)

        names = ["means", "rots", "scales", "opacities", "covs", "covs_inv"]
        originals: dict[str, Any] = {}
        subset_tensors: dict[str, Any] = {}
        for name in names:
            if hasattr(self.base, name):
                value = getattr(self.base, name)
                originals[name] = value
                if torch.is_tensor(value):
                    index = torch.as_tensor(self._subset_ids, dtype=torch.long, device=value.device)
                    subset_tensors[name] = value[index]
                else:
                    subset_tensors[name] = value[self._subset_ids]
        try:
            for name, value in subset_tensors.items():
                setattr(self.base, name, value)
            return self.base.query_distance(*args, **kwargs)
        finally:
            for name, value in originals.items():
                setattr(self.base, name, value)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.base, name)


class V1CandidateSelector:
    def __init__(
        self,
        *,
        gsplat: GSplatLoader,
        risk_table: RiskScoreTable,
        candidate_budget: int,
        near_distance_threshold: float,
        heading_distance_threshold: float,
        heading_cos_threshold: float,
        risk_score_name: str,
        min_candidate_budget: int,
    ):
        self.means = gsplat.means.detach().cpu().numpy()
        self.total = int(self.means.shape[0])
        self.all_ids = np.arange(self.total, dtype=np.int64)
        self.risk_table = risk_table
        self.candidate_budget = int(candidate_budget)
        self.near_distance_threshold = float(near_distance_threshold)
        self.heading_distance_threshold = float(heading_distance_threshold)
        self.heading_cos_threshold = float(heading_cos_threshold)
        self.risk_score_name = risk_score_name
        self.min_candidate_budget = int(min_candidate_budget)
        active = risk_table.columns.get("active_frequency_norm", np.zeros(self.total, dtype=float))
        history_k = max(1, min(self.total, max(250, self.candidate_budget // 4)))
        self.high_active_ids = np.argsort(active)[::-1][:history_k].astype(np.int64)

    def select(self, x: torch.Tensor, u_des: torch.Tensor) -> tuple[np.ndarray | None, dict[str, Any]]:
        debug: dict[str, Any] = {
            "candidate_budget": self.candidate_budget,
            "candidate_count_total": self.total,
            "candidate_count_forced_near": "",
            "candidate_count_forced_heading": "",
            "candidate_count_risk_ranked": "",
            "candidate_count_final": self.total,
            "fallback_used": "True",
            "v1_insertion_level": "partial_pre_cbf",
            "near_distance_threshold": self.near_distance_threshold,
            "heading_distance_threshold": self.heading_distance_threshold,
            "heading_cos_threshold": self.heading_cos_threshold,
            "risk_score_name": self.risk_score_name,
            "fallback_reason": "",
        }
        if self.candidate_budget <= 0:
            debug["fallback_reason"] = "invalid_candidate_budget"
            return None, debug

        try:
            robot = x[:3].detach().cpu().numpy()
            heading = u_des.detach().cpu().numpy()
            vectors = self.means - robot[None, :]
            distances = np.linalg.norm(vectors, axis=1)
            heading_norm = float(np.linalg.norm(heading))
            if heading_norm > 1e-12:
                heading_alignment = np.sum(vectors * heading[None, :], axis=1) / (
                    heading_norm * np.maximum(distances, 1e-12)
                )
            else:
                heading_alignment = np.zeros_like(distances)

            forced_near = distances <= self.near_distance_threshold
            forced_heading = (distances <= self.heading_distance_threshold) & (
                heading_alignment >= self.heading_cos_threshold
            )
            history_distance = max(self.heading_distance_threshold, 2.0 * self.near_distance_threshold)
            forced_history = np.zeros(self.total, dtype=bool)
            relevant_history = self.high_active_ids[distances[self.high_active_ids] <= history_distance]
            forced_history[relevant_history] = True
            forced = forced_near | forced_heading | forced_history

            scores = self.risk_table.runtime_scores(
                ids=self.all_ids,
                risk_score_name=self.risk_score_name,
                distance_to_robot=distances,
                heading_alignment=heading_alignment,
            )
            selected = np.zeros(self.total, dtype=bool)
            selected[forced] = True
            forced_count = int(np.sum(selected))
            ranked_count = 0
            if forced_count < self.candidate_budget:
                remaining = np.where(~selected)[0]
                ranked_remaining = remaining[np.argsort(scores[remaining])[::-1]]
                ranked_count = int(min(self.candidate_budget - forced_count, ranked_remaining.shape[0]))
                selected[ranked_remaining[:ranked_count]] = True

            selected_ids = np.where(selected)[0].astype(np.int64)
            final_count = int(selected_ids.shape[0])
            debug.update(
                {
                    "candidate_count_forced_near": int(np.sum(forced_near)),
                    "candidate_count_forced_heading": int(np.sum(forced_heading)),
                    "candidate_count_risk_ranked": ranked_count,
                    "candidate_count_final": final_count,
                }
            )
            if final_count < min(self.min_candidate_budget, self.total):
                debug["fallback_reason"] = "below_min_candidate_budget"
                debug["candidate_count_final"] = self.total
                return None, debug
            debug["fallback_used"] = "False"
            return selected_ids, debug
        except Exception as exc:
            debug["fallback_reason"] = f"selection_exception:{type(exc).__name__}"
            return None, debug


class RiskAwareV1PreCBFCBF(DetailedCBF):
    def __init__(self, *args: Any, selector: V1CandidateSelector, subset_loader: SubsetGSplatLoader, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.selector = selector
        self.subset_loader = subset_loader
        self.last_selection_debug: dict[str, Any] = {}

    def get_QP_matrices(self, x, u_des, minimal=True):
        subset_ids, debug = self.selector.select(x, u_des)
        self.subset_loader.set_subset(subset_ids)
        try:
            A, l, P, q = super().get_QP_matrices(x, u_des, minimal=minimal)
        finally:
            self.subset_loader.set_subset(None)

        if subset_ids is not None and self.last_active_gaussian_ids is not None:
            local_ids = np.asarray(self.last_active_gaussian_ids, dtype=int)
            valid = (local_ids >= 0) & (local_ids < len(subset_ids))
            mapped = np.full(local_ids.shape, -1, dtype=int)
            mapped[valid] = subset_ids[local_ids[valid]]
            self.last_active_gaussian_ids = mapped
            self.last_mapping_status = f"{self.last_mapping_status}_mapped_from_v1_subset"

        debug["active_constraints_count"] = int(A.shape[0])
        self.last_selection_debug = debug
        return A, l, P, q


class CsvAppender:
    def __init__(self, path: Path, fieldnames: list[str]):
        self.path = path
        self.fieldnames = fieldnames
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists() and self.path.stat().st_size > 0
        self._fh = self.path.open("a", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self._fh, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            self.writer.writeheader()
            self._fh.flush()

    def write(self, row: dict[str, Any]) -> None:
        self.writer.writerow({field: row.get(field, "") for field in self.fieldnames})
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def load_completed_trials(path: Path) -> set[tuple[str, str, int]]:
    if not path.exists():
        return set()
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        return {(r["scene"], r["method"], int(r["trial"])) for r in rows if r.get("trial", "").isdigit()}


def read_trials(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize_trials(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    summaries = []
    keys = sorted({(r.get("scene", ""), r.get("method", "")) for r in rows})
    for scene, method in keys:
        group = [r for r in rows if r.get("scene") == scene and r.get("method") == method]
        safety = [parse_float(r.get("min_safety_h")) for r in group]
        safety = [v for v in safety if v is not None]
        progress = [parse_float(r.get("goal_distance_reduction_ratio")) for r in group]
        final_goal = [parse_float(r.get("final_goal_distance")) for r in group]
        closest_goal = [parse_float(r.get("closest_goal_distance")) for r in group]
        steps = [parse_float(r.get("num_steps")) for r in group]
        runtime = [parse_float(r.get("runtime_mean")) for r in group]
        runtime_p95 = [parse_float(r.get("runtime_p95")) for r in group]
        intervention = [parse_float(r.get("intervention_rate")) for r in group]
        deviation = [parse_float(r.get("control_deviation_mean")) for r in group]
        active = [parse_float(r.get("active_constraints_mean")) for r in group]
        summaries.append(
            {
                "scene": scene,
                "method": method,
                "rows": len(group),
                "success_count": sum(parse_bool(r.get("success")) is True for r in group),
                "collision_count": sum(parse_bool(r.get("collision")) is True for r in group),
                "collision_free_count": sum(parse_bool(r.get("collision_free")) is True for r in group),
                "stopped_before_goal_count": sum(r.get("stop_reason") == "stopped_before_goal" for r in group),
                "solver_failed_count": sum(r.get("stop_reason") == "solver_failed" for r in group),
                "min_safety_h_min": min(safety) if safety else "",
                "min_safety_h_mean": mean_or_blank(safety),
                "goal_distance_reduction_ratio_mean": mean_or_blank([v for v in progress if v is not None]),
                "final_goal_distance_mean": mean_or_blank([v for v in final_goal if v is not None]),
                "closest_goal_distance_mean": mean_or_blank([v for v in closest_goal if v is not None]),
                "num_steps_mean": mean_or_blank([v for v in steps if v is not None]),
                "runtime_mean_mean": mean_or_blank([v for v in runtime if v is not None]),
                "runtime_p95_mean": mean_or_blank([v for v in runtime_p95 if v is not None]),
                "intervention_rate_mean": mean_or_blank([v for v in intervention if v is not None]),
                "control_deviation_mean_mean": mean_or_blank([v for v in deviation if v is not None]),
                "active_constraints_mean_mean": mean_or_blank([v for v in active if v is not None]),
                "qp_infeasible_count_sum": sum(int(float(r.get("qp_infeasible_count") or 0)) for r in group),
            }
        )
    return summaries


def write_summary(output_dir: Path) -> list[dict[str, Any]]:
    rows = read_trials(output_dir / "trials.csv")
    summaries = summarize_trials(rows)
    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)
    return summaries


def write_metrics(output_dir: Path, args: argparse.Namespace, summaries: list[dict[str, Any]]) -> None:
    config: dict[str, Any] = {}
    for key, value in vars(args).items():
        config[key] = str(value) if isinstance(value, Path) else value
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "script": str(Path(__file__).resolve()),
        "config": config,
        "min_safety_h_note": SAFETY_H_NOTE,
        "risk_aware_v1_pre_cbf": {
            "insertion_point": "reproduction-only SubsetGSplatLoader before distance query and CBF matrix construction",
            "actual_insertion_level": "partial_pre_cbf",
            "candidate_budget": args.candidate_budget,
            "near_distance_threshold": args.near_distance_threshold,
            "heading_distance_threshold": args.heading_distance_threshold,
            "heading_cos_threshold": args.heading_cos_threshold,
            "risk_score": args.risk_score,
            "hard_fallback": "keeps near-field, heading-cone, and locally relevant high-active-frequency candidates; falls back to full baseline if the selected subset is too small or selector metadata fails",
        },
        "summary": summaries,
    }
    (output_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_comparison_plot(output_dir: Path) -> None:
    summary_path = output_dir / "summary.csv"
    if not summary_path.exists():
        return
    summary = pd.read_csv(summary_path)
    if summary.empty:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = [
        "collision_count",
        "goal_distance_reduction_ratio_mean",
        "intervention_rate_mean",
        "control_deviation_mean_mean",
        "active_constraints_mean_mean",
        "runtime_mean_mean",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        values = pd.to_numeric(summary[metric], errors="coerce").fillna(0.0)
        ax.bar(summary["method"], values)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(output_dir / "comparison_plot.png", dpi=180)
    plt.close(fig)


def active_rows_for_step(
    *,
    scene: str,
    method: str,
    trial: int,
    step: int,
    x_pre: torch.Tensor,
    u_des: torch.Tensor,
    cbf: DetailedCBF,
    gsplat: GSplatLoader,
    active_log_limit: int,
    near_critical_h: float,
) -> list[dict[str, Any]]:
    if method != "safer_splat_filter" or active_log_limit <= 0:
        return []
    h_values = cbf.last_h_values
    if h_values is None:
        return []
    ids = cbf.last_active_gaussian_ids
    mapping_status = cbf.last_mapping_status
    if ids is None:
        candidate_ids = np.argsort(h_values)[:active_log_limit]
        selected_label = "unknown_mapping_top_low_h_candidates"
    else:
        ids = np.asarray(ids, dtype=int)
        selected_h = h_values[ids]
        candidate_ids = ids[np.argsort(selected_h)[:active_log_limit]]
        selected_label = "True"

    means = gsplat.means.detach().cpu().numpy()
    scales = gsplat.scales.detach().cpu().numpy()
    opacities = gsplat.opacities.detach().cpu().numpy().reshape(-1)
    robot = x_pre[:3].detach().cpu().numpy()
    heading = u_des.detach().cpu().numpy()
    heading_norm = np.linalg.norm(heading)
    rows = []
    for rank, gid in enumerate(candidate_ids):
        gid = int(gid)
        mean = means[gid]
        scale = scales[gid]
        max_scale = float(np.max(scale))
        min_scale = float(np.min(scale))
        vec = mean - robot
        dist = float(np.linalg.norm(vec))
        if heading_norm > 1e-12 and dist > 1e-12:
            heading_alignment = float(np.dot(heading, vec) / (heading_norm * dist))
        else:
            heading_alignment = ""
        rows.append(
            {
                "scene": scene,
                "method": method,
                "trial": trial,
                "step": step,
                "gaussian_id": gid if ids is not None else "",
                "candidate_local_id": gid,
                "candidate_rank": rank,
                "selected_by_baseline": selected_label,
                "is_forced_near_critical": bool_to_csv(float(h_values[gid]) <= near_critical_h),
                "h_value": float(h_values[gid]),
                "distance_or_safety_value": float(h_values[gid]),
                "mean_x": float(mean[0]),
                "mean_y": float(mean[1]),
                "mean_z": float(mean[2]),
                "scale_x": float(scale[0]),
                "scale_y": float(scale[1]),
                "scale_z": float(scale[2]),
                "max_scale": max_scale,
                "anisotropy": max_scale / max(min_scale, 1e-12),
                "opacity": float(opacities[gid]),
                "volume_proxy": float(np.prod(scale)),
                "distance_to_robot": dist,
                "heading_alignment_proxy": heading_alignment,
                "mapping_status": mapping_status,
                "logging_scope": f"lowest_h_selected_constraints_top_{active_log_limit}",
            }
        )
    return rows


def run_trial(
    *,
    args: argparse.Namespace,
    scene: str,
    method: str,
    trial: int,
    scene_cfg: dict[str, Any],
    gsplat: GSplatLoader,
    dynamics: DoubleIntegrator,
    risk_table: RiskScoreTable | None,
    device: torch.device,
    step_writer: CsvAppender,
    active_writer: CsvAppender,
    debug_writer: CsvAppender,
) -> dict[str, Any]:
    alpha = 5.0
    beta = 1.0
    dt = 0.05
    distance_type = "ball-to-ellipsoid"
    x0, xf = make_start_goal_configs(scene_cfg)
    start = x0[trial]
    goal_pos = xf[trial]
    x = torch.tensor(start, device=device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=device, dtype=torch.float32)])
    goal = torch.tensor(goal_pos, device=device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=device, dtype=torch.float32)])
    cbf = None
    if method == "safer_splat_filter":
        cbf = DetailedCBF(gsplat, dynamics, alpha, beta, scene_cfg["radius"], distance_type=distance_type)
    elif method == "risk_aware_v1_pre_cbf":
        if risk_table is None:
            raise ValueError("risk_aware_v1_pre_cbf requires a risk score table")
        subset_loader = SubsetGSplatLoader(gsplat)
        selector = V1CandidateSelector(
            gsplat=gsplat,
            risk_table=risk_table,
            candidate_budget=args.candidate_budget,
            near_distance_threshold=args.near_distance_threshold,
            heading_distance_threshold=args.heading_distance_threshold,
            heading_cos_threshold=args.heading_cos_threshold,
            risk_score_name=args.risk_score,
            min_candidate_budget=args.min_candidate_budget,
        )
        cbf = RiskAwareV1PreCBFCBF(
            subset_loader,
            dynamics,
            alpha,
            beta,
            scene_cfg["radius"],
            distance_type=distance_type,
            selector=selector,
            subset_loader=subset_loader,
        )

    safety_values: list[float] = []
    step_times: list[float] = []
    deviations: list[float] = []
    active_counts: list[int] = []
    positions = [x[:3].detach().cpu().numpy()]
    success = False
    stop_reason = "max_steps"
    start_seconds = time.perf_counter()
    qp_infeasible_count = 0

    for step_idx in range(args.max_steps):
        step = step_idx + 1
        x_pre = x.clone()
        u_des = nominal_control(x, goal)
        cuda_sync(device)
        t0 = time.perf_counter()
        if method == "no_filter":
            u = u_des
            qp_feasible = True
            active_count = 0
        else:
            assert cbf is not None
            u = cbf.solve_QP(x, u_des)
            qp_feasible = bool(cbf.solver_success)
            active_count = int(cbf.last_active_constraints_count)
            selection_debug = dict(getattr(cbf, "last_selection_debug", {}))
        cuda_sync(device)
        runtime_step = time.perf_counter() - t0
        step_times.append(runtime_step)
        active_counts.append(active_count)

        if not qp_feasible:
            success = False
            stop_reason = "solver_failed"
            if cbf is not None:
                qp_infeasible_count = cbf.qp_infeasible_count
            break

        for active_row in active_rows_for_step(
            scene=scene,
            method=method,
            trial=trial,
            step=step,
            x_pre=x_pre,
            u_des=u_des,
            cbf=cbf,
            gsplat=gsplat,
            active_log_limit=args.active_log_limit,
            near_critical_h=0.001,
        ) if cbf is not None else []:
            active_writer.write(active_row)

        x = double_integrator_dynamics(x, u) * dt + x
        h, _, _, _ = gsplat.query_distance(x, radius=scene_cfg["radius"], distance_type=distance_type)
        min_h = float(torch.min(h).detach().cpu().item())
        safety_values.append(min_h)
        positions.append(x[:3].detach().cpu().numpy())
        deviation = float(torch.norm(u - u_des).detach().cpu().item())
        deviations.append(deviation)
        goal_distance = float(torch.norm(x[:3] - goal[:3]).detach().cpu().item())
        u_des_np = u_des.detach().cpu().numpy()
        u_np = u.detach().cpu().numpy()
        x_np = x.detach().cpu().numpy()
        goal_np = goal.detach().cpu().numpy()
        step_writer.write(
            {
                "scene": scene,
                "method": method,
                "trial": trial,
                "step": step,
                "time": step * dt,
                "x": float(x_np[0]),
                "y": float(x_np[1]),
                "z": float(x_np[2]),
                "vx": float(x_np[3]),
                "vy": float(x_np[4]),
                "vz": float(x_np[5]),
                "goal_x": float(goal_np[0]),
                "goal_y": float(goal_np[1]),
                "goal_z": float(goal_np[2]),
                "goal_distance": goal_distance,
                "nominal_u_x": float(u_des_np[0]),
                "nominal_u_y": float(u_des_np[1]),
                "nominal_u_z": float(u_des_np[2]),
                "filtered_u_x": float(u_np[0]),
                "filtered_u_y": float(u_np[1]),
                "filtered_u_z": float(u_np[2]),
                "control_deviation": deviation,
                "min_safety_h_step": min_h,
                "collision_step": bool_to_csv(min_h < 0.0),
                "qp_feasible": bool_to_csv(qp_feasible),
                "runtime_step": runtime_step,
                "active_constraints_count": active_count,
            }
        )
        if method == "risk_aware_v1_pre_cbf":
            debug_row = {field: "" for field in DEBUG_FIELDS}
            debug_row.update(selection_debug)
            debug_row.update(
                {
                    "scene": scene,
                    "trial": trial,
                    "step": step,
                    "min_safety_h_step": min_h,
                    "control_deviation": deviation,
                    "runtime_step": runtime_step,
                    "active_constraints_count": active_count,
                }
            )
            debug_writer.write(debug_row)

        if torch.norm(x - x_pre) < args.goal_tolerance:
            success = bool(torch.norm(x_pre - goal) < args.goal_tolerance)
            stop_reason = "reached_goal" if success else "stopped_before_goal"
            break
        if step_idx >= args.max_steps - 1:
            success = True
            stop_reason = "max_steps_loose_success"

    if cbf is not None:
        qp_infeasible_count = cbf.qp_infeasible_count
    seconds_total = time.perf_counter() - start_seconds
    positions_np = np.asarray(positions, dtype=float)
    goal_pos_np = np.asarray(goal_pos, dtype=float)
    start_np = np.asarray(start, dtype=float)
    final_pos_np = positions_np[-1]
    goal_distances = np.linalg.norm(positions_np - goal_pos_np[None, :], axis=1)
    initial_goal_distance = float(np.linalg.norm(start_np - goal_pos_np))
    final_goal_distance = float(np.linalg.norm(final_pos_np - goal_pos_np))
    goal_distance_reduction = initial_goal_distance - final_goal_distance
    ratio = goal_distance_reduction / initial_goal_distance if initial_goal_distance > 0 else ""
    closest_step = int(np.argmin(goal_distances)) if len(goal_distances) else 0
    min_safety = min(safety_values) if safety_values else ""
    collision = bool(min_safety < 0.0) if min_safety != "" else None
    return {
        "scene": scene,
        "method": method,
        "trial": trial,
        "checkpoint": str(scene_cfg["path_to_gsplat"]),
        "gaussian_count": int(gsplat.means.shape[0]),
        "success": bool_to_csv(success),
        "collision": bool_to_csv(collision),
        "collision_free": bool_to_csv(False if collision is True else (True if collision is False else None)),
        "stop_reason": stop_reason,
        "min_safety_h": min_safety,
        "min_safety_h_note": SAFETY_H_NOTE,
        "goal_distance_reduction_ratio": ratio,
        "initial_goal_distance": initial_goal_distance,
        "final_goal_distance": final_goal_distance,
        "closest_goal_distance": float(goal_distances[closest_step]) if len(goal_distances) else "",
        "closest_goal_step": closest_step,
        "num_steps": len(safety_values),
        "runtime_mean": mean_or_blank(step_times),
        "runtime_p95": percentile(step_times, 95),
        "intervention_rate": mean_or_blank([1.0 if d > 1e-5 else 0.0 for d in deviations]),
        "control_deviation_mean": mean_or_blank(deviations),
        "control_deviation_max": max(deviations) if deviations else "",
        "active_constraints_mean": mean_or_blank(active_counts),
        "active_constraints_p95": percentile(active_counts, 95),
        "qp_infeasible_count": qp_infeasible_count,
        "seconds_total": seconds_total,
        "error": "",
        "success_definition": SUCCESS_DEFINITION,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare no-filter, SAFER-Splat baseline, and risk-aware V1 pre-CBF wrapper.")
    parser.add_argument("--scene", choices=sorted(SCENES), default="stonehenge")
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=["no_filter", "safer_splat_filter", "risk_aware_v1_pre_cbf"])
    parser.add_argument("--trial-start", type=int, default=0)
    parser.add_argument("--trial-end", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--candidate-budget", type=int, default=2000)
    parser.add_argument("--near-distance-threshold", type=float, default=0.08)
    parser.add_argument("--heading-distance-threshold", type=float, default=0.25)
    parser.add_argument("--heading-cos-threshold", type=float, default=0.5)
    parser.add_argument("--risk-score", choices=["risk_v0_active_frequency", "risk_v1_geometry", "risk_v2_hybrid"], default="risk_v2_hybrid")
    parser.add_argument("--risk-score-table", type=Path, default=None)
    parser.add_argument("--goal-tolerance", type=float, default=0.001)
    parser.add_argument("--min-candidate-budget", type=int, default=200)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--active-log-limit", type=int, default=0)
    args = parser.parse_args()

    if args.trial_start < 0 or args.trial_end < args.trial_start or args.trial_end >= 100:
        raise ValueError("trial range must be inclusive within [0, 99]")

    output_dir = args.output_dir or Path(f"work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_{args.scene}")
    if args.risk_score_table is None:
        if args.scene == "stonehenge":
            args.risk_score_table = Path("work/risk_aware_cbf/results/risk_score_table_v0.csv")
        else:
            args.risk_score_table = Path(f"work/risk_aware_cbf/results/{args.scene}_risk_score_table_v0.csv")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = Logger(output_dir / "run_log.txt")
    trial_writer = CsvAppender(output_dir / "trials.csv", TRIAL_FIELDS)
    step_writer = CsvAppender(output_dir / "per_step_trajectory.csv", STEP_FIELDS)
    active_writer = CsvAppender(output_dir / "active_constraints.csv", ACTIVE_FIELDS)
    debug_writer = CsvAppender(output_dir / "v1_candidate_debug.csv", DEBUG_FIELDS)

    try:
        logger.log(f"script={Path(__file__).resolve()}")
        logger.log(f"scene={args.scene} methods={args.methods} trials={args.trial_start}-{args.trial_end}")
        logger.log(
            "risk_aware_v1_pre_cbf="
            f"candidate_budget={args.candidate_budget} "
            f"near_distance_threshold={args.near_distance_threshold} "
            f"heading_distance_threshold={args.heading_distance_threshold} "
            f"heading_cos_threshold={args.heading_cos_threshold} "
            f"risk_score={args.risk_score}"
        )
        scene_cfg = SCENES[args.scene]
        device = torch.device(args.device)
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        gsplat = GSplatLoader(scene_cfg["path_to_gsplat"], device)
        risk_table = None
        if "risk_aware_v1_pre_cbf" in args.methods:
            risk_table = RiskScoreTable(args.risk_score_table, int(gsplat.means.shape[0]))
            logger.log(f"loaded_risk_score_table={args.risk_score_table}")
        dynamics = DoubleIntegrator(device=device, ndim=3)
        completed = load_completed_trials(output_dir / "trials.csv") if args.resume else set()

        for method in args.methods:
            for trial in range(args.trial_start, args.trial_end + 1):
                key = (args.scene, method, trial)
                if args.resume and args.skip_existing and key in completed:
                    logger.log(f"skip_existing method={method} trial={trial}")
                    continue
                logger.log(f"start method={method} trial={trial}")
                try:
                    row = run_trial(
                        args=args,
                        scene=args.scene,
                        method=method,
                        trial=trial,
                        scene_cfg=scene_cfg,
                        gsplat=gsplat,
                        dynamics=dynamics,
                        risk_table=risk_table,
                        device=device,
                        step_writer=step_writer,
                        active_writer=active_writer,
                        debug_writer=debug_writer,
                    )
                    logger.log(
                        f"done method={method} trial={trial} stop={row['stop_reason']} "
                        f"collision={row['collision']} steps={row['num_steps']} "
                        f"min_h={row['min_safety_h']}"
                    )
                except Exception as exc:
                    logger.log(f"error method={method} trial={trial}: {exc!r}")
                    logger.log(traceback.format_exc())
                    row = {field: "" for field in TRIAL_FIELDS}
                    row.update(
                        {
                            "scene": args.scene,
                            "method": method,
                            "trial": trial,
                            "checkpoint": str(scene_cfg["path_to_gsplat"]),
                            "gaussian_count": "",
                            "success": "False",
                            "collision": "",
                            "collision_free": "",
                            "stop_reason": "error",
                            "error": repr(exc),
                            "success_definition": SUCCESS_DEFINITION,
                        }
                    )
                trial_writer.write(row)
                completed.add(key)
                summaries = write_summary(output_dir)
                write_metrics(output_dir, args, summaries)
                write_comparison_plot(output_dir)

        summaries = write_summary(output_dir)
        write_metrics(output_dir, args, summaries)
        write_comparison_plot(output_dir)
        logger.log("final_summary=" + json.dumps(summaries, ensure_ascii=True))
        logger.log(f"wrote={output_dir}")
        return 0
    finally:
        trial_writer.close()
        step_writer.close()
        active_writer.close()
        debug_writer.close()
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
