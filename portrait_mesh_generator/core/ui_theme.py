"""Centralized UI / overlay theme values.

All colours, default sizes and icon names live here so the look of landmarks,
panels and overlays can be tuned in one place (a coding rule for this project).
"""

from __future__ import annotations

from typing import Dict, Tuple

RGBA = Tuple[float, float, float, float]

# Per-category landmark colours (RGBA, linear-ish display colour for empties).
CATEGORY_COLORS: Dict[str, RGBA] = {
    "skull": (0.85, 0.85, 0.20, 1.0),
    "jaw": (0.90, 0.45, 0.15, 1.0),
    "eyes": (0.20, 0.65, 0.95, 1.0),
    "brows": (0.40, 0.80, 0.95, 1.0),
    "nose": (0.30, 0.85, 0.40, 1.0),
    "mouth": (0.95, 0.30, 0.45, 1.0),
    "ears": (0.75, 0.55, 0.95, 1.0),
    "neck": (0.60, 0.60, 0.60, 1.0),
    "profile": (0.95, 0.75, 0.20, 1.0),
}

CATEGORY_ICONS: Dict[str, str] = {
    "skull": "MESH_UVSPHERE",
    "jaw": "MESH_CONE",
    "eyes": "HIDE_OFF",
    "brows": "IPO_EASE_IN_OUT",
    "nose": "CONE",
    "mouth": "MESH_CAPSULE",
    "ears": "MOD_SUBSURF",
    "neck": "MESH_CYLINDER",
    "profile": "AXIS_SIDE",
}

DEFAULT_LANDMARK_SIZE = 0.004
DEFAULT_LANDMARK_OPACITY = 1.0

PANEL_CATEGORY = "PortraitMesh"


def category_color(category: str) -> RGBA:
    return CATEGORY_COLORS.get(category, (0.8, 0.8, 0.8, 1.0))


def category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, "DOT")
