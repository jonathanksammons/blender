"""Panel registration aggregator."""

from __future__ import annotations

import bpy

from . import (
    diagnostics_panel,
    export_panel,
    fitting_panel,
    landmark_panel,
    main_panel,
    reference_panel,
    texture_panel,
)

# Order matters: the root panel must register before its children.
_MODULES = (
    main_panel,
    reference_panel,
    landmark_panel,
    fitting_panel,
    texture_panel,
    export_panel,
    diagnostics_panel,
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
