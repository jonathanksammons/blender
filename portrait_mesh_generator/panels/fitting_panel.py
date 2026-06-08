"""Fit + Refine sections."""

from __future__ import annotations

import bpy
from bpy.types import Panel

from ..panels.main_panel import PMGPanel
from ..properties import get_props


class PMG_PT_fit(PMGPanel, Panel):
    bl_idname = "PMG_PT_fit"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Fit"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)

        col = layout.column(align=True)
        col.operator("pmg.generate_head", text="Generate / Fit Full Head", icon="OUTLINER_OB_ARMATURE")
        col.operator("pmg.fit_front_view", icon="ALIGN_FLUSH")
        col.operator("pmg.fit_profile_view", icon="MOD_THICKNESS")
        col.operator("pmg.reset_fitting", icon="LOOP_BACK")

        box = layout.box()
        box.label(text="Solver")
        box.prop(props, "fit_quality", expand=True)
        box.prop(props, "fit_iterations")
        box.prop(props, "fit_regularization")
        box.prop(props, "fit_symmetry_strength")

        box = layout.box()
        box.label(text="Result")
        box.label(text=f"Status: {props.fit_status}")
        box.label(text=f"Residual: {props.residual_error:.5g}")
        if props.fit_quality_label:
            box.label(text=f"Quality: {props.fit_quality_label}")


_REFINE_SECTIONS = (
    ("Head", "head", ("refine_head_height", "refine_head_width")),
    ("Face / Cheeks", "face", ("refine_cheek_width",)),
    ("Jaw / Chin", "jaw", ("refine_jaw_width", "refine_chin_height")),
    ("Eyes", "eyes", ("refine_eye_spacing",)),
    ("Nose", "nose", ("refine_nose_width", "refine_nose_length")),
    ("Mouth", "mouth", ("refine_mouth_width",)),
)


class PMG_PT_refine(PMGPanel, Panel):
    bl_idname = "PMG_PT_refine"
    bl_parent_id = "PMG_PT_main"
    bl_label = "Refine"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = get_props(context)
        layout.label(text="Live manual adjustment (overrides fit).", icon="MODIFIER")
        for title, section, attrs in _REFINE_SECTIONS:
            box = layout.box()
            row = box.row(align=True)
            row.label(text=title)
            row.operator("pmg.reset_section", text="", icon="LOOP_BACK").section = section
            for attr in attrs:
                box.prop(props, attr, slider=True)


classes = (
    PMG_PT_fit,
    PMG_PT_refine,
)
