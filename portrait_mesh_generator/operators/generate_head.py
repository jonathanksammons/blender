"""Operators for loading/validating the base head and generating the fitted head."""

from __future__ import annotations

import bpy
from bpy.types import Operator

from ..core import base_head, deformation_solver, logging_utils, mesh_validation
from ..properties import get_props

log = logging_utils.get_logger("generate_head")


def _get_output_collection(context, name: str):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        context.scene.collection.children.link(coll)
    return coll


def ensure_base_loaded(context):
    """Return (working, source), creating them if necessary."""
    working, source = deformation_solver.get_working_and_source()
    if working is not None and source is not None:
        return working, source
    raise RuntimeError("Base head not loaded. Use 'Load Base Head' first.")


class PMG_OT_load_base_head(Operator):
    """Load (or generate) the standardized base head and a working copy"""

    bl_idname = "pmg.load_base_head"
    bl_label = "Load Base Head"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = get_props(context)
        coll = _get_output_collection(context, props.output_collection)

        # Remove any previous source/working to keep generation reproducible.
        for name in (base_head.BASE_HEAD_NAME, base_head.WORKING_HEAD_NAME):
            old = bpy.data.objects.get(name)
            if old is not None:
                bpy.data.objects.remove(old, do_unlink=True)

        source, origin = base_head.load_or_create_base(scale=props.working_scale)
        source.name = base_head.BASE_HEAD_NAME
        coll.objects.link(source)
        source.hide_viewport = True
        source.hide_render = True
        props.base_head_source = origin

        # Working copy shares no mesh data with the source.
        work_mesh = source.data.copy()
        working = bpy.data.objects.new(base_head.WORKING_HEAD_NAME, work_mesh)
        working[base_head.PROP_IS_WORKING] = True
        working[base_head.PROP_MESH_VERSION] = source.get(base_head.PROP_MESH_VERSION)
        coll.objects.link(working)

        result = mesh_validation.validate_object(working)
        log.info("Loaded base head (%s). %s", origin, result.summary())
        if not result.ok:
            for e in result.errors:
                self.report({"WARNING"}, e)
        self.report({"INFO"}, f"Base head loaded ({origin}); {result.vertex_count} verts.")
        return {"FINISHED"}


class PMG_OT_validate_base_head(Operator):
    """Validate the working head topology, UVs and version"""

    bl_idname = "pmg.validate_base_head"
    bl_label = "Validate Base Head"
    bl_options = {"REGISTER"}

    def execute(self, context):
        working, _ = deformation_solver.get_working_and_source()
        if working is None:
            self.report({"ERROR"}, "No base head loaded.")
            return {"CANCELLED"}
        result = mesh_validation.validate_object(working)
        log.info("Validation: %s", result.summary())
        level = "INFO" if result.ok else "WARNING"
        self.report({level}, result.summary())
        for msg in result.errors + result.warnings:
            self.report({"WARNING"}, msg)
        return {"FINISHED"}


class PMG_OT_generate_head(Operator):
    """Generate the fitted head: load base if needed, then fit to landmarks"""

    bl_idname = "pmg.generate_head"
    bl_label = "Generate / Fit Full Head"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        working, source = deformation_solver.get_working_and_source()
        if working is None or source is None:
            bpy.ops.pmg.load_base_head()
        # Delegate the actual fit to the front-view fit operator.
        return bpy.ops.pmg.fit_front_view()


classes = (
    PMG_OT_load_base_head,
    PMG_OT_validate_base_head,
    PMG_OT_generate_head,
)
