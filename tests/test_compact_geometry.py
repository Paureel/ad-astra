"""Field, boundary, parser, and independent GR regressions for compact100."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.compact100.geometry import CompactGeometry, CANDIDATE, EXPECTED_HASH, decode
from warpproof.independent import compare_invariant, direct_einstein_tensor
from research.compact100.physics import candidate_jet_model, reference_jet, curvature_fields
from research.compact100.validate import check_sources


class CompactGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = CompactGeometry()

    def test_exact_input_and_endpoint_control_rejection(self):
        check_sources()
        data, radial, angular, coefficients, digest = decode()
        self.assertEqual(digest, EXPECTED_HASH)
        self.assertEqual((len(coefficients), len(coefficients[0])), (32, 46))
        self.assertEqual((len(set(radial))-1, len(set(angular))-1), (40, 26))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"candidate.json"
            for change in ("endpoint", "schema", "certification"):
                item = json.loads(CANDIDATE.read_text())
                if change == "endpoint": item["coefficients"][0][0] = "1"
                if change == "schema": item["score_override"] = "0"
                if change == "certification": item["formal_certification"] = True
                path.write_text(json.dumps(item))
                with self.assertRaises(ValueError): decode(path)
            path.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaises(ValueError): decode(path)

    def test_original_closed_cabin_is_unchanged(self):
        points = np.array([[0., 0., 0.], [8., 0., 0.], [-10., 0., 0.],
                           [0., 10., 0.], [6., 0., 8.], [2.1, -3.7, 5.9]])
        actual = self.geometry.fields(points)
        original = self.geometry.reference.fields(points)
        for a, b in zip(actual, original):
            np.testing.assert_array_equal(a, b)

    def test_flat_exterior_and_regular_axis(self):
        points = np.array([[100., 0., 0.], [-100., 0., 0.], [0., 101., 0.],
                           [1e6, 2e6, -3e6]])
        phi, w, h = self.geometry.fields(points)
        np.testing.assert_array_equal(phi, 2*points[:, 0])
        np.testing.assert_array_equal(w, np.tile([2., 0., 0.], (len(points), 1)))
        np.testing.assert_array_equal(h, np.zeros_like(h))
        jacobian = np.eye(4); jacobian[1, 0] = -2
        np.testing.assert_array_equal(jacobian.T@self.geometry.metric(points[0])@jacobian,
                                      np.diag([-1., 1., 1., 1.]))
        for p in [[11., 0., 0.], [-11., 0., 0.], [17., 0., 0.], [-17., 0., 0.]]:
            self.assertTrue(all(np.all(np.isfinite(v)) for v in self.geometry.fields(p)))
            self.assertAlmostEqual(np.linalg.det(self.geometry.metric(p)), -1., places=12)

    def test_cartesian_derivatives_of_the_actual_potential(self):
        for point in np.array([[12.5, 2., 1.], [14.2, -4.1, 2.7], [-17., 3.2, 4.7], [35., -21., 8.]]):
            phi, w, h = self.geometry.fields(point)
            step = 1e-4
            offsets = np.eye(3)*step
            wp = self.geometry.fields(point+offsets)[1]
            wm = self.geometry.fields(point-offsets)[1]
            fd_h = ((wp-wm)/(2*step)).T
            pp = self.geometry.fields(point+offsets)[0]
            pm = self.geometry.fields(point-offsets)[0]
            np.testing.assert_allclose((pp-pm)/(2*step), w, rtol=3e-6, atol=2e-8)
            np.testing.assert_allclose(fd_h, h, rtol=3e-5, atol=2e-8)

    def test_axisymmetric_covariance(self):
        angle = .713
        rotation = np.array([[1., 0., 0.], [0., np.cos(angle), -np.sin(angle)],
                              [0., np.sin(angle), np.cos(angle)]])
        point = np.array([15.3, 4.1, -2.7])
        phi, w, h = self.geometry.fields(point)
        p2, w2, h2 = self.geometry.fields(rotation@point)
        self.assertAlmostEqual(phi, p2, places=12)
        np.testing.assert_allclose(w2, rotation@w, atol=1e-12)
        np.testing.assert_allclose(h2, rotation@h@rotation.T, atol=1e-12)

    def test_independent_metric_einstein_calculation(self):
        for point in [[12.5, 2., 1.], [-17., 3.2, 4.7], [35., -21., 8.]]:
            result = compare_invariant(self.geometry, point, steps_m=(.02, .01, .005),
                                       relative_tolerance=5e-4, absolute_tolerance_per_m2=1e-7)
            self.assertTrue(result["passed"], result)

    def test_physics_jets_and_stress_against_cartesian_metric(self):
        model = candidate_jet_model()
        for radius, mu in [(13.67, -.87), (21.2, .37), (67.3, -.21)]:
            sine = np.sqrt(1-mu*mu)
            rotation = np.array([[mu, -sine, 0.], [sine, mu, 0.], [0., 0., 1.]])
            point = radius*rotation[:, 0]
            for geometry, jet in [(self.geometry, model.spherical_jet([radius], [mu])),
                                  (self.geometry.reference, reference_jet([radius], [mu]))]:
                jet = {k: jet[k][0, 0] for k in ("W", "H", "T")}
                _, w, h = geometry.fields(point)
                np.testing.assert_allclose(rotation@jet["W"], w, atol=2e-13)
                np.testing.assert_allclose(rotation@jet["H"]@rotation.T, h, atol=2e-13)
                step = 1e-4
                fd = (geometry.fields(point+np.eye(3)*step)[2]
                      - geometry.fields(point-np.eye(3)*step)[2])/(2*step)
                cartesian_third = np.einsum("ai,bj,ck,ijk->cab", rotation, rotation, rotation, jet["T"])
                np.testing.assert_allclose(cartesian_third, fd, rtol=3e-5, atol=2e-8)
                density, stress, _, scalar = curvature_fields(jet)
                direct = direct_einstein_tensor(geometry, point, step_m=.001)
                np.testing.assert_allclose(rotation@stress@rotation.T, direct.einstein[1:, 1:],
                                           rtol=5e-4, atol=2e-6)
                self.assertAlmostEqual(density, direct.twice_Gnn_per_m2/2, delta=2e-6)
                self.assertAlmostEqual(scalar, direct.scalar_curvature_per_m2, delta=1e-5)


if __name__ == "__main__": unittest.main()
