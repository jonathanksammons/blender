import unittest

from portrait_mesh_generator.core import base_head as BH
from portrait_mesh_generator.core import deformation_solver as DS
from portrait_mesh_generator.core import mesh_validation as MV


class TestBaseGeometry(unittest.TestCase):
    def test_expected_vertex_count(self):
        verts, faces, uvs = BH.generate_geometry()
        self.assertEqual(len(verts), BH.expected_vertex_count())
        self.assertEqual(len(faces), len(uvs))

    def test_face_indices_valid(self):
        verts, faces, uvs = BH.generate_geometry()
        n = len(verts)
        for f in faces:
            self.assertTrue(all(0 <= i < n for i in f))
            self.assertIn(len(f), (3, 4))  # quads + pole triangle fans

    def test_uv_corner_counts_match_faces(self):
        verts, faces, uvs = BH.generate_geometry()
        for f, uv in zip(faces, uvs):
            self.assertEqual(len(f), len(uv))

    def test_symmetry_about_yz_plane(self):
        verts, _, _ = BH.generate_geometry()
        xs = sorted(round(v[0], 6) for v in verts)
        # Sum of x should be ~0 for a left-right symmetric mesh.
        self.assertAlmostEqual(sum(v[0] for v in verts), 0.0, places=4)


class TestDeformation(unittest.TestCase):
    def setUp(self):
        self.verts, _, _ = BH.generate_geometry()
        self.regions = DS.load_regions()

    def test_identity_params_no_change(self):
        params = {r.param: 1.0 for r in self.regions}
        out = DS.deform_coords(self.verts, self.regions, params)
        for a, b in zip(self.verts, out):
            self.assertAlmostEqual(a[0], b[0], places=9)
            self.assertAlmostEqual(a[2], b[2], places=9)

    def test_vertex_count_preserved(self):
        out = DS.deform_coords(self.verts, self.regions, {"head_width": 1.4})
        self.assertEqual(len(out), len(self.verts))

    def test_head_width_changes_bbox(self):
        before = max(v[0] for v in self.verts) - min(v[0] for v in self.verts)
        out = DS.deform_coords(self.verts, self.regions, {"head_width": 1.4})
        after = max(v[0] for v in out) - min(v[0] for v in out)
        self.assertGreater(after, before * 1.2)

    def test_head_height_changes_bbox(self):
        before = max(v[2] for v in self.verts) - min(v[2] for v in self.verts)
        out = DS.deform_coords(self.verts, self.regions, {"head_height": 0.8})
        after = max(v[2] for v in out) - min(v[2] for v in out)
        self.assertLess(after, before)


class TestValidationContainer(unittest.TestCase):
    def test_add_error_sets_invalid(self):
        r = MV.ValidationResult()
        self.assertTrue(r.ok)
        r.add_error("boom")
        self.assertFalse(r.ok)
        self.assertIn("boom", r.errors)


if __name__ == "__main__":
    unittest.main()
