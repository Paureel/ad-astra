"""Numerical physics regressions, not continuum proofs or energy certificates.

The published comparison uses Rodal, arXiv:2512.18008v1, Table 6, with its
finite spherical integration radius of 60 m. Whole-space values also retain
the algebraic exterior tail, so they must not be compared directly to that table.
"""
from fractions import Fraction
import math
import unittest

import numpy as np

from warpproof.energy import (
    AngularIntegrator,
    analytic_tail,
    baseline_energy,
    baseline_radial_terms,
)
from warpproof.geometry import Geometry, radial_profile
from warpproof.model import baseline_candidate, make_candidate


class PublishedEnergyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidate = baseline_candidate()
        cls.standard = Geometry(candidate)
        cls.paper = Geometry(candidate, radius=5, sigma=4, beta=1)
        cls.paper_energy = baseline_energy(cls.paper, tail_start=60, tolerance=1e-10)
        cls.standard_energy = baseline_energy(cls.standard, tail_start=80, tolerance=1e-10)

    def test_published_table_6_finite_domain_values(self):
        # Rounded published numerical figures, not exact mathematical constants.
        # https://arxiv.org/html/2512.18008v1#S5.T6
        published = {
            "body_positive_J": 1.29e44,
            "body_negative_J": 1.21e44,
            "body_absolute_J": 2.50e44,
            "body_signed_J": 8.37e42,
        }
        for key, value in published.items():
            with self.subTest(quantity=key):
                relative_difference = abs(self.paper_energy[key] / value - 1)
                self.assertLessEqual(relative_difference, 0.005)
        self.assertGreater(self.paper_energy["value_J"], self.paper_energy["body_absolute_J"])
        self.assertIsNone(self.paper_energy["certified_bounds_J"])

    def test_whole_space_energy_and_tail_scale_as_beta_squared_times_radius(self):
        # Both profiles have sigma*R=20. Increasing R by 4 and beta by 2
        # multiplies any geometrically corresponding energy integral by 16.
        scale = (self.standard.beta / self.paper.beta) ** 2 * (
            self.standard.radius / self.paper.radius
        )
        self.assertAlmostEqual(
            self.standard_energy["value_J"] / self.paper_energy["value_J"],
            scale,
            delta=scale * 2e-10,
        )
        original_tail = analytic_tail(self.paper, 4 * self.paper.radius)
        normalized_tail = analytic_tail(self.standard, 4 * self.standard.radius)
        for quantity in ("absolute_J", "signed_J"):
            with self.subTest(quantity=quantity):
                self.assertAlmostEqual(
                    normalized_tail[quantity] / original_tail[quantity],
                    scale,
                    delta=scale * 2e-13,
                )

    def test_moving_tail_boundary_preserves_whole_space_energy(self):
        first = self.standard_energy
        second = baseline_energy(self.standard, tail_start=120, tolerance=1e-10)
        E = first["value_J"]
        self.assertLess(abs(second["value_J"] - E) / E, 2e-10)
        # This is a material tail contribution, so agreement is not the result
        # of both runs silently discarding an already negligible exterior.
        self.assertGreater(first["tail"]["absolute_J"] / E, 0.1)
        transferred = second["body_absolute_J"] - first["body_absolute_J"]
        removed_tail = first["tail"]["absolute_J"] - second["tail"]["absolute_J"]
        self.assertGreater(transferred, 0)
        self.assertLess(abs(transferred - removed_tail) / E, 2e-10)
        # The vanishing whole-space signed integral is a separate analytic
        # identity; using it here catches missed angular factors and tail signs.
        for result in (first, second, self.paper_energy):
            with self.subTest(tail_start=result["tail"]["start_m"]):
                self.assertLess(abs(result["signed_J"]) / result["value_J"], 2e-10)

    def test_zero_speed_reference_is_flat_and_has_zero_source_energy(self):
        flat = Geometry(baseline_candidate(), beta=0)
        points = np.array([[0., 0., 0.], [19., 6., -5.], [80., -5., 11.]])
        for field in flat.fields(points):
            np.testing.assert_array_equal(field, np.zeros_like(field))
        result = baseline_energy(flat)
        self.assertEqual(result["value_J"], 0)
        self.assertEqual(result["signed_J"], 0)
        np.testing.assert_array_equal(flat.metric(points[1]), np.diag([-1., 1., 1., 1.]))


class GeometricConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = Geometry(baseline_candidate())
        # Include radial, odd longitudinal, and angular terms so a purely
        # radial implementation cannot accidentally pass all derivative checks.
        cls.perturbed = Geometry(make_candidate({
            (0, 0): Fraction(1, 40),
            (1, 0): Fraction(-1, 50),
            (2, 1): Fraction(1, 80),
            (0, 2): Fraction(-1, 100),
        }, name="geometry-test-fixture"))

    def test_origin_is_regular_and_has_correct_small_radius_limit(self):
        for geometry in (self.baseline, self.perturbed):
            for field in geometry.fields(np.zeros(3)):
                np.testing.assert_array_equal(field, np.zeros_like(field))
        # A broader paper-family profile makes the origin limit measurable
        # without the extremely small central coefficient of sigma*R=20.
        R, sigma = 2., 0.6
        radii = np.array([1e-7, 2e-7, 4e-7])
        f, g, fp, gp, gpp = radial_profile(radii, radius=R, sigma=sigma)
        coefficient = sigma ** 2 / math.cosh(sigma * R) ** 2
        np.testing.assert_allclose(f / radii ** 2, coefficient, rtol=1e-12)
        np.testing.assert_allclose(g / radii ** 2, coefficient / 3, rtol=1e-12)
        np.testing.assert_allclose(fp / radii, 2 * coefficient, rtol=1e-12)
        np.testing.assert_allclose(gp / radii, 2 * coefficient / 3, rtol=1e-12)
        np.testing.assert_allclose(gpp, 2 * coefficient / 3, rtol=1e-12)

    def test_analytic_shift_and_hessian_match_cartesian_finite_differences(self):
        points = np.array([[19., 6., -5.], [12., 11., 13.], [33., -4., 11.]])
        step = 1e-4
        for geometry in (self.baseline, self.perturbed):
            with self.subTest(candidate=geometry.candidate.id):
                _, W, H = geometry.fields(points)
                potential_derivatives = []
                shift_derivatives = []
                for direction in np.eye(3):
                    plus = geometry.fields(points + step * direction)
                    minus = geometry.fields(points - step * direction)
                    potential_derivatives.append((plus[0] - minus[0]) / (2 * step))
                    shift_derivatives.append((plus[1] - minus[1]) / (2 * step))
                numeric_W = np.stack(potential_derivatives, axis=-1)
                numeric_H = np.stack(shift_derivatives, axis=-1)
                np.testing.assert_allclose(W, numeric_W, rtol=3e-6, atol=2e-9)
                np.testing.assert_allclose(H, numeric_H, rtol=3e-6, atol=2e-9)
                np.testing.assert_allclose(H, np.swapaxes(H, -1, -2), rtol=0, atol=1e-14)

    def test_compact_perturbation_preserves_cabin_tail_and_joins(self):
        points = np.array([
            [0., 0., 0.], [0., 0., 8.], [0., 10., 0.],
            [40., 0., 0.], [-50., 0., 0.], [0., 0., 80.],
        ])
        for perturbed, reference in zip(self.perturbed.fields(points), self.baseline.fields(points)):
            np.testing.assert_array_equal(perturbed, reference)
        # Hessian corrections must approach zero at both compact joins.
        # These samples supplement the formal polynomial endpoint fixtures;
        # finite sampling itself does not prove global C5 regularity.
        direction = np.array([2., -3., 6.]) / 7
        for boundary, sign in ((10., 1), (40., -1)):
            corrections = []
            for offset in (0.25, 0.125):
                point = (boundary + sign * offset) * direction
                corrections.append(np.linalg.norm(
                    self.perturbed.fields(point)[2] - self.baseline.fields(point)[2]
                ))
            with self.subTest(boundary=boundary):
                self.assertGreater(corrections[0], 0)
                self.assertLess(corrections[1], 0.15 * corrections[0])

    def test_closed_radial_angular_integral_matches_generic_polynomial_route(self):
        generic = AngularIntegrator(self.baseline)
        for radius in (10., 19., 20., 22., 40., 80.):
            absolute, signed = baseline_radial_terms(radius, self.baseline)
            scale = 2 * self.baseline.beta ** 2  # [-1,1] versus [0,1].
            with self.subTest(radius=radius):
                np.testing.assert_allclose(generic.absolute(radius), scale * absolute,
                                           rtol=2e-10, atol=1e-23)
                np.testing.assert_allclose(generic.signed(radius), scale * signed,
                                           rtol=2e-10, atol=1e-23)

    def test_baseline_contains_both_positive_and_negative_density(self):
        density = self.baseline.density(np.array([[30., 0., 0.], [0., 30., 0.], [0., 0., 0.]]))
        self.assertGreater(density[0], 0)
        self.assertLess(density[1], 0)
        self.assertEqual(density[2], 0)


if __name__ == "__main__":
    unittest.main()
