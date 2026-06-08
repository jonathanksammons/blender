"""Export section."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..panels.main_panel import PMGPanel
from ..properties import get_props


class PMG_PT_export(PMGPanel, Panel):
    bl_idname = "PMG_PT_export"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)

        layout.prop(props, "export_directory")
        layout.prop(props, "export_format", expand=True)
        layout.prop(props, "export_unity_preset", icon="GHOST_ENABLED")

        box = layout.box()
        box.prop(props, "export_apply_modifiers")
        box.prop(props, "export_triangulate")
        box.prop(props, "export_preserve_shape_keys")
        box.prop(props, "export_include_textures")
        box.prop(props, "export_scale")

        layout.operator("pmg.export_character", icon="EXPORT")


classes = (PMG_PT_export,)
