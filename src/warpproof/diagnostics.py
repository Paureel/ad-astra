"""Fixed numerical diagnostics, explicitly not continuum admission proofs."""
from __future__ import annotations

import numpy as np

from .geometry import Geometry
from .model import benchmark, exact


def sampled_constraints(geometry: Geometry) -> dict:
    spec = benchmark()
    caps = spec["draft_admissibility_caps"]
    radii = np.unique(np.concatenate((np.linspace(0, 80, 161),
        np.linspace(17, 23, 61), [geometry.inner, geometry.outer])))
    mu = np.linspace(-1, 1, 49)
    rr, mm = np.meshgrid(radii, mu, indexing="ij")
    points = np.stack((rr*mm, rr*np.sqrt(1-mm*mm), np.zeros_like(rr)), axis=-1).reshape(-1, 3)
    _, W, K = geometry.fields(points)
    step = 0.002
    third = np.empty((len(points), 3, 3, 3))
    for j in range(3):
        dq = np.eye(3)[j]*step
        third[..., j] = (geometry.fields(points+dq)[2]-geometry.fields(points-dq)[2])/(2*step)
    values = {
        "maximum_shift_norm": float(np.max(np.linalg.norm(W, axis=-1))),
        "maximum_shift_jacobian_frobenius_per_m": float(np.max(np.linalg.norm(K, axis=(-2, -1)))),
        "maximum_shift_hessian_frobenius_per_m2": float(np.max(np.sqrt(np.sum(third*third, axis=(1, 2, 3))))),
    }
    limits = {key: float(exact(caps[key])) for key in values}
    cabin_mu = np.linspace(-1, 1, 101)
    radius = float(exact(spec["cabin"]["proper_radius_m"]))
    cr, cm = np.meshgrid(np.linspace(0, radius, 41), cabin_mu, indexing="ij")
    cabin = np.stack((cr*cm, cr*np.sqrt(1-cm*cm), np.zeros_like(cr)), axis=-1)
    cabin_max = float(np.max(np.linalg.norm(geometry.fields(cabin)[1], axis=-1)))
    cabin_limit = float(exact(spec["cabin"]["maximum_shift_norm"]))
    checks = [{"quantity": key, "sampled_maximum": value, "draft_limit": limits[key],
               "sampled_pass": value <= limits[key]} for key, value in values.items()]
    checks.append({"quantity": "cabin_shift_norm", "sampled_maximum": cabin_max,
                   "draft_limit": cabin_limit, "sampled_pass": cabin_max <= cabin_limit})
    return {
        "passed_on_samples": all(c["sampled_pass"] for c in checks),
        "continuum_admissibility_proved": False,
        "checks": checks,
        "samples": {"radial_count": len(radii), "angular_count": len(mu),
                    "maximum_radius_m": 80, "third_derivative_step_m": step,
                    "cabin_radial_count": 41, "cabin_angular_count": len(cabin_mu)},
        "limitations": "Finite samples and a finite-difference third derivative. Unsampled points, the infinite exterior, and rounding errors are not certified.",
    }
