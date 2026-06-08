"""Apply bounded deformation parameters to the base head mesh.

The numerical core (:func:`deform_coords`) is pure Python and unit-testable. A
thin Blender wrapper (:func:`apply_to_object`) moves only vertex *coordinates*
via ``foreach_get``/``foreach_set`` -- it never alters topology or UV loops, so
vertex count and UVs are preserved exactly (a first-version requirement).

Each deformation *region* scales one axis of nearby vertices about a pivot with
a smooth falloff:

    new[axis] = pivot[axis] + (orig[axis] - pivot[axis]) * (1 + (factor-1)*w)

where ``w`` in [0,1] combines a radial smoothstep falloff with an optional
front-of-face mask. Regions are data-driven (``assets/deformation_regions.json``)
so the deformation map is maintainable without code edits.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

Vec3 = Tuple[float, float, float]
AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


@dataclass
class DeformRegion:
    name: str
    param: str
    center: Tuple[float, float, float]  # fractions of bbox [0,1]
    radius: float                       # fraction of max bbox dimension
    axis: str
    falloff: str = "smooth"             # "smooth" or "none"
    front_only: bool = False
    pivot: str = "axis"                 # "axis" (region centre) or "center"


def default_regions_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "deformation_regions.json"


def load_regions(path: Optional[Path] = None) -> List[DeformRegion]:
    path = Path(path) if path else default_regions_path()
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    regions = []
    for entry in data["regions"]:
        regions.append(
            DeformRegion(
                name=entry["name"],
                param=entry["param"],
                center=tuple(entry["center"]),
                radius=float(entry["radius"]),
                axis=entry["axis"],
                falloff=entry.get("falloff", "smooth"),
                front_only=bool(entry.get("front_only", False)),
                pivot=entry.get("pivot", "axis"),
            )
        )
    return regions


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 0.0 if x < edge0 else 1.0
    t = (x - edge0) / (edge1 - edge0)
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _bbox(coords: Sequence[Vec3]) -> Tuple[Vec3, Vec3]:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def deform_coords(
    coords: Sequence[Vec3],
    regions: Sequence[DeformRegion],
    params: Mapping[str, float],
    bbox: Optional[Tuple[Vec3, Vec3]] = None,
) -> List[Vec3]:
    """Return new coordinates after applying all regions in order.

    ``coords`` are local-space vertex coordinates. ``params`` maps region.param
    -> multiplicative factor (1.0 = no change). Regions whose param is absent or
    ~1.0 are skipped.
    """
    if not coords:
        return []
    bmin, bmax = bbox if bbox else _bbox(coords)
    dims = tuple(max(1e-9, bmax[i] - bmin[i]) for i in range(3))
    max_dim = max(dims)
    centroid = tuple((bmin[i] + bmax[i]) * 0.5 for i in range(3))

    out: List[Vec3] = [tuple(c) for c in coords]

    for region in regions:
        factor = params.get(region.param)
        if factor is None or abs(factor - 1.0) < 1e-6:
            continue
        axis = AXIS_INDEX[region.axis]
        center_local = tuple(bmin[i] + region.center[i] * dims[i] for i in range(3))
        radius_local = region.radius * max_dim
        pivot = center_local if region.pivot == "axis" else centroid

        new_out: List[Vec3] = []
        for c in out:
            if region.falloff == "none" or radius_local <= 0:
                w = 1.0
            else:
                d = math.dist(c, center_local)
                w = 1.0 - _smoothstep(0.0, radius_local, d)
            if region.front_only:
                # Face front is -Y; mask out the back of the head smoothly.
                front_mask = 1.0 - _smoothstep(center_local[1], center_local[1] + dims[1] * 0.25, c[1])
                w *= front_mask
            if w <= 0.0:
                new_out.append(c)
                continue
            scale = 1.0 + (factor - 1.0) * w
            moved = list(c)
            moved[axis] = pivot[axis] + (c[axis] - pivot[axis]) * scale
            new_out.append(tuple(moved))
        out = new_out
    return out


def apply_to_object(working_obj, source_obj, regions, params) -> int:
    """Deform ``working_obj`` from ``source_obj``'s rest coordinates.

    Reads rest coordinates from the source (never mutated), applies the
    deformation and writes the result back to the working mesh. Returns the
    number of vertices moved (== vertex count, unchanged).
    """
    src_mesh = source_obj.data
    n = len(src_mesh.vertices)
    flat = [0.0] * (n * 3)
    src_mesh.vertices.foreach_get("co", flat)
    coords = [(flat[i * 3], flat[i * 3 + 1], flat[i * 3 + 2]) for i in range(n)]

    new_coords = deform_coords(coords, regions, params)

    out_flat = [0.0] * (n * 3)
    for i, (x, y, z) in enumerate(new_coords):
        out_flat[i * 3] = x
        out_flat[i * 3 + 1] = y
        out_flat[i * 3 + 2] = z
    work_mesh = working_obj.data
    work_mesh.vertices.foreach_set("co", out_flat)
    work_mesh.update()
    return n


_REGION_CACHE: Optional[List[DeformRegion]] = None


def cached_regions() -> List[DeformRegion]:
    global _REGION_CACHE
    if _REGION_CACHE is None:
        _REGION_CACHE = load_regions()
    return _REGION_CACHE


def get_working_and_source():
    """Return (working_obj, source_obj) by their canonical names, or (None, None)."""
    import bpy  # type: ignore
    from . import base_head

    working = bpy.data.objects.get(base_head.WORKING_HEAD_NAME)
    source = bpy.data.objects.get(base_head.BASE_HEAD_NAME)
    return working, source


def apply_params(params: Mapping[str, float]) -> bool:
    """Deform the scene's working head from its source using ``params``.

    Returns True if a deformation was applied, False if no head exists yet.
    Safe to call from property-update callbacks.
    """
    working, source = get_working_and_source()
    if working is None or source is None:
        return False
    apply_to_object(working, source, cached_regions(), params)
    return True
