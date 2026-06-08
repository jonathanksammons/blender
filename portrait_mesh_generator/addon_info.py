"""Central, dependency-free metadata for the PortraitMesh Generator add-on.

This module intentionally imports nothing from Blender so it can be read by
unit tests, build scripts, and the external landmark adapter without a running
Blender instance.
"""

from __future__ import annotations

# Human readable identity ----------------------------------------------------
ADDON_NAME = "PortraitMesh Generator"
ADDON_PACKAGE = "portrait_mesh_generator"

# Semantic version of the add-on itself.
ADDON_VERSION = (0, 1, 0)

# Versions of the data contracts. These are checked at runtime so that a mesh,
# schema, or saved project produced by an older build is detected instead of
# silently mis-interpreted.
LANDMARK_SCHEMA_VERSION = 1
BASE_MESH_VERSION = 1
PROJECT_FILE_VERSION = 1

# Minimum Blender version this add-on is written and tested against.
MIN_BLENDER_VERSION = (5, 1, 0)


def version_string(version: tuple[int, ...]) -> str:
    """Return a dotted version string, e.g. ``(0, 1, 0) -> "0.1.0"``."""
    return ".".join(str(part) for part in version)


def addon_version_string() -> str:
    return version_string(ADDON_VERSION)
