"""Front-view fitting operator.

Reads the current front landmarks, computes normalized measurements, solves for
bounded deformation parameters and applies them to the working head. The result
is written into the Refine sliders, which are the single source of truth for the
head's shape (so manual refinement and Reset behave predictably).
"""

from __future__ import annotations

import bpy
from bpy.types import Operator

from ..core import (
    deformation_solver,
    fitting_solver,
    landmark_objects as LO,
    logging_utils,
    measurements as M,
)
from ..properties import get_props

log = logging_utils.get_logger("fit_front_view")

# Landmarks that must be present for a meaningful fit.
REQUIRED = ("pupil_l", "pupil_r", "cheekbone_l", "cheekbone_r", "skull_top", "chin")


def compute_front_measurements(context):
    """Return (measurements, points) for the current front landmarks."""
    points = LO.read_points("front")
    return M.compute_measurements(points), points


class PMG_OT_fit_front_view(Operator):
    """Fit the head to the front-view landmarks"""

    bl_idname = "pmg.fit_front_view"
    bl_label = "Fit Front View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = get_props(context)
        working, source = deformation_solver.get_working_and_source()
        if working is None or source is None:
            self.report({"ERROR"}, "Load the base head first.")
            return {"CANCELLED"}

        points = LO.read_points("front")
        if not points:
            self.report({"ERROR"}, "No front landmarks found. Create landmarks first.")
            return {"CANCELLED"}
        missing = [n for n in REQUIRED if n not in points]
        if missing:
            self.report({"ERROR"}, f"Missing required landmarks: {', '.join(missing)}")
            return {"CANCELLED"}

        measurements = M.compute_measurements(points)

        # Solver settings, with quality preset overrides.
        try:
            profile = fitting_solver.load_profile()
        except OSError:
            profile = {}
        weights = profile.get("weights")
        regularization = props.fit_regularization
        max_iter = props.fit_iterations
        preset = profile.get("quality_presets", {}).get(props.fit_quality, {})
        max_iter = preset.get("max_iterations", max_iter)
        regularization = preset.get("regularization", regularization)

        result = fitting_solver.solve(
            measurements,
            weights=weights,
            regularization=regularization,
            max_iterations=max_iter,
            symmetry_strength=props.fit_symmetry_strength,
        )

        # Write into refine sliders (this also live-applies the deformation),
        # then apply once more explicitly to be deterministic.
        props.set_refine_from_params(result.params)
        deformation_solver.apply_params(result.params)

        props.residual_error = result.residual
        props.fit_quality_label = result.quality_label()
        props.fit_status = (
            f"{'converged' if result.converged else 'max-iter'} "
            f"in {result.iterations} iters"
        )

        # Report clamping honestly.
        clamped_meas = [m.name for m in measurements.values() if m.clamped]
        if clamped_meas:
            self.report({"WARNING"}, f"Clamped measurements: {', '.join(clamped_meas)}")
        if result.clamped_params:
            self.report({"WARNING"}, f"Clamped parameters: {', '.join(result.clamped_params)}")
        if result.skipped_params:
            log.info("Skipped params (missing data): %s", result.skipped_params)

        log.info(
            "Front fit: residual=%.6g iters=%d converged=%s params=%s",
            result.residual, result.iterations, result.converged,
            {k: round(v, 3) for k, v in result.params.items()},
        )
        self.report(
            {"INFO"},
            f"Fit {result.quality_label()} (residual {result.residual:.4g}, "
            f"{result.iterations} iters).",
        )
        return {"FINISHED"}


classes = (PMG_OT_fit_front_view,)
