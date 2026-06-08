"""Operator registration aggregator."""

from __future__ import annotations

import bpy

from . import (
    auto_detect_landmarks,
    create_landmarks,
    export_character,
    fit_front_view,
    fit_profile_view,
    generate_head,
    import_references,
    project_texture,
    reset_fitting,
)

_MODULES = (
    import_references,
    create_landmarks,
    auto_detect_landmarks,
    generate_head,
    fit_front_view,
    fit_profile_view,
    reset_fitting,
    project_texture,
    export_character,
)


def all_classes():
    classes = []
    for mod in _MODULES:
        classes.extend(mod.classes)
    return classes


def register():
    for cls in all_classes():
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(all_classes()):
        bpy.utils.unregister_class(cls)
