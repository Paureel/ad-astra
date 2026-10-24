# SPDX-License-Identifier: Apache-2.0
"""Conditional compact/tail energy bounds, with exact rational log enclosures.

These evaluate the formulas in the submitted report. They do not certify a
candidate, establish a GR bridge in Lean, or modify the frozen benchmark.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from fractions import Fraction as F
from functools import lru_cache
from math import isqrt

C = F(299792458)
G = F(66743, 10**15)
A = F(10)
BETA = F(2)
EPSILON = F(1, 10**6)
REFERENCE_REPORTED = (F("4.249035252e45"), F("4.251126101e45"))
CANDIDATE_REPORTED_UPPER = F("1.545308012e45")


@lru_cache(maxsize=256)
def _log_series(x: F, terms: int) -> tuple[F, F]:
    if not F(1) <= x <= F(2) or terms < 1:
        raise ValueError("Series argument must be in [1,2], with positive terms.")
    z = (x - 1) / (x + 1)
    power, total = z, F(0)
    for k in range(terms):
        total += 2 * power / (2*k + 1)
        power *= z*z
    remainder = 2*power / ((2*terms + 1)*(1-z*z))
    return total, total + remainder


def log_interval(x: F, terms: int = 32) -> tuple[F, F]:
    """Enclose natural log(x) by atanh series and exact powers-of-two reduction."""
    x = F(x)
    if x <= 0:
        raise ValueError("Logarithm requires a positive rational argument.")
    k = 0
    while x >= 2:
        x /= 2
        k += 1
    while x < 1:
        x *= 2
        k -= 1
    lo, hi = _log_series(x, terms)
    l2, u2 = _log_series(F(2), terms)
    return (lo + k*l2, hi + k*u2) if k >= 0 else (lo + k*u2, hi + k*l2)


def sqrt_interval(x: F, digits: int = 40) -> tuple[F, F]:
    if x < 0 or digits < 1:
        raise ValueError("Use a nonnegative argument and positive precision.")
    scale = 10**digits
    lo = F(isqrt(x.numerator*scale*scale // x.denominator), scale)
    return (lo, lo) if lo*lo == x else (lo, lo + F(1, scale))


def _parameters(a, radius, beta, epsilon):
    a, radius, beta, epsilon = map(F, (a, radius, beta, epsilon))
    if not (a > 0 and radius > a and beta > epsilon >= 0):
        raise ValueError("Require radius > cabin > 0 and beta > epsilon >= 0.")
    return a, radius, beta - epsilon


def compact_floor(radius: F, a=A, beta=BETA, epsilon=EPSILON) -> tuple[F, F]:
    """Enclosure of the conditional lower-bound formula, not of actual energy."""
    a, radius, b = _parameters(a, radius, beta, epsilon)
    llo, lhi = log_interval(radius/a)
    numerator = C**4*b*b*a*radius / (3*G*(radius-a))
    return numerator/lhi, numerator/llo


def tail_floor(radius: F, surface_mean: F, a=A, beta=BETA, epsilon=EPSILON) -> tuple[F, F]:
    """Strengthened conditional formula retaining the outer tangential term.

    surface_mean is an upper bound on (1/4pi) integral |grad_S psi(R)|^2.
    This bound must be supplied and justified separately for a real candidate.
    """
    a, radius, b = _parameters(a, radius, beta, epsilon)
    s = F(surface_mean)
    if s < 0:
        raise ValueError("The squared surface mean cannot be negative.")
    slo, shi = sqrt_interval(3*s/2)
    base = b*b*a/3 - s/(2*radius)
    blo = max(F(0), base + max(F(0), b*a-shi)**2/(3*(radius-a)))
    bhi = max(F(0), base + max(F(0), b*a-slo)**2/(3*(radius-a)))
    llo, lhi = log_interval(radius/a)
    return C**4*blo/(G*lhi), C**4*bhi/(G*llo)


def radius_lhs(radius: F, a=A, terms=32) -> tuple[F, F]:
    radius, a = F(radius), F(a)
    if radius < a or a <= 0:
        raise ValueError("Require radius >= cabin > 0.")
    lo, hi = log_interval(radius/a, terms)
    return (1-a/radius)*lo, (1-a/radius)*hi


def necessary_radius(factor: F, iterations=80, reference_upper=None) -> tuple[F, F]:
    """Enclose the radius root conditional on the PDF's reference upper bound."""
    if factor <= 0 or iterations < 1:
        raise ValueError("Use a positive reduction factor and iteration count.")
    reference_upper = REFERENCE_REPORTED[1] if reference_upper is None else F(reference_upper)
    if reference_upper <= 0:
        raise ValueError("The reference energy upper endpoint must be positive.")
    target = C**4*(BETA-EPSILON)**2*A*F(factor)/(3*G*reference_upper)
    lo, hi = A, 2*A
    while radius_lhs(hi)[1] < target:
        hi *= 2
    if radius_lhs(hi)[0] <= target:
        hi *= 2
    for _ in range(iterations):
        mid, terms = (lo+hi)/2, 32
        while True:
            lower, upper = radius_lhs(mid, terms=terms)
            if upper < target:
                lo = mid
                break
            if lower > target:
                hi = mid
                break
            terms *= 2
    return lo, hi


def outward(interval: tuple[F, F], digits=40) -> dict[str, str]:
    result = {}
    for name, value, rounding in zip(("lower", "upper"), interval, (ROUND_FLOOR, ROUND_CEILING)):
        with localcontext() as ctx:
            ctx.prec = digits
            ctx.rounding = rounding
            result[name] = str(Decimal(value.numerator)/Decimal(value.denominator))
    return result
