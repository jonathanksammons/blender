"""Reference image handling and image<->world coordinate mapping (Blender side).

A reference is shown as an ``IMAGE`` empty lying in a view-aligned plane. We
build a *logical* frame of width ``W`` and height ``H`` (metres) centred on the
empty so landmark positions map deterministically between world space and
normalized image coordinates, independent of viewport state.

Front-view convention (matches Blender Numpad-1):
    normalized x in [0,1], left->right  ==>  world +X (screen right)
    normalized y in [0,1], top->bottom  ==>  world +Z (screen up, inverted)
Landmarks live at y = 0; the image plane sits slightly behind at y = +offset.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, Tuple

# Custom-property keys on reference empties.
PROP_IS_REF = "pmg_is_reference"
PROP_REF_VIEW = "pmg_reference_view"
PROP_REF_W = "pmg_reference_width"
PROP_REF_H = "pmg_reference_height"
PROP_REF_PATH = "pmg_reference_path"

DEFAULT_REF_HEIGHT = 0.30  # metres for a head-height portrait at working scale 1.0
PLANE_BACK_OFFSET = 0.12   # image sits behind landmark plane

VIEW_ROTATIONS = {
    # Euler XYZ radians to orient the image plane for each view.
    "front": (math.pi / 2.0, 0.0, 0.0),
    "left": (math.pi / 2.0, 0.0, -math.pi / 2.0),
    "right": (math.pi / 2.0, 0.0, math.pi / 2.0),
}


class ReferenceError(RuntimeError):
    pass


def load_reference_image(filepath: str):
    """Load an image into bpy.data.images with clear errors. Returns the image."""
    import bpy  # type: ignore

    path = Path(bpy.path.abspath(filepath)) if filepath else None
    if not path or not path.is_file():
        raise ReferenceError(f"Image file not found: {filepath}")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".tif", ".tiff", ".exr"}:
        raise ReferenceError(f"Unsupported image format: {path.suffix}")
    try:
        image = bpy.data.images.load(str(path), check_existing=True)
    except RuntimeError as exc:
        raise ReferenceError(f"Blender could not load image: {exc}") from exc
    if image.size[0] == 0 or image.size[1] == 0:
        raise ReferenceError("Image has zero dimensions or failed to decode.")
    return image


def frame_dimensions(image, height: float = DEFAULT_REF_HEIGHT) -> Tuple[float, float]:
    """Return (W, H) preserving the image aspect ratio."""
    res_x, res_y = image.size[0], image.size[1]
    aspect = (res_x / res_y) if res_y else 1.0
    return height * aspect, height


def create_reference_empty(context, image, view: str, height: float = DEFAULT_REF_HEIGHT,
                           collection=None):
    """Create (or replace) an image empty for ``view`` and return it."""
    import bpy  # type: ignore

    if view not in VIEW_ROTATIONS:
        raise ReferenceError(f"Unknown reference view: {view}")

    # Remove any existing reference for this view to avoid duplicates.
    existing = find_reference_empty(view)
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)

    w, h = frame_dimensions(image, height)
    empty = bpy.data.objects.new(f"PMG_Ref_{view.capitalize()}", None)
    empty.empty_display_type = "IMAGE"
    empty.data = image
    empty.empty_display_size = w  # width-based; yields displayed height == h
    empty.empty_image_offset = (-0.5, -0.5)  # centre the image on the origin
    empty.rotation_euler = VIEW_ROTATIONS[view]
    empty.use_empty_image_alpha = True
    empty.color = (1.0, 1.0, 1.0, 1.0)

    if view == "front":
        empty.location = (0.0, PLANE_BACK_OFFSET, 0.0)
    elif view == "left":
        empty.location = (-PLANE_BACK_OFFSET, 0.0, 0.0)
    else:  # right
        empty.location = (PLANE_BACK_OFFSET, 0.0, 0.0)

    empty[PROP_IS_REF] = True
    empty[PROP_REF_VIEW] = view
    empty[PROP_REF_W] = w
    empty[PROP_REF_H] = h
    empty[PROP_REF_PATH] = image.filepath

    target_collection = collection or context.scene.collection
    target_collection.objects.link(empty)
    return empty


def find_reference_empty(view: str):
    import bpy  # type: ignore

    for obj in bpy.data.objects:
        if obj.get(PROP_IS_REF) and obj.get(PROP_REF_VIEW) == view:
            return obj
    return None


def normalized_to_world(empty, nx: float, ny: float) -> Tuple[float, float, float]:
    """Map normalized image coords to a world position on the landmark plane."""
    w = float(empty.get(PROP_REF_W, DEFAULT_REF_HEIGHT))
    h = float(empty.get(PROP_REF_H, DEFAULT_REF_HEIGHT))
    view = empty.get(PROP_REF_VIEW, "front")
    u = (nx - 0.5) * w
    v = (0.5 - ny) * h
    if view == "front":
        return (u, 0.0, v)
    if view == "left":
        return (0.0, -u, v)
    return (0.0, u, v)  # right


def world_to_normalized(empty, world: Tuple[float, float, float]) -> Tuple[float, float]:
    """Inverse of :func:`normalized_to_world`."""
    w = float(empty.get(PROP_REF_W, DEFAULT_REF_HEIGHT))
    h = float(empty.get(PROP_REF_H, DEFAULT_REF_HEIGHT))
    view = empty.get(PROP_REF_VIEW, "front")
    if view == "front":
        u, v = world[0], world[2]
    elif view == "left":
        u, v = -world[1], world[2]
    else:
        u, v = world[1], world[2]
    nx = u / w + 0.5 if w else 0.5
    ny = 0.5 - v / h if h else 0.5
    return nx, ny
