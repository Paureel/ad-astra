"""Independent exact flat-space checks for the Hamiltonian ray integrator."""
import unittest

import numpy as np

from warpproof.geodesics import integrate_null_ray


class ConstantShiftGeometry:
    """Minkowski spacetime in a uniformly shifted Cartesian chart."""
    c = 299792458.0

    def __init__(self, shift):
        self.shift = np.asarray(shift, dtype=float)

    def fields(self, point):
        return float(self.shift @ point), self.shift.copy(), np.zeros((3, 3))


class GeodesicTests(unittest.TestCase):
    def test_minkowski_null_speed_and_seconds(self):
        geometry = ConstantShiftGeometry([0, 0, 0])
        direction = np.array([3.0, 4.0, 0.0]) / 5
        result = integrate_null_ray(geometry, direction, final_ct_m=6, sample_count=13)
        self.assertEqual(result["status"], "finite_interval_complete")
        self.assertEqual(len(result["points"]), 13)
        for point in result["points"]:
            ct = point["t_s"] * geometry.c
            q = np.array([point["x_m"], point["y_m"], point["z_m"]])
            np.testing.assert_allclose(q, ct * direction, atol=2e-12)
        self.assertLess(result["max_null_residual"], 2e-14)

    def test_constant_shift_is_a_coordinate_change(self):
        geometry = ConstantShiftGeometry([2.0, 0.25, -0.1])
        direction = np.array([0.0, 1.0, 0.0])
        result = integrate_null_ray(geometry, direction, final_ct_m=5, sample_count=11)
        self.assertEqual(result["status"], "finite_interval_complete")
        for point in result["points"]:
            ct = point["t_s"] * geometry.c
            q = np.array([point["x_m"], point["y_m"], point["z_m"]])
            # In inertial coordinates q_lab=q+W*u, the ray travels at c.
            np.testing.assert_allclose(q + geometry.shift * ct, direction * ct, atol=3e-12)
            self.assertAlmostEqual(point["eulerian_frequency_ratio"], 1.0, places=13)

    def test_stopping_sphere_reports_finite_domain_only(self):
        result = integrate_null_ray(ConstantShiftGeometry([0, 0, 0]), [1, 0, 0],
                                    final_ct_m=6, sample_count=13, stop_radius_m=2.2)
        self.assertEqual(result["status"], "escaped")
        self.assertAlmostEqual(result["points"][-1]["x_m"], 2.2, places=11)
        self.assertEqual(result["event_radius_m"], 2.2)
        self.assertIn("no claim", result["status_description"])
        self.assertLess(len(result["points"]), 13)

    def test_invalid_direction_is_rejected(self):
        geometry = ConstantShiftGeometry([0, 0, 0])
        for direction in ([0, 0, 0], [float("nan"), 1, 0], [1, 0]):
            with self.assertRaises(ValueError):
                integrate_null_ray(geometry, direction)

    def test_failed_ray_keeps_an_honest_initial_sample(self):
        class UnresolvedGeometry(ConstantShiftGeometry):
            def fields(self, point):
                if np.linalg.norm(point) > 0.5:
                    raise FloatingPointError("Synthetic unresolved metric region")
                return super().fields(point)

        result = integrate_null_ray(UnresolvedGeometry([0, 0, 0]), [1, 0, 0],
                                    final_ct_m=6, sample_count=13)
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["integrator"]["success"])
        self.assertEqual(len(result["points"]), 1)
        self.assertEqual(result["points"][0]["t_s"], 0.0)
        self.assertIn("Synthetic unresolved", result["solver_message"])


if __name__ == "__main__":
    unittest.main()
