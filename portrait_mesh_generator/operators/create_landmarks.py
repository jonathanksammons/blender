"""Operators for creating, editing, mirroring and (de)serialising landmarks."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

from ..core import (
    image_alignment,
    landmark_objects as LO,
    landmark_schema,
    landmark_storage,
    logging_utils,
    symmetry,
)
from ..properties import get_props

log = logging_utils.get_logger("create_landmarks")


class PMG_OT_create_landmarks(Operator):
    """Create manually-editable landmark points for the active view"""

    bl_idname = "pmg.create_landmarks"
    bl_label = "Create Manual Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = get_props(context)
        view = props.active_view
        if image_alignment.find_reference_empty(view) is None:
            self.report({"ERROR"}, f"Load the {view} reference image first.")
            return {"CANCELLED"}
        project = landmark_storage.project_from_defaults(props.project_name)
        if view != "front":
            # Profile defaults
            project.views[view] = {
                d.name: landmark_storage.LandmarkPoint(pos=d.default)
                for d in landmark_schema.profile_landmarks()
            }
        try:
            count = LO.create_landmarks_from_project(context, project, view, size=props.landmark_size)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        log.info("Created %d landmarks for %s view", count, view)
        self.report({"INFO"}, f"Created {count} landmarks ({view}).")
        return {"FINISHED"}


class PMG_OT_mirror_landmarks(Operator):
    """Mirror landmarks from one side to the other about the face midline"""

    bl_idname = "pmg.mirror_landmarks"
    bl_label = "Mirror Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    source_side: EnumProperty(
        items=[("L", "Left -> Right", ""), ("R", "Right -> Left", "")],
        default="L",
    )

    def execute(self, context):
        props = get_props(context)
        view = props.active_view
        ref = image_alignment.find_reference_empty(view)
        if ref is None:
            self.report({"ERROR"}, "No reference image for this view.")
            return {"CANCELLED"}
        points = LO.read_points(view)
        if not points:
            self.report({"ERROR"}, "No landmarks to mirror.")
            return {"CANCELLED"}
        mirrored = symmetry.mirror_landmarks(points, source_side=self.source_side)

        by_name = {o.get(LO.PROP_LM_NAME): o for o in LO.iter_landmark_empties(view)}
        moved = 0
        for left, right in landmark_schema.symmetry_pairs(view if view != "front" else "front"):
            dst = right if self.source_side == "L" else left
            if dst in by_name and dst in mirrored:
                obj = by_name[dst]
                if obj.get(LO.PROP_LM_LOCKED, False):
                    continue
                obj.location = image_alignment.normalized_to_world(ref, *mirrored[dst])
                moved += 1
        self.report({"INFO"}, f"Mirrored {moved} landmark(s).")
        return {"FINISHED"}


class PMG_OT_reset_landmarks(Operator):
    """Reset landmarks to schema defaults (selected, category, or all)"""

    bl_idname = "pmg.reset_landmarks"
    bl_label = "Reset Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    mode: EnumProperty(
        items=[("SELECTED", "Selected", ""), ("CATEGORY", "Category", ""), ("ALL", "All", "")],
        default="SELECTED",
    )
    category: StringProperty(default="")

    def execute(self, context):
        props = get_props(context)
        view = props.active_view
        ref = image_alignment.find_reference_empty(view)
        if ref is None:
            self.report({"ERROR"}, "No reference image for this view.")
            return {"CANCELLED"}

        reset = 0
        for obj in LO.iter_landmark_empties(view):
            lname = obj.get(LO.PROP_LM_NAME)
            ldef = landmark_schema.get(lname)
            if ldef is None:
                continue
            if self.mode == "SELECTED" and not obj.select_get():
                continue
            if self.mode == "CATEGORY" and obj.get(LO.PROP_LM_CATEGORY) != self.category:
                continue
            if obj.get(LO.PROP_LM_LOCKED, False):
                continue
            obj.location = image_alignment.normalized_to_world(ref, *ldef.default)
            reset += 1
        self.report({"INFO"}, f"Reset {reset} landmark(s).")
        return {"FINISHED"}


class PMG_OT_toggle_landmark_lock(Operator):
    """Lock or unlock the selected landmarks"""

    bl_idname = "pmg.toggle_landmark_lock"
    bl_label = "Toggle Landmark Lock"
    bl_options = {"REGISTER", "UNDO"}

    lock: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        n = 0
        for obj in LO.iter_landmark_empties():
            if obj.select_get():
                obj[LO.PROP_LM_LOCKED] = self.lock
                obj.lock_location = (self.lock, self.lock, self.lock)
                n += 1
        self.report({"INFO"}, f"{'Locked' if self.lock else 'Unlocked'} {n} landmark(s).")
        return {"FINISHED"}


class PMG_OT_export_landmarks(Operator):
    """Export all landmark views to a versioned JSON file"""

    bl_idname = "pmg.export_landmarks"
    bl_label = "Export Landmark JSON"
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        props = get_props(context)
        if not self.filepath:
            self.filepath = props.landmark_json_path or "//portrait_landmarks.json"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        props = get_props(context)
        project = landmark_storage.LandmarkProject(project_name=props.project_name)
        any_points = False
        for view in ("front", "left", "right"):
            if image_alignment.find_reference_empty(view) is None:
                continue
            snap = LO.read_project(view, props.project_name)
            if snap.views.get(view):
                project.views[view] = snap.views[view]
                any_points = True
        if not any_points:
            self.report({"ERROR"}, "No landmarks to export.")
            return {"CANCELLED"}
        try:
            landmark_storage.save(project, Path(bpy.path.abspath(self.filepath)))
        except OSError as exc:
            self.report({"ERROR"}, f"Could not write file: {exc}")
            return {"CANCELLED"}
        props.landmark_json_path = self.filepath
        log.info("Exported landmarks to %s", self.filepath)
        self.report({"INFO"}, f"Exported landmarks to {self.filepath}")
        return {"FINISHED"}


class PMG_OT_import_landmarks(Operator):
    """Import landmarks from a versioned JSON file"""

    bl_idname = "pmg.import_landmarks"
    bl_label = "Import Landmark JSON"
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        props = get_props(context)
        try:
            project, warnings = landmark_storage.load(Path(bpy.path.abspath(self.filepath)))
        except (FileNotFoundError, landmark_schema.SchemaValidationError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        for w in warnings:
            self.report({"WARNING"}, w)
            log.warning("Import: %s", w)

        created_total = 0
        for view, points in project.views.items():
            if image_alignment.find_reference_empty(view) is None:
                self.report({"WARNING"}, f"No reference for '{view}'; skipped its landmarks.")
                continue
            created_total += LO.create_landmarks_from_project(context, project, view, size=props.landmark_size)
        if created_total == 0:
            self.report({"ERROR"}, "No landmarks imported (load reference images first).")
            return {"CANCELLED"}
        props.landmark_json_path = self.filepath
        self.report({"INFO"}, f"Imported {created_total} landmark(s).")
        return {"FINISHED"}


classes = (
    PMG_OT_create_landmarks,
    PMG_OT_mirror_landmarks,
    PMG_OT_reset_landmarks,
    PMG_OT_toggle_landmark_lock,
    PMG_OT_export_landmarks,
    PMG_OT_import_landmarks,
)
