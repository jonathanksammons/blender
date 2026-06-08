"""Core logic package.

Modules here are split into:
* pure-Python (no ``bpy``): landmark_schema, landmark_storage, measurements,
  fitting_solver, deformation_solver (numerics), symmetry, profile_depth,
  dependency_manager, logging_utils, ui_theme -- importable by unit tests.
* Blender-dependent: base_head, image_alignment, landmark_objects,
  mesh_validation, texture_projection -- import ``bpy``/``bmesh`` lazily.
"""
