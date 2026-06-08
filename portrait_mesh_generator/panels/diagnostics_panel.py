"""Diagnostics section."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..addon_info import (
    BASE_MESH_VERSION,
    LANDMARK_SCHEMA_VERSION,
    addon_version_string,
)
from ..core import (
    dependency_manager,
    deformation_solver,
    landmark_objects as LO,
    logging_utils,
    mesh_validation,
)
from ..panels.main_panel import PMGPanel
from ..preferences import get_preferences
from ..properties import get_props


class PMG_PT_diagnostics(PMGPanel, Panel):
    bl_idname = "PMG_PT_diagnostics"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Diagnostics"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)

        col = layout.column(align=True)
        col.label(text=f"Blender: {bpy.app.version_string}")
        col.label(text=f"Add-on: {addon_version_string()}")
        col.label(text=f"Base mesh ver: {BASE_MESH_VERSION}")
        col.label(text=f"Schema ver: {LANDMARK_SCHEMA_VERSION}")

        prefs = get_preferences(context)
        report = dependency_manager.build_report(prefs.external_python_path or None)
        layout.label(
            text=f"Detector: {'available' if report.detector_available else 'unavailable'}",
            icon="CHECKMARK" if report.detector_available else "X",
        )
        layout.label(text="Manual mode: always usable", icon="CHECKMARK")

        box = layout.box()
        box.label(text="Scene")
        for view in ("front", "left", "right"):
            from ..core import image_alignment
            present = image_alignment.find_reference_empty(view) is not None
            box.label(text=f"  {view} image: {'yes' if present else 'no'}")
        box.label(text=f"  landmarks: {LO.count_landmarks()}")
        box.label(text=f"  avg confidence: {LO.average_confidence():.2f}")

        working, _ = deformation_solver.get_working_and_source()
        if working is not None:
            res = mesh_validation.validate_object(working)
            box.label(text=f"  mesh: {'valid' if res.ok else 'INVALID'}",
                      icon="CHECKMARK" if res.ok else "ERROR")
            box.label(text=f"  verts: {res.vertex_count}  uv: {'yes' if res.has_uvs else 'no'}")
        else:
            box.label(text="  mesh: not loaded")

        box.label(text=f"  residual: {props.residual_error:.5g}")

        layout.operator("pmg.run_diagnostics", icon="INFO")
        layout.label(text=f"Log: {logging_utils.get_log_file().name}", icon="TEXT")


classes = (PMG_PT_diagnostics,)
