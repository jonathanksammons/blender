"""Operators that reset the fitting back toward the neutral base shape."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..core import deformation_solver, logging_utils
from ..properties import REFINE_PARAMS, get_props

log = logging_utils.get_logger("reset_fitting")

# Refine parameters grouped by Refine-panel section.
SECTIONS = {
    "head": ("head_height", "head_width"),
    "face": ("cheek_width",),
    "jaw": ("jaw_width", "chin_height"),
    "eyes": ("eye_spacing",),
    "nose": ("nose_width", "nose_length"),
    "mouth": ("mouth_width",),
}


class PMG_OT_reset_fitting(Operator):
    """Reset all fitting parameters and restore the neutral base shape"""

    bl_idname = "pmg.reset_fitting"
    bl_label = "Reset Fit"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = get_props(context)
        working, source = deformation_solver.get_working_and_source()
        if working is None or source is None:
            self.report({"ERROR"}, "No head to reset.")
            return {"CANCELLED"}
        props.reset_refine()
        # reset_refine triggers updates, but apply identity explicitly too.
        deformation_solver.apply_params({n: 1.0 for n in REFINE_PARAMS})
        props.residual_error = 0.0
        props.fit_status = "reset"
        props.fit_quality_label = ""
        log.info("Fitting reset to neutral base.")
        self.report({"INFO"}, "Fit reset to neutral base shape.")
        return {"FINISHED"}


class PMG_OT_reset_section(Operator):
    """Reset one Refine section to neutral"""

    bl_idname = "pmg.reset_section"
    bl_label = "Reset Section"
    bl_options = {"REGISTER", "UNDO"}

    section: StringProperty(default="head")

    def execute(self, context):
        props = get_props(context)
        names = SECTIONS.get(self.section, ())
        for name in names:
            setattr(props, f"refine_{name}", 1.0)
        self.report({"INFO"}, f"Reset section '{self.section}'.")
        return {"FINISHED"}


classes = (
    PMG_OT_reset_fitting,
    PMG_OT_reset_section,
)
