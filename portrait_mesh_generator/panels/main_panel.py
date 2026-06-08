"""Root panel + Setup section."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..core import ui_theme
from ..properties import get_props


class PMGPanel:
    """Mixin with shared panel placement in the 3D View sidebar."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_theme.PANEL_CATEGORY


class PMG_PT_main(PMGPanel, Panel):
    bl_idname = "PMG_PT_main"
    bl_label = "PortraitMesh"

    def draw(self, context):
        layout = self.layout
        props = get_props(context)

        col = layout.column(align=True)
        col.prop(props, "project_name")
        col.prop(props, "working_scale")

        row = layout.row(align=True)
        row.prop(props, "use_symmetry", toggle=True, icon="MOD_MIRROR")
        row.prop(props, "preserve_source", toggle=True, icon="MESH_DATA")

        box = layout.box()
        box.label(text="Setup", icon="TOOL_SETTINGS")
        box.prop(props, "output_collection")
        col = box.column(align=True)
        col.operator("pmg.load_base_head", icon="MESH_MONKEY")
        col.operator("pmg.validate_base_head", icon="CHECKMARK")
        if props.base_head_source:
            box.label(text=f"Base source: {props.base_head_source}", icon="INFO")


classes = (PMG_PT_main,)
