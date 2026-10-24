"""Independent arithmetic, boundary-term, and cutoff-core checks."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import unittest

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import betainc

from research.compact100.bounds import (C, G, A, BETA, EPSILON, REFERENCE_REPORTED,
    log_interval, sqrt_interval, compact_floor, tail_floor, necessary_radius,
    radius_lhs, outward)
from research.compact100.audit import core_energy, core_profile
from warpproof.geometry import Geometry
from warpproof.model import baseline_candidate


def evaluate(p, x):
    return sum(c*x**i for i, c in enumerate(p))


def derivative(p):
    return [i*c for i, c in enumerate(p)][1:]


def multiply(a, b):
    out = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return out


def integrate(p, a, b):
    return sum(c*(b**(i+1)-a**(i+1))/(i+1) for i, c in enumerate(p))


class CompactBoundsTests(unittest.TestCase):
    def test_rational_logs_against_independent_decimal_ln(self):
        with localcontext() as ctx:
            ctx.prec = 90
            for x in [F(1, 100), F(1), F(2), F(10), F(10**166), 1+F(1, 10**20)]:
                lo, hi = log_interval(x)
                reference = (Decimal(x.numerator)/Decimal(x.denominator)).ln()
                dl = Decimal(lo.numerator)/Decimal(lo.denominator)
                du = Decimal(hi.numerator)/Decimal(hi.denominator)
                self.assertLessEqual(dl, reference)
                self.assertGreaterEqual(du, reference)
                coarse = log_interval(x, terms=16)
                self.assertLessEqual(coarse[0], lo)
                self.assertGreaterEqual(coarse[1], hi)

    def test_square_root_and_outward_rounding(self):
        for x in [F(0), F(1, 4), F(1600), F(3201, 2)]:
            lo, hi = sqrt_interval(x)
            self.assertLessEqual(lo*lo, x)
            self.assertGreaterEqual(hi*hi, x)
        decimals = outward((F(1, 3), F(1, 3)), digits=18)
        self.assertLess(F(decimals["lower"]), F(1, 3))
        self.assertGreater(F(decimals["upper"]), F(1, 3))

    def test_floor_and_outer_tangential_term(self):
        previous = None
        for r in [F(100), F(300), F(500), F(1000), F(1000000)]:
            interval = compact_floor(r)
            self.assertEqual(interval, tail_floor(r, F(0)))
            if previous is not None:
                self.assertLess(interval[1], previous[0])
            previous = interval
        lo, hi = compact_floor(F(100))
        self.assertGreater(lo, F("0.778676722e45"))
        self.assertLess(hi, F("0.778676723e45"))
        self.assertGreater(tail_floor(F(150), F(1067))[0], F("0.436928720e45"))
        self.assertEqual(tail_floor(F(100), F(10**6)), (F(0), F(0)))
        for radius in [F(0), A-1, A]:
            with self.assertRaises(ValueError):
                compact_floor(radius)
        with self.assertRaises(ValueError):
            tail_floor(F(100), F(-1))

    def test_necessary_radius_brackets_are_proved_by_intervals(self):
        for factor, rough_lower, rough_upper in [(10, F(482), F(483)), (100, F("3e17"), F("3.1e17"))]:
            lo, hi = necessary_radius(F(factor))
            target = C**4*(BETA-EPSILON)**2*A*factor/(3*G*REFERENCE_REPORTED[1])
            self.assertLess(radius_lhs(lo)[1], target)
            self.assertGreater(radius_lhs(hi)[0], target)
            self.assertGreater(lo, rough_lower)
            self.assertLess(hi, rough_upper)

    def test_cutoff_exact_endpoint_jets(self):
        p = [F(0)]*6 + list(map(F, [462, -1980, 3465, -3080, 1386, -252]))
        self.assertEqual(evaluate(p, F(0)), 0)
        self.assertEqual(evaluate(p, F(1)), 1)
        dp = p
        for _ in range(5):
            dp = derivative(dp)
            self.assertEqual(evaluate(dp, F(0)), 0)
            self.assertEqual(evaluate(dp, F(1)), 0)
        # Independent polynomial versus positive Bernstein/beta evaluation.
        for t in [F(1, 5), F(1, 2), F(4, 5)]:
            self.assertAlmostEqual(1-float(evaluate(p, t)), betainc(6, 6, 1-float(t)), places=14)

    def test_nonzero_outer_boundary_term_is_required(self):
        # For psi=r*f(r)*mu, the radial+interface identity reduces exactly to
        # int(f+r*f')^2 + a*f(a)^2 - R*f(R)^2 = int r^2*f'^2.
        a, radius = F(2), F(5)
        for k in range(1, 13):
            p = [F(k, 7), F((-1)**k*k, 11), F((k % 3)-1, 13)]
            dp = derivative(p)
            radial_derivative = [(i+1)*c for i, c in enumerate(p)]
            radial = integrate(multiply(radial_derivative, radial_derivative), a, radius)
            inner = a*evaluate(p, a)**2
            outer = radius*evaluate(p, radius)**2
            rhs = integrate([F(0), F(0)]+multiply(dp, dp), a, radius)
            self.assertEqual(radial+inner-outer, rhs)
            self.assertNotEqual(outer, 0)
            self.assertNotEqual(radial+inner, rhs)

    def test_core_against_cartesian_hessian_quadrature(self):
        geometry = Geometry(baseline_candidate())
        mu, wm = leggauss(512)
        z, wz = leggauss(384)
        total, signed = 0., 0.
        for left, right in [(0, 10), (10, 11)]:
            r = left+(right-left)*(z+1)/2
            rr, mm = np.meshgrid(r, mu, indexing="ij")
            points = np.stack([rr*mm, rr*np.sqrt(1-mm*mm), np.zeros_like(rr)], axis=-1)
            phi, w, h = geometry.fields(points)
            n = points/rr[..., None]
            t = np.clip(rr-10, 0, 1)
            eta = betainc(6, 6, 1-t)
            ep = -2772*t**5*(1-t)**5
            epp = -13860*t**4*(1-t)**4*(1-2*t)
            nn = n[..., :, None]*n[..., None, :]
            hc = (eta[..., None, None]*h
                + ep[..., None, None]*(n[..., :, None]*w[..., None, :]+w[..., :, None]*n[..., None, :])
                + phi[..., None, None]*(epp[..., None, None]*nn+(ep/rr)[..., None, None]*(np.eye(3)-nn)))
            q = np.trace(hc, axis1=-2, axis2=-1)**2-np.sum(hc*hc, axis=(-2, -1))
            weights = (wz*(right-left)/2*r*r)[:, None]*wm[None, :]
            total += float(np.sum(weights*np.abs(q)))
            signed += float(np.sum(weights*q))
        energy = total*float(C**4/(8*G))
        reference = core_energy()
        self.assertLess(abs(energy/reference["absolute_energy_J"]-1), 3e-5)
        self.assertLess(abs(signed)/total, 1e-11)
        self.assertLess(reference["absolute_energy_J"], 7.47e28)
        self.assertIsNone(reference["certified_bounds_J"])
        g, gp, gpp = core_profile(np.array([11., 12., 100.]))
        self.assertTrue(all(np.all(v == 0) for v in (g, gp, gpp)))


if __name__ == "__main__":
    unittest.main()
