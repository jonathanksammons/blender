import unittest

from portrait_mesh_generator.core import fitting_solver as FS
from portrait_mesh_generator.core import landmark_schema as ls
from portrait_mesh_generator.core import measurements as M


def default_points():
    return {d.name: d.default for d in ls.front_landmarks()}


class TestFittingSolver(unittest.TestCase):
    def test_default_face_is_identity(self):
        ms = M.compute_measurements(default_points())
        res = FS.solve(ms, regularization=0.0)
        for name, val in res.params.items():
            self.assertAlmostEqual(val, 1.0, places=2, msg=name)
        self.assertLess(res.residual, 1e-3)
        self.assertTrue(res.converged)

    def test_recovers_synthetic_scale(self):
        # Build measurements that are reference * known factors.
        refs = FS.reference_measurements()
        factor = 1.3
        meas = {}
        for param, mname in FS.PARAM_TO_MEASUREMENT.items():
            meas[mname] = M.Measurement(
                name=mname, raw=0.0, normalized=refs[mname] * factor,
                sources=(), available=True,
            )
        res = FS.solve(meas, regularization=0.0, max_iterations=200)
        for name, val in res.params.items():
            self.assertAlmostEqual(val, factor, places=2, msg=name)

    def test_parameters_are_bounded(self):
        refs = FS.reference_measurements()
        meas = {}
        for param, mname in FS.PARAM_TO_MEASUREMENT.items():
            meas[mname] = M.Measurement(
                name=mname, raw=0.0, normalized=refs[mname] * 10.0,
                sources=(), available=True,
            )
        res = FS.solve(meas, regularization=0.0)
        lo, hi = FS.PARAM_BOUNDS
        for val in res.params.values():
            self.assertLessEqual(val, hi + 1e-9)
            self.assertGreaterEqual(val, lo - 1e-9)
        self.assertTrue(res.clamped_params)

    def test_missing_measurement_skipped(self):
        ms = M.compute_measurements(default_points())
        del ms["mouth_width"]
        res = FS.solve(ms)
        self.assertIn("mouth_width", res.skipped_params)
        self.assertNotIn("mouth_width", res.params)


if __name__ == "__main__":
    unittest.main()
