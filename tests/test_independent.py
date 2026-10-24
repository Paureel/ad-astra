"""Numerical controls for the independent metric-to-Einstein calculation."""
import json
import unittest

import numpy as np

from warpproof.geometry import Geometry
from warpproof.independent import (
    compare_invariant,
    crosscheck_geometry,
    direct_einstein_tensor,
)
from warpproof.model import ROOT, baseline_candidate, load_candidate


class LinearShiftMetric:
    """A metric-only fixture whose curvature need not vanish."""

    def __init__(self, matrix, offset):
        self.matrix = np.asarray(matrix, dtype=float)
        self.offset = np.asarray(offset, dtype=float)

    def metric(self, point):
        shift = self.matrix @ np.asarray(point) + self.offset
        value = np.eye(4)
        value[0, 0] = -1 + shift @ shift
        value[0, 1:] = shift
        value[1:, 0] = shift
        return value


class IndependentTensorTests(unittest.TestCase):
    def test_constant_shift_is_flat_and_normal_is_unit(self):
        geometry = LinearShiftMetric(np.zeros((3, 3)), [0.25, -0.4, 1.2])
        result = direct_einstein_tensor(geometry, [1.1, -2.2, 3.3])
        np.testing.assert_allclose(result.einstein, 0, atol=1e-12)
        np.testing.assert_allclose(result.normal, [1, -0.25, 0.4, -1.2], atol=1e-13)
        self.assertLess(result.normal_norm_residual, 1e-13)

    def test_quadratic_metric_matches_analytic_constraint(self):
        matrix = np.array([[0.07, 0.02, -0.01],
                           [0.02, -0.03, 0.015],
                           [-0.01, 0.015, 0.05]])
        # This fixture supplies no fields() or invariant() shortcut. A direct
        # tensor evaluation must use metric samples alone.
        geometry = LinearShiftMetric(matrix, [0.2, -0.3, 0.4])
        result = direct_einstein_tensor(geometry, [0.6, -0.8, 1.2], step_m=0.02)
        expected = np.trace(matrix)**2 - np.trace(matrix @ matrix)
        self.assertGreater(abs(expected), 1e-3)
        self.assertAlmostEqual(result.twice_Gnn_per_m2, expected, delta=2e-9)
        self.assertLess(result.ricci_symmetry_residual_per_m2, 1e-9)

    def test_actual_profile_refines_toward_reduced_invariant(self):
        geometry = Geometry(baseline_candidate())
        report = compare_invariant(geometry, [17, 6, 8])
        errors = [sample["absolute_residual_per_m2"] for sample in report["samples"]]
        self.assertTrue(report["passed"], report)
        self.assertLess(errors[-1], 0.15 * errors[0])
        self.assertTrue(all(order > 1.7 for order in report["observed_error_orders"]))

    def test_perturbed_candidate_crosscheck_is_explicitly_numerical(self):
        candidate = load_candidate(ROOT / "candidates" / "example-perturbation.json")
        report = crosscheck_geometry(Geometry(candidate))
        self.assertTrue(report["passed"], report)
        self.assertFalse(report["formal_certification"])
        self.assertEqual(report["status"], "numerical_only")
        self.assertEqual(len(report["checks"]), 5)
        json.dumps(report, allow_nan=False)

    def test_bad_steps_and_points_are_rejected(self):
        geometry = Geometry(baseline_candidate())
        with self.assertRaises(ValueError):
            direct_einstein_tensor(geometry, [1, 2, 3], step_m=0)
        with self.assertRaises(ValueError):
            direct_einstein_tensor(geometry, [1, np.nan, 3])
        with self.assertRaises(ValueError):
            compare_invariant(geometry, [1, 2, 3], steps_m=(0.01, 0.02))


if __name__ == "__main__":
    unittest.main()
