"""Whole-space numerical source-energy integrals with a retained algebraic tail.

Every return value is numerical_only. Quadrature error estimates and the
analytically derived tail remainder are not Lean-checked certificates.
"""
from __future__ import annotations

import math
import warnings
import numpy as np
from scipy.integrate import quad, IntegrationWarning
from numpy.polynomial import legendre as leg

from .geometry import Geometry, radial_profile


def baseline_radial_terms(r, geometry):
    if r == 0:
        return 0.0, 0.0
    _, _, fp, a, _ = radial_profile(r, geometry.radius, geometry.sigma)
    p, q = float(4*a*(a+fp)), float(2*a*a)
    h = q-p/3 if p <= q else p/3-q+4*q/3*math.sqrt(q/p)
    return r*r*h, r*r*(p/3-q)


def analytic_tail(geometry, start):
    """Leading 1/r tail plus a derived exponential remainder estimate.

    The inequality is documented in docs/MATHEMATICS.md; formal proof is open.
    Floating-point evaluation here is not outward-rounded interval arithmetic.
    """
    if start <= max(geometry.radius, geometry.outer if geometry.candidate.terms else 0):
        raise ValueError("Tail start must lie beyond the profile radius and every perturbation.")
    beta, R, sigma = geometry.beta, geometry.radius, geometry.sigma
    k = 1/math.tanh(sigma*R)
    C, lam = R*k, 2*sigma
    scale = geometry.c**4*beta**2/(6*geometry.G)
    absolute = scale*C*C/start*(2*math.sqrt(2)-1)
    signed = -scale*C*C/start
    remainder = (geometry.c**4*beta**2/(4*geometry.G))*C*k*math.exp(-lam*(start-R))*(
        4/3+20/(3*lam*start)+20/(3*lam*lam*start*start))
    return {"start_m": start, "absolute_J": absolute, "signed_J": signed,
            "analytic_remainder_bound_J": remainder,
            "formalized": False, "floating_point_rounding_certified": False}


def _integrate(function, edges, tol):
    total, error = 0.0, 0.0
    notes = []
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", IntegrationWarning)
        for a, b in zip(edges[:-1], edges[1:]):
            if b <= a:
                continue
            v, e = quad(function, a, b, epsabs=tol, epsrel=tol, limit=160)
            total += v
            error += e
        notes = [str(w.message) for w in captured]
    return total, error, notes


def baseline_energy(geometry, tail_start=None, tolerance=1e-9):
    if geometry.candidate.terms:
        raise ValueError("Use evaluate_energy for a perturbed candidate.")
    L = float(tail_start if tail_start is not None else 4*geometry.radius)
    edges = sorted(set([0., max(0., geometry.radius-8/geometry.sigma), geometry.radius,
                        min(L, geometry.radius+8/geometry.sigma), L]))
    edges = [e for e in edges if 0 <= e <= L]
    body, err, notes = _integrate(lambda r: baseline_radial_terms(r, geometry)[0], edges, tolerance)
    signed, sign_err, more = _integrate(lambda r: baseline_radial_terms(r, geometry)[1], edges, tolerance)
    factor = geometry.c**4*geometry.beta**2/(4*geometry.G)
    tail = analytic_tail(geometry, L)
    E_body, S_body = factor*body, factor*signed
    E, S = E_body+tail["absolute_J"], S_body+tail["signed_J"]
    return {"quantity": "absolute_eulerian_source_energy", "label": "Absolute Eulerian source energy",
        "value_J": E, "positive_J": (E+S)/2, "negative_J": (E-S)/2,
        "signed_J": S, "body_absolute_J": E_body, "body_signed_J": S_body,
        "body_positive_J": (E_body+S_body)/2, "body_negative_J": (E_body-S_body)/2,
        "error_estimate_J": factor*(err+sign_err)+tail["analytic_remainder_bound_J"],
        "error_kind": "adaptive quadrature estimate plus analytic tail remainder; not a rigorous total enclosure",
        "certified_bounds_J": None, "tail": tail, "warnings": notes+more,
        "method": "analytic angular integration; adaptive radial quadrature; algebraic tail with exponential remainder"}


def polynomial_absolute_integral(coefficients):
    """Numerical integral of |Legendre polynomial| on [-1,1] by real roots."""
    c = np.asarray(coefficients, dtype=float)
    scale = float(np.max(np.abs(c)))
    if scale == 0:
        return 0.0
    keep = np.flatnonzero(np.abs(c) > 2e-13*scale)
    c = c[:keep[-1]+1]
    roots = leg.legroots(c/scale) if len(c) > 1 else np.array([])
    knots = [-1.0]+sorted(float(z.real) for z in roots
                         if abs(z.imag) < 1e-7 and -1 < z.real < 1)+[1.0]
    primitive = leg.legint(c)
    return sum(abs(float(leg.legval(b, primitive)-leg.legval(a, primitive)))
               for a, b in zip(knots[:-1], knots[1:]))


class AngularIntegrator:
    """Axisymmetric invariant is angular polynomial for this restricted family.

    This implementation numerically interpolates the invariant, checks held-out
    nodes and integrates across polynomial roots. The degree reduction needs a
    formal bridge before it can support an official certificate.
    """
    def __init__(self, geometry, degree=10, nodes=18):
        self.geometry = geometry
        self.degree = degree
        self.mu, _ = leg.leggauss(nodes)
        self.fit = np.linalg.pinv(leg.legvander(self.mu, degree))
        self.test_mu = np.array([-0.987, -0.713, -0.201, 0.317, 0.809, 0.993])
        self.max_relative_residual = 0.0

    def coefficients(self, r):
        mu = self.mu
        points = np.column_stack((r*mu, r*np.sqrt(1-mu*mu), np.zeros_like(mu)))
        values = self.geometry.invariant(points)
        c = self.fit@values
        tm = self.test_mu
        checks = self.geometry.invariant(np.column_stack((r*tm, r*np.sqrt(1-tm*tm), np.zeros_like(tm))))
        residual = float(np.max(np.abs(leg.legval(tm, c)-checks)))/max(1e-24, float(np.max(np.abs(checks))))
        self.max_relative_residual = max(self.max_relative_residual, residual)
        if residual > 1e-7:
            raise ArithmeticError("Angular polynomial reconstruction failed its held-out numerical check.")
        return c

    def absolute(self, r):
        return r*r*polynomial_absolute_integral(self.coefficients(r))

    def signed(self, r):
        return r*r*2*float(self.coefficients(r)[0])


def evaluate_energy(geometry, tolerance=1e-8, refinement=False):
    from .model import baseline_candidate
    if not geometry.candidate.terms:
        return baseline_energy(geometry, tolerance=tolerance)
    reference = Geometry(baseline_candidate())
    out = baseline_energy(reference, tolerance=tolerance)
    angular = AngularIntegrator(geometry, degree=12 if refinement else 10, nodes=24 if refinement else 18)
    knots = sorted(set([geometry.inner, geometry.radius-3/geometry.sigma, geometry.radius,
                        geometry.radius+3/geometry.sigma, 30., geometry.outer]))
    knots = [r for r in knots if geometry.inner <= r <= geometry.outer]
    shell, err, warnings1 = _integrate(angular.absolute, knots, tolerance)
    signed, sign_err, warnings2 = _integrate(angular.signed, knots, tolerance)
    old_shell, old_err, _ = _integrate(lambda r: 2*geometry.beta**2*baseline_radial_terms(r, reference)[0], knots, tolerance)
    old_signed, old_sign_err, _ = _integrate(lambda r: 2*geometry.beta**2*baseline_radial_terms(r, reference)[1], knots, tolerance)
    factor = geometry.c**4/(8*geometry.G)
    delta, delta_signed = factor*(shell-old_shell), factor*(signed-old_signed)
    out["value_J"] += delta
    out["body_absolute_J"] += delta
    out["signed_J"] += delta_signed
    out["body_signed_J"] += delta_signed
    E, S = out["value_J"], out["signed_J"]
    out["positive_J"], out["negative_J"] = (E+S)/2, (E-S)/2
    out["body_positive_J"] = (out["body_absolute_J"]+out["body_signed_J"])/2
    out["body_negative_J"] = (out["body_absolute_J"]-out["body_signed_J"])/2
    out["error_estimate_J"] += factor*(err+sign_err+old_err+old_sign_err)
    out["angular_max_relative_residual"] = angular.max_relative_residual
    out["warnings"] += warnings1+warnings2
    out["method"] = "axisymmetric angular polynomial root integration; adaptive radial quadrature; unchanged analytic tail"
    return out

