# SPDX-License-Identifier: Apache-2.0
"""The submitted compact potential, implemented as a separate research model.

Data never replace the frozen v1 decoder. The exact input boundary controls are
checked before SciPy evaluates the degree-six tensor spline numerically.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
import re

import numpy as np
from scipy.interpolate import BSpline
from scipy.special import betainc

from warpproof.geometry import Geometry
from warpproof.model import baseline_candidate

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE/"upstream"
CANDIDATE = UPSTREAM/"research/radical_compact/global_search/tensor-polished-candidate.json"
CONTRACT = UPSTREAM/"research/expanded_family/localized-exterior-contract.json"
EXPECTED_HASH = "6c0cdb24b7e376f3670c294647f49c57420ded22f57b5083f00900c6da0eb041"


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate candidate key: "+key)
        result[key] = value
    return result


def _rational(value):
    if not isinstance(value, str) or len(value) > 128 or not re.fullmatch(r"-?\d+(?:/[1-9]\d*)?", value):
        raise ValueError("Expected a short exact rational string.")
    return F(value)


def decode(path=CANDIDATE):
    path = Path(path)
    if path.stat().st_size > 2**20:
        raise ValueError("Candidate exceeds the 1 MiB research input limit.")
    raw = path.read_bytes()
    d = json.loads(raw, object_pairs_hook=_unique)
    expected = {"schema_version", "id", "status", "formal_certification", "contract_id", "contract_sha256",
        "scenario", "outer_radius_m", "representation", "radial_degree", "angular_degree", "radial_knots_m",
        "angular_knots", "coefficients", "coefficient_order", "main_definition", "core_correction", "symmetry",
        "regularity", "admission_status"}
    if set(d) != expected or type(d["schema_version"]) is not int or d["schema_version"] != 1:
        raise ValueError("Unexpected compact research schema.")
    if d["contract_id"] != "rodal-2c-localized-exterior-research" or d["contract_sha256"] != sha256(CONTRACT.read_bytes()).hexdigest():
        raise ValueError("Candidate and research contract differ.")
    if d["status"] != "numerical_only" or d["formal_certification"] is not False:
        raise ValueError("Candidate data cannot assert certification.")
    if d["scenario"] != "compact_spherical_exterior" or _rational(d["outer_radius_m"]) != 100:
        raise ValueError("This implementation is the declared compact-100 scenario.")
    if d["representation"] != "tensor_product_radial_angular_bspline":
        raise ValueError("Unsupported representation.")
    if d["coefficient_order"] != "Rows angular basis index, columns radial basis index":
        raise ValueError("Unexpected coefficient ordering.")
    if d["core_correction"] != "eta(r)*Phi0, eta=1 onr<=10, eta=1-S(r-10) on10<r<11, eta0beyond11; degree11 smootherstepS":
        raise ValueError("The core definition is fixed.")
    knots = []
    for field, degree, low, high in [("radial_knots_m", "radial_degree", F(11), F(100)),
                                    ("angular_knots", "angular_degree", F(-1), F(1))]:
        values = d[field]
        if type(d[degree]) is not int or d[degree] != 6 or not isinstance(values, list) or not 14 <= len(values) <= 135:
            raise ValueError("Expected bounded degree-six knot data.")
        k = list(map(_rational, values))
        if k[:7] != [low]*7 or k[-7:] != [high]*7 or any(not low < v < high for v in k[7:-7]):
            raise ValueError("Incorrect knot endpoints.")
        if any(a >= b for a, b in zip(k[7:-7], k[8:-7])):
            raise ValueError("Interior knots must be simple and ordered.")
        knots.append(k)
    rk, mk = knots
    nr, nm = len(rk)-7, len(mk)-7
    if not isinstance(d["coefficients"], list) or len(d["coefficients"]) != nm:
        raise ValueError("Incorrect angular coefficient count.")
    coefficients = []
    for j, row in enumerate(d["coefficients"]):
        if not isinstance(row, list) or len(row) != nr:
            raise ValueError("Incorrect radial coefficient count.")
        row = list(map(_rational, row))
        greville = sum(mk[j+1:j+7], F(0))/6
        if row[:6] != [F(0)]*6 or row[-6:] != [greville]*6:
            raise ValueError("The controls do not preserve C5 core/exterior matching.")
        coefficients.append(row)
    return d, rk, mk, coefficients, sha256(raw).hexdigest()


class CompactGeometry:
    def __init__(self, path=CANDIDATE):
        self.data, rk, mk, c, self.input_sha256 = decode(path)
        self.radial_edges = np.array(sorted(set(rk)), dtype=float)
        self.angular_edges = np.array(sorted(set(mk)), dtype=float)
        self.coefficients = np.array(c, dtype=float)
        self.radial = BSpline(np.array(rk, dtype=float), np.eye(len(rk)-7), 6, extrapolate=False)
        self.angular = BSpline(np.array(mk, dtype=float), np.eye(len(mk)-7), 6, extrapolate=False)
        self.reference = Geometry(baseline_candidate())
        self.beta, self.c, self.G = 2., self.reference.c, self.reference.G
        self.density_factor = self.c**4/(16*np.pi*self.G)

    def _jets(self, r, mu, order=2):
        radial = [self.radial(r, k)@self.coefficients.T for k in range(order+1)]
        angular = [self.angular(mu, k) for k in range(order+1)]
        return {(i, j): np.sum(radial[i]*angular[j], axis=-1)
                for i in range(order+1) for j in range(order+1-i)}

    def fields(self, points):
        original = np.asarray(points, dtype=float)
        if original.shape[-1:] != (3,) or not np.all(np.isfinite(original)):
            raise ValueError("Use finite Cartesian points with trailing dimension three.")
        shape = original.shape[:-1]
        q = original.reshape(-1, 3)
        r = np.linalg.norm(q, axis=1)
        phi = np.zeros(len(q)); w = np.zeros_like(q); h = np.zeros((len(q), 3, 3))
        core = r < 11
        if np.any(core):
            qc, rc = q[core], r[core]
            p0, w0, h0 = self.reference.fields(qc)
            n = qc/np.where(rc == 0, 1., rc)[:, None]
            nn = n[:, :, None]*n[:, None, :]
            t = np.clip(rc-10, 0, 1)
            eta = betainc(6, 6, 1-t)
            ep = -2772*t**5*(1-t)**5
            epp = -13860*t**4*(1-t)**4*(1-2*t)
            ep_over_r = ep/np.where(rc == 0, 1., rc)
            phi[core] = eta*p0
            w[core] = eta[:, None]*w0+(ep*p0)[:, None]*n
            h[core] = (eta[:, None, None]*h0
                + ep[:, None, None]*(n[:, :, None]*w0[:, None, :]+w0[:, :, None]*n[:, None, :])
                + p0[:, None, None]*(epp[:, None, None]*nn+ep_over_r[:, None, None]*(np.eye(3)-nn)))
        shell = (r > 11) & (r < 100)
        if np.any(shell):
            rs = r[shell]; n = q[shell]/rs[:, None]
            mu = np.clip(n[:, 0], -1, 1); m = np.array([1., 0., 0.])-mu[:, None]*n
            jets = self._jets(rs, mu)
            fr = 2*(jets[0, 0]+rs*jets[1, 0]); fu = 2*rs*jets[0, 1]
            frr = 2*(2*jets[1, 0]+rs*jets[2, 0])
            fru = 2*(jets[0, 1]+rs*jets[1, 1]); fuu = 2*rs*jets[0, 2]
            nn = n[:, :, None]*n[:, None, :]
            nm = n[:, :, None]*m[:, None, :]+m[:, :, None]*n[:, None, :]
            mm = m[:, :, None]*m[:, None, :]
            transverse = np.eye(3)-nn
            phi[shell] = 2*rs*jets[0, 0]
            w[shell] = fr[:, None]*n+(fu/rs)[:, None]*m
            h[shell] = (frr[:, None, None]*nn+(fru/rs-fu/rs**2)[:, None, None]*nm
                +(fuu/rs**2)[:, None, None]*mm+(fr/rs-mu*fu/rs**2)[:, None, None]*transverse)
        outside = r >= 100
        phi[outside] = 2*q[outside, 0]; w[outside, 0] = 2
        return phi.reshape(shape), w.reshape(shape+(3,)), h.reshape(shape+(3, 3))

    def invariant(self, points):
        h = self.fields(points)[2]
        return np.trace(h, axis1=-2, axis2=-1)**2-np.sum(h*h, axis=(-2, -1))

    def density(self, points):
        return self.density_factor*self.invariant(points)

    def metric(self, point):
        w = self.fields(point)[1]
        g = np.eye(4); g[0, 0] = -1+w@w
        g[0, 1:] = w; g[1:, 0] = w
        return g
