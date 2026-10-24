"""Published irrotational geometry plus compact scalar-potential perturbations.

Coordinates q are comoving metres and u=ct is measured in metres. The convention
is ds²=-du²+|dq+W du|², W=grad(Phi). It gives the exterior transformation
x_lab=q_x+beta*u. No material evolution is being simulated.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .model import Candidate, benchmark, exact


def logcosh(x):
    x = np.asarray(x, dtype=float)
    a = np.abs(x)
    return a + np.log1p(np.exp(-2*a)) - math.log(2)


def logsinh_positive(x):
    x = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return x + np.log(-np.expm1(-2*x)) - math.log(2)


def radial_profile(r, radius=20.0, sigma=1.0):
    """Return f=1-F, g, f', g', g'' using stable forms of Rodal Eqs.14,59.

    An origin Taylor expansion is used for sigma*r<1e-3. This is a numerical
    approximation, documented and tested; it is not a transcendental certificate.
    """
    rr = np.asarray(r, dtype=float)
    if np.any(rr < 0) or radius <= 0 or sigma <= 0:
        raise ValueError("Nonnegative radii and positive shape parameters required.")
    a, b = sigma*radius, sigma*rr
    t = math.tanh(a)
    if t == 0:
        raise ValueError("Degenerate profile.")
    den_log = np.logaddexp(logcosh(2*a), logcosh(2*b))
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        f = np.exp(math.log(2) + 2*logsinh_positive(b) - den_log)
        df = np.exp(math.log(2*sigma) + logsinh_positive(2*b)
                    + np.logaddexp(logcosh(2*a), 0.0) - 2*den_log)
        lp = lambda x: np.log1p(np.exp(-2*np.abs(x)))
        tm = -2*math.exp(-2*a)/(1+math.exp(-2*a))
        r_safe = np.where(rr == 0, 1.0, rr)
        g_in = tm/t + (lp(a-b)-lp(a+b))/(2*sigma*r_safe*t)
        integral_F = radius/t + (lp(a+b)-lp(b-a))/(2*sigma*t)
        g_out = 1-integral_F/r_safe
        g = np.where(rr <= radius, g_in, g_out)
        gp = (f-g)/r_safe
        gpp = df/r_safe-2*gp/r_safe
    small = b < 1e-3
    sech2 = 4*math.exp(-2*a)/(1+math.exp(-2*a))**2
    k2 = sigma**2*sech2
    k4 = sigma**4*sech2*(1/3-sech2)
    k6 = sigma**6*sech2*(2/45-2*sech2/3+sech2**2)
    f = np.where(small, k2*rr**2+k4*rr**4+k6*rr**6, f)
    g = np.where(small, k2*rr**2/3+k4*rr**4/5+k6*rr**6/7, g)
    df = np.where(small, 2*k2*rr+4*k4*rr**3+6*k6*rr**5, df)
    gp = np.where(small, 2*k2*rr/3+4*k4*rr**3/5+6*k6*rr**5/7, gp)
    gpp = np.where(small, 2*k2/3+12*k4*rr**2/5+30*k6*rr**4/7, gpp)
    return f, g, df, gp, gpp


@dataclass
class Jet2:
    """Second-order forward differentiation for polynomial perturbations only."""
    v: np.ndarray
    d: np.ndarray
    h: np.ndarray

    @staticmethod
    def constant(value):
        v = np.asarray(value, dtype=float)
        return Jet2(v, np.zeros(v.shape+(3,)), np.zeros(v.shape+(3, 3)))

    @staticmethod
    def variable(value, index):
        z = Jet2.constant(value)
        z.d[..., index] = 1
        return z

    @staticmethod
    def lift(other):
        return other if isinstance(other, Jet2) else Jet2.constant(other)

    def __add__(self, other):
        b = self.lift(other)
        return Jet2(self.v+b.v, self.d+b.d, self.h+b.h)

    __radd__ = __add__

    def __neg__(self):
        return Jet2(-self.v, -self.d, -self.h)

    def __sub__(self, other):
        return self + (-self.lift(other))

    def __rsub__(self, other):
        return self.lift(other) + (-self)

    def __mul__(self, other):
        b = self.lift(other)
        cross = np.einsum("...i,...j->...ij", self.d, b.d)
        return Jet2(self.v*b.v,
                    self.d*b.v[..., None]+b.d*self.v[..., None],
                    self.h*b.v[..., None, None]+b.h*self.v[..., None, None]
                    +cross+np.swapaxes(cross, -1, -2))

    __rmul__ = __mul__

    def __truediv__(self, scalar):
        if not np.isscalar(scalar) or scalar == 0:
            raise ValueError("Jet division supports only nonzero scalar constants.")
        return self*(1/float(scalar))

    def __pow__(self, n):
        if type(n) is not int or n < 0:
            raise ValueError("Jet powers must be nonnegative integers.")
        out = Jet2.constant(np.ones_like(self.v))
        base = self
        while n:
            if n & 1:
                out = out*base
            base = base*base
            n >>= 1
        return out


class Geometry:
    def __init__(self, candidate: Candidate, *, beta=None, radius=None, sigma=None):
        self.candidate = candidate
        spec = benchmark()
        p = spec["parameters"]
        self.beta = float(exact(p["speed_c"])) if beta is None else float(beta)
        self.radius = float(exact(p["profile_radius_m"])) if radius is None else float(radius)
        self.sigma = float(exact(p["sigma_per_m"])) if sigma is None else float(sigma)
        self.inner = float(exact(spec["family"]["inner_support_m"]))
        self.outer = float(exact(spec["family"]["outer_support_m"]))
        self.c = float(exact(spec["constants"]["c_m_s"]))
        self.G = float(exact(spec["constants"]["G_m3_kg_s2"]))
        self.density_factor = self.c**4/(16*math.pi*self.G)
        if candidate.terms and (beta is not None or radius is not None or sigma is not None):
            raise ValueError("Parameter overrides are reserved for unperturbed paper-reproduction fixtures.")

    def fields(self, points):
        """Return potential, W, and DW=Hess(Phi), preserving leading dimensions."""
        original = np.asarray(points, dtype=float)
        if original.shape[-1:] != (3,) or not np.all(np.isfinite(original)):
            raise ValueError("Points must be finite with a trailing Cartesian dimension of three.")
        shape = original.shape[:-1]
        q = original.reshape(-1, 3)
        r = np.linalg.norm(q, axis=1)
        safe_r = np.where(r == 0, 1.0, r)
        n = q/safe_r[:, None]
        _, g, _, gp, gpp = radial_profile(r, self.radius, self.sigma)
        e = np.array([1., 0., 0.])
        nn = np.einsum("ni,nj->nij", n, n)
        phi = self.beta*q[:, 0]*g
        W = self.beta*(g[:, None]*e+q[:, 0, None]*gp[:, None]*n)
        K = self.beta*(gp[:, None, None]*(np.einsum("i,nj->nij", e, n)
                        +np.einsum("ni,j->nij", n, e))
            +q[:, 0, None, None]*(gpp[:, None, None]*nn
                +(gp/safe_r)[:, None, None]*(np.eye(3)-nn)))
        inside = (r > self.inner) & (r < self.outer)
        if self.candidate.terms and np.any(inside):
            x, y, z = [Jet2.variable(q[inside, i], i) for i in range(3)]
            u = x/self.radius
            w = (y*y+z*z)/(self.radius**2)
            s = (x*x+y*y+z*z-self.inner**2)/(self.outer**2-self.inner**2)
            window = (4*s*(1-s))**6
            P = Jet2.constant(np.zeros(np.count_nonzero(inside)))
            for i, j, coefficient in self.candidate.terms:
                P = P+float(coefficient)*(u**i)*(w**j)
            perturbation = self.beta*self.radius*window*P
            phi[inside] += perturbation.v
            W[inside] += perturbation.d
            K[inside] += perturbation.h
        return phi.reshape(shape), W.reshape(shape+(3,)), K.reshape(shape+(3, 3))

    def invariant(self, points):
        K = self.fields(points)[2]
        return np.trace(K, axis1=-2, axis2=-1)**2-np.sum(K*K, axis=(-2, -1))

    def density(self, points):
        return self.density_factor*self.invariant(points)

    def metric(self, point):
        W = self.fields(np.asarray(point))[1]
        g = np.eye(4)
        g[0, 0] = -1+W@W
        g[0, 1:] = W
        g[1:, 0] = W
        return g

