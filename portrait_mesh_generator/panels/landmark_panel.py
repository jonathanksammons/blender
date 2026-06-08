"""Landmarks + Measurements sections."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..core import landmark_objects as LO, landmark_schema, measurements as M
from ..panels.main_panel import PMGPanel
from ..properties import get_props


class PMG_PT_landmarks(PMGPanel, Panel):
    bl_idname = "PMG_PT_landmarks"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Landmarks"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)

        layout.prop(props, "active_view", expand=True)

        col = layout.column(align=True)
        col.operator("pmg.create_landmarks", icon="TRACKER")
        col.operator("pmg.auto_detect_landmarks", icon="CAMERA_DATA")

        row = layout.row(align=True)
        row.operator("pmg.mirror_landmarks", text="Mirror L>R", icon="MOD_MIRROR").source_side = "L"
        row.operator("pmg.mirror_landmarks", text="Mirror R>L").source_side = "R"

        box = layout.box()
        box.label(text="Reset", icon="LOOP_BACK")
        row = box.row(align=True)
        row.operator("pmg.reset_landmarks", text="Selected").mode = "SELECTED"
        row.operator("pmg.reset_landmarks", text="All").mode = "ALL"
        row = box.row(align=True)
        row.operator("pmg.toggle_landmark_lock", text="Lock", icon="LOCKED").lock = True
        row.operator("pmg.toggle_landmark_lock", text="Unlock", icon="UNLOCKED").lock = False

        box = layout.box()
        box.label(text="Display")
        box.prop(props, "landmark_size")
        box.prop(props, "show_landmark_names")
        grid = box.grid_flow(columns=3, even_columns=True)
        for cat in landmark_schema.CATEGORIES:
            attr = f"cat_{cat}"
            if hasattr(props, attr):
                grid.prop(props, attr)

        box = layout.box()
        box.label(text="JSON")
        row = box.row(align=True)
        row.operator("pmg.import_landmarks", text="Import", icon="IMPORT")
        row.operator("pmg.export_landmarks", text="Export", icon="EXPORT")

        layout.label(text=f"Count: {LO.count_landmarks(props.active_view)}  "
                          f"avg conf: {LO.average_confidence(props.active_view):.2f}")


class PMG_PT_measurements(PMGPanel, Panel):
    bl_idname = "PMG_PT_measurements"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Measurements"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)
        points = LO.read_points("front")
        if not points:
            layout.label(text="No front landmarks yet.", icon="INFO")
            return
        scale, scale_name = M.reference_scale(points)
        layout.label(text=f"Normalized by: {scale_name}")
        ms = M.compute_measurements(points)
        col = layout.column(align=True)
        for name, m in ms.items():
            row = col.row(align=True)
            if not m.available:
                row.label(text=f"{name}: n/a", icon="BLANK1")
                continue
            icon = "ERROR" if m.clamped else ("MODIFIER" if m.overridden else "BLANK1")
            row.label(text=f"{name}: {m.normalized:.3f}", icon=icon)


classes = (
    PMG_PT_landmarks,
    PMG_PT_measurements,
)
