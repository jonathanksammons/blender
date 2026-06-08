"""Blender PropertyGroup definitions.

Per the project coding rules, PropertyGroup *data* is kept separate from fitting
*logic*: these properties only hold state and small UI-update callbacks. All
numerics live in :mod:`core`.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from .core import deformation_solver, image_alignment, landmark_objects

# Names of the nine slice deformation parameters, in UI order.
REFINE_PARAMS = (
    "head_height",
    "head_width",
    "cheek_width",
    "jaw_width",
    "chin_height",
    "eye_spacing",
    "nose_width",
    "nose_length",
    "mouth_width",
)


def _refine_params_dict(props) -> dict:
    return {name: getattr(props, f"refine_{name}") for name in REFINE_PARAMS}


def _refine_update(self, context):
    """Live-apply refine sliders to the working head (guarded no-op if absent)."""
    try:
        deformation_solver.apply_params(_refine_params_dict(self))
    except Exception:
        # Never raise from a property update; diagnostics surface real errors.
        pass


def _opacity_update(self, context):
    for view, attr in (("front", "front_opacity"), ("left", "left_opacity"), ("right", "right_opacity")):
        ref = image_alignment.find_reference_empty(view)
        if ref is not None:
            ref.color = (1.0, 1.0, 1.0, float(getattr(self, attr)))
            ref.use_empty_image_alpha = True


def _visibility_update(self, context):
    for view, attr in (("front", "show_front"), ("left", "show_left"), ("right", "show_right")):
        ref = image_alignment.find_reference_empty(view)
        if ref is not None:
            ref.hide_viewport = not bool(getattr(self, attr))


def _landmark_size_update(self, context):
    for obj in landmark_objects.iter_landmark_empties():
        obj.empty_display_size = float(self.landmark_size)


def _landmark_names_update(self, context):
    for obj in landmark_objects.iter_landmark_empties():
        obj.show_name = bool(self.show_landmark_names)


def _category_visibility_update(self, context):
    mapping = {
        "skull": self.cat_skull, "jaw": self.cat_jaw, "eyes": self.cat_eyes,
        "brows": self.cat_brows, "nose": self.cat_nose, "mouth": self.cat_mouth,
        "ears": self.cat_ears, "neck": self.cat_neck, "profile": self.cat_profile,
    }
    for obj in landmark_objects.iter_landmark_empties():
        cat = obj.get(landmark_objects.PROP_LM_CATEGORY, "skull")
        obj.hide_viewport = not bool(mapping.get(cat, True))


def _refine_prop(name: str, label: str) -> FloatProperty:
    return FloatProperty(
        name=label, default=1.0, min=0.6, max=1.6, soft_min=0.7, soft_max=1.4,
        precision=3, update=_refine_update,
    )


class PMG_Properties(PropertyGroup):
    # --- Setup ---------------------------------------------------------
    project_name: StringProperty(name="Project", default="PortraitMesh Project")
    working_scale: FloatProperty(name="Working Scale", default=1.0, min=0.01, max=100.0)
    use_symmetry: BoolProperty(name="Symmetry", default=True)
    preserve_source: BoolProperty(name="Preserve Source Mesh", default=True)
    output_collection: StringProperty(name="Output Collection", default="PortraitMesh")
    base_head_source: StringProperty(name="Base Head Source", default="")

    # --- References ----------------------------------------------------
    front_image_path: StringProperty(name="Front", subtype="FILE_PATH")
    left_image_path: StringProperty(name="Left", subtype="FILE_PATH")
    right_image_path: StringProperty(name="Right", subtype="FILE_PATH")
    ref_height: FloatProperty(name="Reference Height", default=0.30, min=0.05, max=5.0)
    front_opacity: FloatProperty(name="Front Opacity", default=1.0, min=0.0, max=1.0, update=_opacity_update)
    left_opacity: FloatProperty(name="Left Opacity", default=1.0, min=0.0, max=1.0, update=_opacity_update)
    right_opacity: FloatProperty(name="Right Opacity", default=1.0, min=0.0, max=1.0, update=_opacity_update)
    show_front: BoolProperty(name="Show Front", default=True, update=_visibility_update)
    show_left: BoolProperty(name="Show Left", default=True, update=_visibility_update)
    show_right: BoolProperty(name="Show Right", default=True, update=_visibility_update)

    # --- Landmarks -----------------------------------------------------
    active_view: EnumProperty(
        name="View",
        items=[("front", "Front", ""), ("left", "Left", ""), ("right", "Right", "")],
        default="front",
    )
    landmark_size: FloatProperty(name="Size", default=0.004, min=0.0005, max=0.05, update=_landmark_size_update)
    show_landmark_names: BoolProperty(name="Show Names", default=False, update=_landmark_names_update)
    landmark_json_path: StringProperty(name="Landmark JSON", subtype="FILE_PATH")

    cat_skull: BoolProperty(name="Skull", default=True, update=_category_visibility_update)
    cat_jaw: BoolProperty(name="Jaw", default=True, update=_category_visibility_update)
    cat_eyes: BoolProperty(name="Eyes", default=True, update=_category_visibility_update)
    cat_brows: BoolProperty(name="Brows", default=True, update=_category_visibility_update)
    cat_nose: BoolProperty(name="Nose", default=True, update=_category_visibility_update)
    cat_mouth: BoolProperty(name="Mouth", default=True, update=_category_visibility_update)
    cat_ears: BoolProperty(name="Ears", default=True, update=_category_visibility_update)
    cat_neck: BoolProperty(name="Neck", default=True, update=_category_visibility_update)
    cat_profile: BoolProperty(name="Profile", default=True, update=_category_visibility_update)

    # --- Fit -----------------------------------------------------------
    fit_iterations: IntProperty(name="Max Iterations", default=50, min=1, max=500)
    fit_regularization: FloatProperty(name="Regularization", default=0.01, min=0.0, max=1.0)
    fit_symmetry_strength: FloatProperty(name="Symmetry Strength", default=1.0, min=0.0, max=1.0)
    fit_quality: EnumProperty(
        name="Quality",
        items=[("preview", "Preview", "Fast, fewer iterations"),
               ("final", "Final", "Higher quality")],
        default="final",
    )
    residual_error: FloatProperty(name="Residual", default=0.0)
    fit_status: StringProperty(name="Status", default="not fitted")
    fit_quality_label: StringProperty(name="Quality", default="")

    # --- Refine (live multipliers; also the source of truth for shape) --
    refine_head_height: _refine_prop("head_height", "Head Height")
    refine_head_width: _refine_prop("head_width", "Head Width")
    refine_cheek_width: _refine_prop("cheek_width", "Cheek Width")
    refine_jaw_width: _refine_prop("jaw_width", "Jaw Width")
    refine_chin_height: _refine_prop("chin_height", "Chin Height")
    refine_eye_spacing: _refine_prop("eye_spacing", "Eye Spacing")
    refine_nose_width: _refine_prop("nose_width", "Nose Width")
    refine_nose_length: _refine_prop("nose_length", "Nose Length")
    refine_mouth_width: _refine_prop("mouth_width", "Mouth Width")

    # --- Export --------------------------------------------------------
    export_directory: StringProperty(name="Output Dir", subtype="DIR_PATH")
    export_format: EnumProperty(
        name="Format",
        items=[("FBX", "FBX", "Autodesk FBX"), ("GLTF", "glTF", "glTF 2.0")],
        default="FBX",
    )
    export_unity_preset: BoolProperty(name="Unity Preset", default=True)
    export_apply_modifiers: BoolProperty(name="Apply Modifiers", default=True)
    export_preserve_shape_keys: BoolProperty(name="Preserve Shape Keys", default=False)
    export_triangulate: BoolProperty(name="Triangulate Copy", default=False)
    export_include_textures: BoolProperty(name="Include Textures", default=True)
    export_scale: FloatProperty(name="Export Scale", default=1.0, min=0.0001, max=1000.0)

    def set_refine_from_params(self, params: dict) -> None:
        for name in REFINE_PARAMS:
            if name in params:
                setattr(self, f"refine_{name}", float(params[name]))

    def reset_refine(self) -> None:
        for name in REFINE_PARAMS:
            setattr(self, f"refine_{name}", 1.0)


def get_props(context) -> PMG_Properties:
    return context.scene.portrait_mesh


classes = (PMG_Properties,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.portrait_mesh = bpy.props.PointerProperty(type=PMG_Properties)


def unregister():
    del bpy.types.Scene.portrait_mesh
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
