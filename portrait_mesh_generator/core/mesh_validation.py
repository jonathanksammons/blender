"""Base/working mesh validation.

Validation results are returned as data so panels and operators can present
actionable messages. The bmesh-based checks require Blender; the
:class:`ValidationResult` container and the topology summary helpers are plain
data and importable anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..addon_info import BASE_MESH_VERSION
from . import base_head


@dataclass
class ValidationResult:
    ok: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    vertex_count: int = 0
    face_count: int = 0
    has_uvs: bool = False
    non_manifold_edges: int = 0
    duplicate_verts: int = 0
    mesh_version: Optional[int] = None

    def add_error(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def summary(self) -> str:
        state = "VALID" if self.ok else "INVALID"
        return (
            f"[{state}] verts={self.vertex_count} faces={self.face_count} "
            f"uv={'yes' if self.has_uvs else 'no'} "
            f"non_manifold_edges={self.non_manifold_edges} "
            f"duplicates={self.duplicate_verts}"
        )


def validate_object(obj, *, expect_version: bool = True, merge_distance: float = 1e-5) -> ValidationResult:
    """Validate a Blender mesh object for use as a PortraitMesh base/working head."""
    import bmesh  # type: ignore

    result = ValidationResult()
    if obj is None or getattr(obj, "type", None) != "MESH":
        result.add_error("Object is missing or is not a mesh.")
        return result

    mesh = obj.data
    result.vertex_count = len(mesh.vertices)
    result.face_count = len(mesh.polygons)
    result.has_uvs = len(mesh.uv_layers) > 0
    result.mesh_version = obj.get(base_head.PROP_MESH_VERSION)

    if result.vertex_count == 0:
        result.add_error("Mesh has no vertices.")
        return result
    if not result.has_uvs:
        result.add_warning("Mesh has no UV layer; texture projection will be limited.")

    if expect_version:
        if result.mesh_version is None:
            result.add_warning("Mesh has no PortraitMesh base-version tag.")
        elif result.mesh_version != BASE_MESH_VERSION:
            result.add_error(
                f"Base mesh version mismatch: mesh={result.mesh_version} "
                f"expected={BASE_MESH_VERSION}. Anchors may be invalid."
            )

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        result.non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
        if result.non_manifold_edges:
            result.add_error(f"Mesh has {result.non_manifold_edges} non-manifold edge(s).")

        # Duplicate vertices: count merges a doubles-find would perform.
        found = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=merge_distance)
        targetmap = found.get("targetmap", {})
        result.duplicate_verts = len(targetmap)
        if result.duplicate_verts:
            result.add_warning(f"Mesh has {result.duplicate_verts} duplicate vertices.")
    finally:
        bm.free()

    return result


def check_anchor_compatibility(obj) -> ValidationResult:
    """Verify the working mesh matches the expected base topology for anchoring."""
    result = ValidationResult()
    if obj is None or getattr(obj, "type", None) != "MESH":
        result.add_error("No mesh to check anchors against.")
        return result
    result.vertex_count = len(obj.data.vertices)
    expected = base_head.expected_vertex_count()
    version = obj.get(base_head.PROP_MESH_VERSION)
    if version == BASE_MESH_VERSION and result.vertex_count != expected:
        result.add_error(
            f"Anchor mismatch: vertex count {result.vertex_count} != expected {expected}."
        )
    return result
