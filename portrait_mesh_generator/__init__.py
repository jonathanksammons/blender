"""PortraitMesh Generator -- landmark-driven portrait-to-mesh head reconstruction.

A local-only Blender 5.1 add-on. It deforms a single standardized base head to
match facial landmarks placed over portrait references. No cloud services, no
paid APIs, no automatic downloads. See ``docs/`` for full documentation.
"""

from __future__ import annotations

from .addon_info import ADDON_NAME, ADDON_VERSION, MIN_BLENDER_VERSION

# Legacy bl_info block (also shipped with blender_manifest.toml for the
# extension system). Kept so "Install from Disk" works on 5.1.
bl_info = {
    "name": ADDON_NAME,
    "author": "PortraitMesh Generator contributors",
    "version": ADDON_VERSION,
    "blender": MIN_BLENDER_VERSION,
    "location": "View3D > Sidebar > PortraitMesh",
    "description": "Generate a recognizable editable head mesh from portrait references (local-only).",
    "category": "Mesh",
    "doc_url": "",
    "tracker_url": "",
}

def _register_modules():
    """Import the Blender-dependent submodules in registration order.

    Imported lazily (inside register/unregister) so that the pure-Python ``core``
    package -- and the unit tests -- can import this package without ``bpy``.
    """
    from . import operators, panels, preferences, properties

    return (preferences, properties, operators, panels)


def register():
    from .core import logging_utils

    logging_utils.configure()
    log = logging_utils.get_logger("register")
    for module in _register_modules():
        module.register()
    log.info("%s registered (v%s).", ADDON_NAME, ".".join(map(str, ADDON_VERSION)))


def unregister():
    from .core import logging_utils

    log = logging_utils.get_logger("register")
    for module in reversed(_register_modules()):
        try:
            module.unregister()
        except Exception as exc:  # ensure later modules still unregister
            log.error("Error unregistering %s: %s", module.__name__, exc)
    log.info("%s unregistered.", ADDON_NAME)
    logging_utils.shutdown()


if __name__ == "__main__":
    register()
