import unittest

from portrait_mesh_generator.addon_info import LANDMARK_SCHEMA_VERSION
from portrait_mesh_generator.core import landmark_schema as ls
from portrait_mesh_generator.core import landmark_storage as storage


class TestLandmarkSchema(unittest.TestCase):
    def test_front_landmark_coverage(self):
        names = ls.front_landmark_names()
        # Spot-check required vertical-slice landmarks exist.
        for required in (
            "eye_inner_l", "eye_outer_r", "pupil_l", "nose_tip", "nostril_l",
            "mouth_corner_r", "upper_lip", "lower_lip", "chin",
            "jaw_corner_l", "cheek_r", "temple_l", "skull_top",
        ):
            self.assertIn(required, names)

    def test_symmetry_pairs_are_mutual(self):
        for left, right in ls.symmetry_pairs():
            self.assertEqual(ls.get(left).symmetry_partner, right)
            self.assertEqual(ls.get(right).symmetry_partner, left)
            self.assertEqual(ls.get(left).side, "L")
            self.assertEqual(ls.get(right).side, "R")

    def test_defaults_in_unit_range(self):
        for d in ls.all_landmarks():
            x, y = d.default
            self.assertTrue(0.0 <= x <= 1.0, d.name)
            self.assertTrue(0.0 <= y <= 1.0, d.name)

    def test_validate_good_payload(self):
        payload = {
            "schema_version": LANDMARK_SCHEMA_VERSION,
            "views": {"front": {"nose_tip": {"pos": [0.5, 0.5]}}},
        }
        warnings = ls.validate_landmark_payload(payload)
        self.assertEqual(warnings, [])

    def test_validate_rejects_missing_views(self):
        with self.assertRaises(ls.SchemaValidationError):
            ls.validate_landmark_payload({"schema_version": 1})

    def test_validate_rejects_bad_coords(self):
        bad = {"schema_version": 1, "views": {"front": {"nose_tip": {"pos": ["a", 1]}}}}
        with self.assertRaises(ls.SchemaValidationError):
            ls.validate_landmark_payload(bad)

    def test_storage_round_trip(self):
        proj = storage.project_from_defaults("Test")
        payload = storage.to_payload(proj)
        proj2, warnings = storage.from_payload(payload)
        self.assertEqual(warnings, [])
        self.assertEqual(set(proj.views["front"]), set(proj2.views["front"]))
        # Positions preserved.
        for name in proj.views["front"]:
            self.assertAlmostEqual(
                proj.views["front"][name].pos[0], proj2.views["front"][name].pos[0]
            )


if __name__ == "__main__":
    unittest.main()
