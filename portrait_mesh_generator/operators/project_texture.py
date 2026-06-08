"""Texture operators.

'Create Material' is fully implemented (Principled BSDF using the front image on
the head's UVs). Camera-based projection/blending is Phase 7 and the relevant
operators report that honestly instead of pretending.
"""

from __future__ import annotations

import bpy
from bpy.types import Operator

from ..core import deformation_solver, image_alignment, logging_utils, texture_projection
from ..properties import get_props

log = logging_utils.get_logger("project_texture")


class PMG_OT_create_material(Operator):
    """Create a Principled BSDF material using the front reference image"""

    bl_idname = "pmg.create_material"
    bl_label = "Create Material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        working, _ = deformation_solver.get_working_and_source()
        if working is None:
            self.report({"ERROR"}, "Load/generate the head first.")
            return {"CANCELLED"}
        ref = image_alignment.find_reference_empty("front")
        image = ref.data if (ref is not None and ref.type == "EMPTY") else None
        mat = texture_projection.create_principled_material(working, image)
        log.info("Created material '%s' (image=%s)", mat.name, bool(image))
        self.report({"INFO"}, f"Material '{mat.name}' created.")
        return {"FINISHED"}


class PMG_OT_project_texture(Operator):
    """Project reference photos onto the head (Phase 7 - not implemented)"""

    bl_idname = "pmg.project_texture"
    bl_label = "Project Textures"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            texture_projection.project_front_texture()
        except NotImplementedError as exc:
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


classes = (
    PMG_OT_create_material,
    PMG_OT_project_texture,
)
