"""Texture section."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..panels.main_panel import PMGPanel


class PMG_PT_texture(PMGPanel, Panel):
    bl_idname = "PMG_PT_texture"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Texture"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator("pmg.create_material", icon="MATERIAL")
        col = layout.column(align=True)
        col.enabled = True
        col.operator("pmg.project_texture", icon="MOD_UVPROJECT")
        layout.label(text="Full projection: Phase 7 (not yet).", icon="INFO")
        layout.label(text="Hair must be created separately.", icon="INFO")


classes = (PMG_PT_texture,)
