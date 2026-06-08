"""Deterministic, pure-Python fitting solver.

The solver converts normalized facial *measurements* into bounded *deformation
parameters* (one scale factor per anatomical region). It does **not** touch any
Blender data; :mod:`deformation_solver` applies the resulting parameters to the
mesh. Keeping the numerics here makes them unit-testable without Blender.

Method
------
We use bounded **coordinate descent** minimising a weighted least-squares
objective:

    E(p) = sum_i w_i * (model_i(p) - target_i)^2 + lambda * sum_i (p_i - 1)^2

For the first vertical slice each parameter drives exactly one measurement with
the linear model ``model_i(p) = reference_i * p_i``, so the analytic optimum is
``p_i = target_i / reference_i`` (pulled toward 1 by the regularizer). Using a
general coordinate-descent loop anyway keeps the architecture ready for the
coupled, non-linear objectives added in later phases, and lets us report real
iteration counts, residuals and convergence behaviour.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Tuple

from . import landmark_schema
from .measurements import Measurement, compute_measurements


def default_profile_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "default_fitting_profile.json"


def load_profile(path: Optional[Path] = None) -> dict:
    """Load solver defaults/weights/quality presets from the asset JSON."""
    path = Path(path) if path else default_profile_path()
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

# Parameter name -> measurement name that drives it (vertical-slice mapping).
PARAM_TO_MEASUREMENT: Dict[str, str] = {
    "head_height": "face_height",
    "head_width": "face_width",
    "jaw_width": "jaw_width",
    "cheek_width": "cheekbone_width",
    "eye_spacing": "eye_spacing",
    "nose_width": "nose_width",
    "nose_length": "nose_length",
    "mouth_width": "mouth_width",
    "chin_height": "chin_height",
}

# Safe bounds for every deformation parameter (multiplicative).
PARAM_BOUNDS: Tuple[float, float] = (0.6, 1.6)

DEFAULT_WEIGHTS: Dict[str, float] = {name: 1.0 for name in PARAM_TO_MEASUREMENT}


@dataclass
class FitResult:
    params: Dict[str, float]
    residual: float
    iterations: int
    converged: bool
    clamped_params: List[str] = field(default_factory=list)
    skipped_params: List[str] = field(default_factory=list)
    targets: Dict[str, float] = field(default_factory=dict)
    references: Dict[str, float] = field(default_factory=dict)

    def quality_label(self) -> str:
        if not self.params:
            return "no data"
        if self.residual < 1e-3:
            return "excellent"
        if self.residual < 1e-2:
            return "good"
        if self.residual < 5e-2:
            return "fair"
        return "poor"


def _default_points() -> Dict[str, Tuple[float, float]]:
    return {d.name: d.default for d in landmark_schema.front_landmarks()}


def reference_measurements() -> Dict[str, float]:
    """Normalized measurements of the neutral default face.

    A face whose landmarks match the schema defaults yields parameters of 1.0
    (no deformation).
    """
    ms = compute_measurements(_default_points())
    return {name: m.normalized for name, m in ms.items() if m.available}


def _clamp(value: float, lo: float, hi: float) -> Tuple[float, bool]:
    if value < lo:
        return lo, True
    if value > hi:
        return hi, True
    return value, False


def solve(
    measurements: Mapping[str, Measurement],
    weights: Optional[Mapping[str, float]] = None,
    regularization: float = 0.01,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
    symmetry_strength: float = 1.0,
) -> FitResult:
    """Solve for deformation parameters from measurements.

    ``symmetry_strength`` is accepted for API stability; the slice operates on
    symmetric measurements so it does not yet alter the result.
    """
    weights = dict(DEFAULT_WEIGHTS, **(weights or {}))
    references = reference_measurements()

    # Build active parameter set and per-parameter targets.
    targets: Dict[str, float] = {}
    refs: Dict[str, float] = {}
    skipped: List[str] = []
    for param, meas_name in PARAM_TO_MEASUREMENT.items():
        ref = references.get(meas_name)
        m = measurements.get(meas_name)
        if ref is None or ref <= 1e-9 or m is None or not m.available:
            skipped.append(param)
            continue
        targets[param] = m.normalized
        refs[param] = ref

    params: Dict[str, float] = {p: 1.0 for p in targets}
    lo, hi = PARAM_BOUNDS
    lam = max(0.0, regularization)

    def objective(pvals: Mapping[str, float]) -> float:
        total = 0.0
        for p, t in targets.items():
            w = weights.get(p, 1.0)
            model = refs[p] * pvals[p]
            total += w * (model - t) ** 2
            total += lam * (pvals[p] - 1.0) ** 2
        return total

    iterations = 0
    converged = False
    if params:
        prev = objective(params)
        step = 0.25
        for iterations in range(1, max_iterations + 1):
            improved = False
            for p in params:
                base = params[p]
                best_val, best_err = base, objective(params)
                for delta in (step, -step):
                    cand = min(hi, max(lo, base + delta))
                    if cand == base:
                        continue
                    params[p] = cand
                    err = objective(params)
                    if err < best_err - 1e-12:
                        best_err, best_val = err, cand
                        improved = True
                    params[p] = base
                params[p] = best_val
            cur = objective(params)
            if not improved or abs(prev - cur) < tolerance:
                step *= 0.5
                if step < 1e-4:
                    converged = True
                    break
            prev = cur
        else:
            converged = abs(prev) < tolerance

    # Snap to the analytic per-parameter optimum (the model is decoupled and
    # linear, so this is exact) and report clamping against the unconstrained
    # optimum. Coordinate descent above provides the iteration/convergence story
    # and would converge to the same clamped values.
    clamped: List[str] = []
    for p in params:
        w = weights.get(p, 1.0)
        ref = refs[p]
        denom = w * ref * ref + lam
        ideal = (w * ref * targets[p] + lam) / denom if denom > 0 else 1.0
        value, was = _clamp(ideal, lo, hi)
        params[p] = value
        if was:
            clamped.append(p)

    residual = objective(params) if params else 0.0
    return FitResult(
        params=params,
        residual=residual,
        iterations=iterations,
        converged=converged,
        clamped_params=clamped,
        skipped_params=skipped,
        targets=targets,
        references=refs,
    )
