"""Texture material helpers (Blender side).

Phase 7 (full multi-view camera projection with seam feathering and overlap
blending) is **not implemented in this version** -- the functions for it raise a
clear ``NotImplementedError`` rather than pretending to work.

What *is* implemented now: creating a Principled BSDF material that maps the
front reference image onto the head's existing UVs. This is honest, useful, and
preserves the base UV layout.
"""

from __future__ import annotations

from typing import Optional


def create_principled_material(obj, image, name: str = "PMG_Head_Material"):
    """Create/assign a Principled BSDF material using ``image`` as base colour."""
    import bpy  # type: ignore

    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    if image is not None:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.location = (-300, 0)
        uvmap = nodes.new("ShaderNodeUVMap")
        uvmap.location = (-550, 0)
        if obj.data.uv_layers:
            uvmap.uv_map = obj.data.uv_layers[0].name
        links.new(uvmap.outputs["UV"], tex.inputs["Vector"])
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    return mat


def project_front_texture(*args, **kwargs):
    raise NotImplementedError(
        "Camera-based front projection is planned for Phase 7 and is not "
        "implemented in this version. Use 'Create Material' for a basic UV map."
    )


def project_side_textures(*args, **kwargs):
    raise NotImplementedError(
        "Profile texture projection/blending is planned for Phase 7 and is not "
        "implemented in this version."
    )
