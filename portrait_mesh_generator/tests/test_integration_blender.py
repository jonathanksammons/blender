"""Blender integration tests.

These require a running Blender (``bpy``). Run with::

    blender --background --python portrait_mesh_generator/tests/run_blender_tests.py

When imported outside Blender the whole module is skipped, so it is safe for the
pure-Python ``unittest discover`` run too.
"""

from __future__ import annotations

import unittest

try:
    import bpy  # type: ignore
    HAS_BPY = True
except ModuleNotFoundError:  # pragma: no cover - exercised only outside Blender
    HAS_BPY = False


@unittest.skipUnless(HAS_BPY, "requires Blender (bpy)")
class TestAddonIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import portrait_mesh_generator as pmg
        # Register cleanly; if already registered, re-register from scratch.
        try:
            pmg.register()
        except Exception:
            pmg.unregister()
            pmg.register()
        cls.pmg = pmg

    @classmethod
    def tearDownClass(cls):
        cls.pmg.unregister()

    def setUp(self):
        # Fresh scene-ish state for each test.
        bpy.ops.wm.read_homefile(use_empty=True)

    def test_registration_adds_scene_property(self):
        self.assertTrue(hasattr(bpy.context.scene, "portrait_mesh"))

    def test_base_head_build_and_validate(self):
        from portrait_mesh_generator.core import base_head, mesh_validation
        obj = base_head.build_base_object()
        bpy.context.scene.collection.objects.link(obj)
        self.assertEqual(len(obj.data.vertices), base_head.expected_vertex_count())
        self.assertGreater(len(obj.data.uv_layers), 0)
        result = mesh_validation.validate_object(obj)
        self.assertTrue(result.ok, result.summary())
        self.assertEqual(result.non_manifold_edges, 0)

    def test_load_base_head_operator(self):
        from portrait_mesh_generator.core import base_head, deformation_solver
        self.assertEqual(bpy.ops.pmg.load_base_head(), {"FINISHED"})
        working, source = deformation_solver.get_working_and_source()
        self.assertIsNotNone(working)
        self.assertIsNotNone(source)
        # Source and working must not share mesh data.
        self.assertNotEqual(working.data, source.data)

    def _make_reference(self):
        from portrait_mesh_generator.core import image_alignment
        img = bpy.data.images.new("pmg_test_img", width=512, height=640)
        return image_alignment.create_reference_empty(bpy.context, img, "front")

    def test_reference_and_landmarks_and_fit(self):
        from portrait_mesh_generator.core import (
            deformation_solver, landmark_objects as LO, landmark_storage,
        )
        self._make_reference()
        proj = landmark_storage.project_from_defaults("IT")
        n = LO.create_landmarks_from_project(bpy.context, proj, "front")
        self.assertEqual(n, len(proj.views["front"]))

        bpy.ops.pmg.load_base_head()
        working, source = deformation_solver.get_working_and_source()
        before = [v.co.copy() for v in working.data.vertices]

        # Move cheekbones wider, then fit.
        for o in LO.iter_landmark_empties("front"):
            if o.get(LO.PROP_LM_NAME) == "cheekbone_l":
                o.location.x -= 0.05
            if o.get(LO.PROP_LM_NAME) == "cheekbone_r":
                o.location.x += 0.05
        self.assertEqual(bpy.ops.pmg.fit_front_view(), {"FINISHED"})

        after = working.data.vertices
        self.assertEqual(len(after), len(before))  # vertex count preserved
        moved = any((after[i].co - before[i]).length > 1e-5 for i in range(len(before)))
        self.assertTrue(moved, "fit did not change the mesh")
        self.assertGreater(len(working.data.uv_layers), 0)  # UVs preserved

        # Reset restores base shape.
        self.assertEqual(bpy.ops.pmg.reset_fitting(), {"FINISHED"})
        for i in range(len(before)):
            self.assertLess((working.data.vertices[i].co - before[i]).length, 1e-5)

    def test_material_creation(self):
        from portrait_mesh_generator.core import texture_projection
        bpy.ops.pmg.load_base_head()
        from portrait_mesh_generator.core import deformation_solver
        working, _ = deformation_solver.get_working_and_source()
        mat = texture_projection.create_principled_material(working, None)
        self.assertIn(mat.name, [m.name for m in working.data.materials])

    def test_fbx_export_produces_file(self):
        import tempfile
        from pathlib import Path
        from portrait_mesh_generator.core import base_head, deformation_solver
        bpy.ops.pmg.load_base_head()
        working, source = deformation_solver.get_working_and_source()
        before_verts = len(source.data.vertices)
        with tempfile.TemporaryDirectory() as d:
            props = bpy.context.scene.portrait_mesh
            props.export_directory = d
            props.export_format = "FBX"
            self.assertEqual(bpy.ops.pmg.export_character(), {"FINISHED"})
            files = list(Path(d).glob("*.fbx"))
            self.assertEqual(len(files), 1)
            self.assertGreater(files[0].stat().st_size, 0)
        # Source mesh not mutated by export; export duplicate cleaned up.
        self.assertEqual(len(source.data.vertices), before_verts)
        self.assertIsNone(bpy.data.objects.get(base_head.WORKING_HEAD_NAME + "_EXPORT"))

    def test_landmark_json_round_trip(self):
        import tempfile, os
        from pathlib import Path
        from portrait_mesh_generator.core import landmark_objects as LO, landmark_storage
        self._make_reference()
        proj = landmark_storage.project_from_defaults("RT")
        LO.create_landmarks_from_project(bpy.context, proj, "front")
        snap = LO.read_project("front", "RT")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lm.json"
            landmark_storage.save(snap, p)
            loaded, warnings = landmark_storage.load(p)
            self.assertEqual(warnings, [])
            self.assertEqual(set(loaded.views["front"]), set(snap.views["front"]))


if __name__ == "__main__":
    unittest.main()
