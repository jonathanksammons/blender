"""Operators for loading and managing reference portrait images."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

from ..core import image_alignment, logging_utils
from ..properties import get_props

log = logging_utils.get_logger("import_references")

_VIEW_ITEMS = [
    ("front", "Front", "Front-facing portrait"),
    ("left", "Left Profile", "Left profile portrait"),
    ("right", "Right Profile", "Right profile portrait"),
]


class PMG_OT_load_reference(Operator):
    """Load a portrait image and create a view-aligned reference plane"""

    bl_idname = "pmg.load_reference"
    bl_label = "Load Reference Image"
    bl_options = {"REGISTER", "UNDO"}

    view: EnumProperty(items=_VIEW_ITEMS, default="front", options={"SKIP_SAVE"})
    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})
    filter_image: bpy.props.BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tga;*.bmp;*.tif;*.tiff;*.exr",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        props = get_props(context)
        if not self.filepath:
            self.report({"ERROR"}, "No image selected.")
            return {"CANCELLED"}
        try:
            image = image_alignment.load_reference_image(self.filepath)
            empty = image_alignment.create_reference_empty(
                context, image, self.view, height=props.ref_height
            )
        except image_alignment.ReferenceError as exc:
            log.error("Reference load failed (%s): %s", self.view, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        setattr(props, f"{self.view}_image_path", self.filepath)
        log.info("Loaded %s reference: %s (%dx%d)", self.view, self.filepath,
                 image.size[0], image.size[1])
        self.report({"INFO"}, f"Loaded {self.view} reference: {empty.name}")

        if self.view == "front":
            _set_front_orthographic(context)
        return {"FINISHED"}


def _set_front_orthographic(context):
    """Snap the active 3D view to front orthographic (Numpad 1 equivalent)."""
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                if region.type == "WINDOW":
                    with context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_axis(type="FRONT", align_active=False)
                    return


class PMG_OT_align_front_view(Operator):
    """Snap the viewport to front orthographic to edit landmarks over the photo"""

    bl_idname = "pmg.align_front_view"
    bl_label = "Front Orthographic View"
    bl_options = {"REGISTER"}

    def execute(self, context):
        _set_front_orthographic(context)
        return {"FINISHED"}


class PMG_OT_reset_alignment(Operator):
    """Reload reference images at their default transforms"""

    bl_idname = "pmg.reset_alignment"
    bl_label = "Reset Reference Alignment"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = get_props(context)
        reloaded = 0
        for view in ("front", "left", "right"):
            path = getattr(props, f"{view}_image_path")
            if not path:
                continue
            try:
                image = image_alignment.load_reference_image(path)
                image_alignment.create_reference_empty(context, image, view, height=props.ref_height)
                reloaded += 1
            except image_alignment.ReferenceError as exc:
                self.report({"WARNING"}, f"{view}: {exc}")
        self.report({"INFO"}, f"Reset {reloaded} reference(s).")
        return {"FINISHED"}


classes = (
    PMG_OT_load_reference,
    PMG_OT_align_front_view,
    PMG_OT_reset_alignment,
)
