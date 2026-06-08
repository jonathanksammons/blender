"""Add-on preferences.

Holds the optional external-Python path used for out-of-process landmark
detection. The add-on never installs packages or downloads models; these
preferences only *point at* a Python the user has already set up.
"""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import AddonPreferences

from .addon_info import ADDON_PACKAGE, addon_version_string


class PMG_Preferences(AddonPreferences):
    bl_idname = ADDON_PACKAGE

    external_python_path: StringProperty(
        name="External Python",
        description=(
            "Optional path to a Python executable with a landmark detector "
            "installed (e.g. mediapipe). Used only when you run Auto Detect. "
            "Leave empty to use manual landmarks only."
        ),
        subtype="FILE_PATH",
        default="",
    )

    allow_inprocess_detector: BoolProperty(
        name="Allow In-Process Detector",
        description=(
            "If enabled and a compatible detector is importable inside Blender's "
            "Python, allow using it directly. Off by default for stability"
        ),
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"PortraitMesh Generator v{addon_version_string()}", icon="USER")
        box = layout.box()
        box.label(text="Local-only. No network access, no automatic downloads.", icon="LOCKED")
        box.prop(self, "external_python_path")
        box.prop(self, "allow_inprocess_detector")
        box.operator("pmg.run_diagnostics", icon="INFO")


def get_preferences(context) -> PMG_Preferences:
    return context.preferences.addons[ADDON_PACKAGE].preferences


classes = (PMG_Preferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
