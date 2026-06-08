"""Standardized base head mesh.

PortraitMesh deforms *one reusable base mesh*; it never generates arbitrary
topology per face. Ideally that base mesh is an artist-sculpted
``assets/base_head.blend``. Because a binary .blend cannot be authored as source
text, this module also provides a **deterministic procedural fallback** so the
add-on is fully functional out of the box.

The procedural head is a lathe-style surface (elliptical cross-sections stacked
along Z) shaped by an anatomical radius profile. It is:

* clean quad topology (two pole triangle-fans at skull top / neck base),
* manifold, with stable vertex indices (generation is fully deterministic),
* UV-mapped (cylindrical unwrap with a single back seam),
* symmetric about the YZ plane,
* real-world scale, facing -Y (so it reads correctly in Front view).

It is clearly an *approximation*; see ``docs/LIMITATIONS.md``. The fitting,
anchor and region systems all read the live bounding box, so a higher-quality
base mesh can replace it without code changes.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ..addon_info import BASE_MESH_VERSION

# Marker custom-property keys written onto generated objects.
PROP_IS_BASE = "pmg_is_base_head"
PROP_IS_WORKING = "pmg_is_working_head"
PROP_MESH_VERSION = "pmg_base_mesh_version"

BASE_HEAD_NAME = "PMG_BaseHead_Source"
WORKING_HEAD_NAME = "PMG_Head"

# Generation resolution. Vertex count = RINGS * SEGMENTS + 2 poles.
RINGS = 24
SEGMENTS = 32

# Anatomical radius profile as (z, half_width_x, half_depth_y, centre_y),
# in metres, ordered top -> bottom. Interpolated across rings.
_PROFILE: Tuple[Tuple[float, float, float, float], ...] = (
    (0.135, 0.045, 0.050, 0.000),  # near skull-top pole
    (0.110, 0.070, 0.090, 0.000),  # upper skull
    (0.075, 0.074, 0.098, 0.000),  # forehead
    (0.045, 0.075, 0.100, 0.000),  # brow / temple
    (0.015, 0.076, 0.099, 0.000),  # cheekbone (widest)
    (-0.015, 0.072, 0.095, 0.005),  # mid-face
    (-0.045, 0.062, 0.085, 0.008),  # jaw
    (-0.075, 0.045, 0.070, 0.010),  # lower jaw
    (-0.095, 0.030, 0.052, 0.006),  # chin
    (-0.115, 0.045, 0.050, 0.000),  # neck top
    (-0.150, 0.050, 0.052, 0.000),  # neck mid
    (-0.175, 0.045, 0.046, 0.000),  # near neck pole
)


def _interp_profile(z: float) -> Tuple[float, float, float]:
    """Linearly interpolate (rx, ry, cy) at height ``z`` from the profile."""
    pts = _PROFILE
    if z >= pts[0][0]:
        return pts[0][1], pts[0][2], pts[0][3]
    if z <= pts[-1][0]:
        return pts[-1][1], pts[-1][2], pts[-1][3]
    for i in range(len(pts) - 1):
        z0, rx0, ry0, cy0 = pts[i]
        z1, rx1, ry1, cy1 = pts[i + 1]
        if z1 <= z <= z0:
            t = (z - z0) / (z1 - z0) if z1 != z0 else 0.0
            return (
                rx0 + (rx1 - rx0) * t,
                ry0 + (ry1 - ry0) * t,
                cy0 + (cy1 - cy0) * t,
            )
    return pts[-1][1], pts[-1][2], pts[-1][3]


def generate_geometry() -> Tuple[List[Tuple[float, float, float]],
                                 List[Tuple[int, ...]],
                                 List[List[Tuple[float, float]]]]:
    """Return ``(verts, faces, face_uvs)`` for the procedural base head.

    Pure Python (no bpy) so geometry can be inspected/tested standalone.
    ``face_uvs[i]`` lists one (u, v) per corner of ``faces[i]``.
    """
    z_top = _PROFILE[0][0]
    z_bottom = _PROFILE[-1][0]

    verts: List[Tuple[float, float, float]] = []
    # ring r in [0, RINGS-1] from bottom (0) to top (RINGS-1).
    ring_z: List[float] = []
    for r in range(RINGS):
        t = r / (RINGS - 1)
        z = z_bottom + (z_top - z_bottom) * t
        ring_z.append(z)
        rx, ry, cy = _interp_profile(z)
        for s in range(SEGMENTS):
            theta = (s / SEGMENTS) * 2.0 * math.pi
            x = rx * math.cos(theta)
            y = cy + ry * math.sin(theta)
            verts.append((x, y, z))

    pole_bottom = len(verts)
    verts.append((0.0, _PROFILE[-1][3], z_bottom - 0.012))
    pole_top = len(verts)
    verts.append((0.0, _PROFILE[0][3], z_top + 0.012))

    def vidx(r: int, s: int) -> int:
        return r * SEGMENTS + (s % SEGMENTS)

    faces: List[Tuple[int, ...]] = []
    face_uvs: List[List[Tuple[float, float]]] = []

    def uv(r: int, s: int) -> Tuple[float, float]:
        # s may equal SEGMENTS at the wrap seam -> u = 1.0 (avoids seam stretch).
        return (s / SEGMENTS, r / (RINGS - 1))

    # Side quads.
    for r in range(RINGS - 1):
        for s in range(SEGMENTS):
            faces.append((vidx(r, s), vidx(r, s + 1), vidx(r + 1, s + 1), vidx(r + 1, s)))
            face_uvs.append([uv(r, s), uv(r, s + 1), uv(r + 1, s + 1), uv(r + 1, s)])

    # Bottom pole fan (ring 0).
    for s in range(SEGMENTS):
        faces.append((pole_bottom, vidx(0, s + 1), vidx(0, s)))
        face_uvs.append([(0.5, 0.0), ((s + 1) / SEGMENTS, 0.0), (s / SEGMENTS, 0.0)])

    # Top pole fan (ring RINGS-1).
    top = RINGS - 1
    for s in range(SEGMENTS):
        faces.append((pole_top, vidx(top, s), vidx(top, s + 1)))
        face_uvs.append([(0.5, 1.0), (s / SEGMENTS, 1.0), ((s + 1) / SEGMENTS, 1.0)])

    return verts, faces, face_uvs


# --- Blender-side construction ---------------------------------------------
# Everything below requires bpy; imports are local so this module stays
# importable (for the geometry generator/tests) without Blender.


def build_base_object(name: str = BASE_HEAD_NAME, scale: float = 1.0):
    """Create a Blender object for the procedural base head and return it."""
    import bpy  # type: ignore

    verts, faces, face_uvs = generate_geometry()
    if scale != 1.0:
        verts = [(x * scale, y * scale, z * scale) for (x, y, z) in verts]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([list(v) for v in verts], [], [list(f) for f in faces])
    mesh.update()

    uv_layer = mesh.uv_layers.new(name="UVMap")
    loop_uvs = uv_layer.data
    li = 0
    for fi, poly in enumerate(mesh.polygons):
        corners = face_uvs[fi]
        for c in range(poly.loop_total):
            loop_uvs[li].uv = corners[c]
            li += 1

    mesh.validate(verbose=False)
    mesh.update()

    # Recalculate normals to point outward.
    _recalc_normals(mesh)

    obj = bpy.data.objects.new(name, mesh)
    obj[PROP_IS_BASE] = True
    obj[PROP_MESH_VERSION] = BASE_MESH_VERSION
    return obj


def _recalc_normals(mesh) -> None:
    import bmesh  # type: ignore

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def load_or_create_base(scale: float = 1.0):
    """Load ``assets/base_head.blend`` if present and valid, else build procedural.

    Returns ``(object, source_str)`` where source_str is "asset" or "procedural".
    """
    import bpy  # type: ignore
    from pathlib import Path

    asset_path = Path(__file__).resolve().parent.parent / "assets" / "base_head.blend"
    if asset_path.is_file():
        try:
            with bpy.data.libraries.load(str(asset_path), link=False) as (src, dst):
                if "PMG_BaseHead" in src.objects:
                    dst.objects = ["PMG_BaseHead"]
            for obj in dst.objects:
                if obj is not None:
                    obj[PROP_IS_BASE] = True
                    obj[PROP_MESH_VERSION] = BASE_MESH_VERSION
                    return obj, "asset"
        except Exception:
            # Fall through to procedural; the caller logs the reason.
            pass
    return build_base_object(scale=scale), "procedural"


def expected_vertex_count() -> int:
    return RINGS * SEGMENTS + 2
