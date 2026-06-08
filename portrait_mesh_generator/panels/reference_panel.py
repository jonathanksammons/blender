"""References section."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..core import image_alignment
from ..panels.main_panel import PMGPanel
from ..properties import get_props


class PMG_PT_references(PMGPanel, Panel):
    bl_idname = "PMG_PT_references"
    bl_parent_id = "PMG_PT_main"
    bl_label = "References"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)

        layout.prop(props, "ref_height")
        for view, label, op_icon, op_prop, vis_prop in (
            ("front", "Front", "IMAGE_REFERENCE", "front_opacity", "show_front"),
            ("left", "Left", "TRIA_LEFT", "left_opacity", "show_left"),
            ("right", "Right", "TRIA_RIGHT", "right_opacity", "show_right"),
        ):
            box = layout.box()
            row = box.row(align=True)
            op = row.operator("pmg.load_reference", text=f"Load {label}", icon=op_icon)
            op.view = view
            present = image_alignment.find_reference_empty(view) is not None
            row.label(text="", icon="CHECKMARK" if present else "BLANK1")
            if present:
                r2 = box.row(align=True)
                r2.prop(props, vis_prop, text="", icon="HIDE_OFF")
                r2.prop(props, op_prop, slider=True)

        row = layout.row(align=True)
        row.operator("pmg.align_front_view", icon="VIEW_CAMERA")
        row.operator("pmg.reset_alignment", icon="FILE_REFRESH")


classes = (PMG_PT_references,)
