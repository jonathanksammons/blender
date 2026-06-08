"""Export the fitted head for Unity (FBX/glTF).

Exports a *duplicate* so the working source mesh is never destructively altered.
Helper objects (references, landmarks, controllers) are excluded. Transforms are
applied on the duplicate; the original is untouched.
"""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.types import Operator

from ..core import deformation_solver, logging_utils
from ..properties import get_props

log = logging_utils.get_logger("export")


def _prepare_export_copy(context, props):
    """Return a temporary duplicate object prepared for export."""
    working, _ = deformation_solver.get_working_and_source()
    if working is None:
        raise RuntimeError("No fitted head to export.")

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = working.evaluated_get(depsgraph) if props.export_apply_modifiers else working
    mesh = bpy.data.meshes.new_from_object(
        eval_obj, preserve_all_data_layers=True, depsgraph=depsgraph
    )
    dup = bpy.data.objects.new(working.name + "_EXPORT", mesh)
    context.scene.collection.objects.link(dup)

    # Apply transform on the duplicate only.
    dup.matrix_world = working.matrix_world.copy()
    dup.select_set(True)
    context.view_layer.objects.active = dup
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if props.export_triangulate:
        mod = dup.modifiers.new("PMG_Tri", "TRIANGULATE")
        mod.quad_method = "BEAUTY"
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return dup


class PMG_OT_export_character(Operator):
    """Export the fitted head as FBX or glTF (Unity-friendly)"""

    bl_idname = "pmg.export_character"
    bl_label = "Export Character"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = get_props(context)
        out_dir = Path(bpy.path.abspath(props.export_directory)) if props.export_directory else None
        if not out_dir:
            self.report({"ERROR"}, "Set an output directory first.")
            return {"CANCELLED"}
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.report({"ERROR"}, f"Output directory not writable: {exc}")
            return {"CANCELLED"}

        # Deselect everything; we export only the prepared duplicate.
        for obj in context.selected_objects:
            obj.select_set(False)

        try:
            dup = _prepare_export_copy(context, props)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        name = bpy.path.clean_name(props.project_name) or "portrait_head"
        try:
            if props.export_format == "FBX":
                path = out_dir / f"{name}.fbx"
                result = self._export_fbx(path, props)
            else:
                path = out_dir / f"{name}.glb"
                result = self._export_gltf(path, props)
        except Exception as exc:  # noqa: BLE001 - report any exporter failure clearly
            log.error("Export failed: %s", exc)
            self.report({"ERROR"}, f"Export failed: {exc}")
            result = False
        finally:
            bpy.data.objects.remove(dup, do_unlink=True)

        if not result:
            return {"CANCELLED"}
        log.info("Exported %s to %s", props.export_format, path)
        self.report({"INFO"}, f"Exported {props.export_format}: {path}")
        return {"FINISHED"}

    def _export_fbx(self, path: Path, props) -> bool:
        if not hasattr(bpy.ops.export_scene, "fbx"):
            self.report({"ERROR"}, "FBX exporter not available. Enable the FBX I/O add-on.")
            return False
        kwargs = dict(
            filepath=str(path),
            use_selection=True,
            object_types={"MESH"},
            mesh_smooth_type="FACE",
            add_leaf_bones=False,
            bake_anim=False,
        )
        if props.export_unity_preset:
            kwargs.update(
                apply_scale_options="FBX_SCALE_ALL",
                axis_forward="-Z",
                axis_up="Y",
                global_scale=props.export_scale,
            )
        bpy.ops.export_scene.fbx(**kwargs)
        return True

    def _export_gltf(self, path: Path, props) -> bool:
        if not hasattr(bpy.ops.export_scene, "gltf"):
            self.report({"ERROR"}, "glTF exporter not available. Enable the glTF I/O add-on.")
            return False
        bpy.ops.export_scene.gltf(
            filepath=str(path),
            export_format="GLB",
            use_selection=True,
            export_apply=False,
            export_yup=True,
        )
        return True


classes = (PMG_OT_export_character,)
