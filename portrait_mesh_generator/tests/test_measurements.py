import unittest

from portrait_mesh_generator.core import landmark_schema as ls
from portrait_mesh_generator.core import measurements as M
from portrait_mesh_generator.core import symmetry


def default_points():
    return {d.name: d.default for d in ls.front_landmarks()}


class TestMeasurements(unittest.TestCase):
    def test_reference_scale_prefers_pupils(self):
        pts = default_points()
        scale, name = M.reference_scale(pts)
        self.assertEqual(name, "interpupillary")
        self.assertGreater(scale, 0.0)

    def test_default_face_measurements_available(self):
        ms = M.compute_measurements(default_points())
        for key in ("face_width", "face_height", "jaw_width", "eye_spacing",
                    "nose_width", "nose_length", "mouth_width", "chin_height"):
            self.assertTrue(ms[key].available, key)
            self.assertGreater(ms[key].normalized, 0.0, key)

    def test_normalization_is_scale_invariant(self):
        pts = default_points()
        # Uniformly scale all points about origin -> normalized values unchanged.
        scaled = {k: (x * 2.0, y * 2.0) for k, (x, y) in pts.items()}
        a = M.compute_measurements(pts)
        b = M.compute_measurements(scaled)
        self.assertAlmostEqual(a["face_width"].normalized, b["face_width"].normalized, places=6)

    def test_clamping_reported(self):
        pts = default_points()
        # Push cheekbones absurdly wide to exceed face_width clamp.
        pts["cheekbone_l"] = (-2.0, 0.45)
        pts["cheekbone_r"] = (3.0, 0.45)
        ms = M.compute_measurements(pts)
        self.assertTrue(ms["face_width"].clamped)
        self.assertIsNotNone(ms["face_width"].clamped_to)

    def test_override_applied(self):
        pts = default_points()
        ms = M.compute_measurements(pts, overrides={"nose_width": 0.9})
        self.assertTrue(ms["nose_width"].overridden)
        self.assertAlmostEqual(ms["nose_width"].normalized, 0.9)

    def test_missing_landmarks_marked_unavailable(self):
        pts = default_points()
        del pts["neck_l"]
        ms = M.compute_measurements(pts)
        self.assertFalse(ms["neck_width"].available)

    def test_facial_thirds_sum_to_one(self):
        thirds = M.facial_thirds(default_points())
        self.assertIsNotNone(thirds)
        self.assertAlmostEqual(sum(thirds), 1.0, places=6)


class TestSymmetry(unittest.TestCase):
    def test_mirror_left_to_right(self):
        pts = default_points()
        # Perturb left eye outer; mirror should set right partner symmetrically.
        pts["eye_outer_l"] = (0.30, 0.42)
        mirrored = symmetry.mirror_landmarks(pts, source_side="L")
        mid = symmetry.estimate_midline_x(pts)
        expected_x = 2 * mid - 0.30
        self.assertAlmostEqual(mirrored["eye_outer_r"][0], expected_x, places=6)
        self.assertAlmostEqual(mirrored["eye_outer_r"][1], 0.42, places=6)


if __name__ == "__main__":
    unittest.main()
