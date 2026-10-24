"""Independent numerical 4D curvature checks for the stationary benchmark.

The tensor calculation samples only ``geometry.metric(point)``. It does not use
the reduced Hessian invariant, its derivatives, or the energy integration code.
Spatial metric derivatives use second-order central differences; time
derivatives are zero because this benchmark is stationary in comoving
coordinates (u=ct, x, y, z), all measured in metres.

The index convention follows the independent exact-rational polynomial checks
in ``formal/diagnostics/direct_ricci_check.py``. This module extends that route
to the actual smooth numerical geometry. Finite-difference agreement is a
diagnostic, not a GR proof, a global admissibility check, or an error enclosure.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

import numpy as np


class StationaryMetric(Protocol):
    def metric(self, point): ...


@dataclass(frozen=True)
class EinsteinDiagnostic:
    point_m: np.ndarray
    step_m: float
    metric: np.ndarray
    inverse_metric: np.ndarray
    ricci: np.ndarray
    scalar_curvature_per_m2: float
    einstein: np.ndarray
    normal: np.ndarray
    twice_Gnn_per_m2: float
    inverse_residual: float
    normal_norm_residual: float
    ricci_symmetry_residual_per_m2: float
    metric_condition_number: float


def _metric_sample(geometry: StationaryMetric, point: np.ndarray) -> np.ndarray:
    value = np.asarray(geometry.metric(point), dtype=float)
    if value.shape != (4, 4) or not np.all(np.isfinite(value)):
        raise ValueError("The metric must be a finite 4 by 4 matrix.")
    if not np.allclose(value, value.T, rtol=0.0, atol=1e-12):
        raise ValueError("The metric must be symmetric.")
    return value


def direct_einstein_tensor(
    geometry: StationaryMetric,
    point_m,
    step_m: float = 0.01,
) -> EinsteinDiagnostic:
    """Calculate Ricci and Einstein tensors from 19 stationary metric samples.

    Array indices in ``dg[e,a,b]`` and ``ddg[e,f,a,b]`` place derivative
    coordinates first. The curvature convention is
    R_ab = d_c Gamma^c_ab - d_b Gamma^c_ac
           + Gamma^c_cd Gamma^d_ab - Gamma^c_bd Gamma^d_ac.

    The future-directed normal is reconstructed from the inverse metric. For
    the benchmark it is n=(1,-W); its norm is checked numerically. Tensor entries
    and 2 G(n,n) have units m^-2, with no c^4/(16*pi*G) energy prefactor.
    """
    point = np.asarray(point_m, dtype=float)
    if point.shape != (3,) or not np.all(np.isfinite(point)):
        raise ValueError("The point must contain three finite spatial coordinates.")
    if isinstance(step_m, bool) or not math.isfinite(step_m) or step_m <= 0:
        raise ValueError("The finite-difference step must be finite and positive.")
    h = float(step_m)
    metric = _metric_sample(geometry, point)
    inverse = np.linalg.inv(metric)
    if inverse[0, 0] >= 0:
        raise ValueError("The constant-time slice does not have a timelike normal.")

    dg = np.zeros((4, 4, 4), dtype=float)
    ddg = np.zeros((4, 4, 4, 4), dtype=float)
    offsets = np.eye(3) * h
    for i in range(3):
        plus = _metric_sample(geometry, point + offsets[i])
        minus = _metric_sample(geometry, point - offsets[i])
        dg[i + 1] = (plus - minus) / (2 * h)
        ddg[i + 1, i + 1] = (plus - 2 * metric + minus) / h**2
        for j in range(i):
            pp = _metric_sample(geometry, point + offsets[i] + offsets[j])
            pm = _metric_sample(geometry, point + offsets[i] - offsets[j])
            mp = _metric_sample(geometry, point - offsets[i] + offsets[j])
            mm = _metric_sample(geometry, point - offsets[i] - offsets[j])
            mixed = (pp - pm - mp + mm) / (4 * h**2)
            ddg[i + 1, j + 1] = mixed
            ddg[j + 1, i + 1] = mixed

    # Differentiate the matrix inverse algebraically; no differencing of an
    # independently inverted neighbouring matrix is needed.
    dinverse = -np.einsum("ai,eij,jb->eab", inverse, dg, inverse)
    christoffel = np.zeros((4, 4, 4), dtype=float)
    dchristoffel = np.zeros((4, 4, 4, 4), dtype=float)
    for a in range(4):
        for b in range(4):
            for c in range(4):
                combination = dg[b, :, c] + dg[c, :, b] - dg[:, b, c]
                christoffel[a, b, c] = 0.5 * inverse[a] @ combination
                for e in range(4):
                    differentiated = (
                        ddg[e, b, :, c] + ddg[e, c, :, b] - ddg[e, :, b, c]
                    )
                    dchristoffel[e, a, b, c] = 0.5 * (
                        dinverse[e, a] @ combination + inverse[a] @ differentiated
                    )

    ricci = np.zeros((4, 4), dtype=float)
    for a in range(4):
        for b in range(4):
            derivative = sum(
                dchristoffel[c, c, a, b] - dchristoffel[b, c, a, c]
                for c in range(4)
            )
            product = sum(
                christoffel[c, c, d] * christoffel[d, a, b]
                - christoffel[c, b, d] * christoffel[d, a, c]
                for c in range(4) for d in range(4)
            )
            ricci[a, b] = derivative + product
    scalar = float(np.einsum("ab,ab", inverse, ricci))
    einstein = ricci - 0.5 * scalar * metric
    normal = -inverse[:, 0] / math.sqrt(-inverse[0, 0])
    twice_Gnn = float(2 * normal @ einstein @ normal)
    if not np.all(np.isfinite(einstein)) or not math.isfinite(twice_Gnn):
        raise ValueError("The finite-difference curvature calculation is non-finite.")
    return EinsteinDiagnostic(
        point_m=point.copy(),
        step_m=h,
        metric=metric,
        inverse_metric=inverse,
        ricci=ricci,
        scalar_curvature_per_m2=scalar,
        einstein=einstein,
        normal=normal,
        twice_Gnn_per_m2=twice_Gnn,
        inverse_residual=float(np.max(np.abs(metric @ inverse - np.eye(4)))),
        normal_norm_residual=abs(float(normal @ metric @ normal) + 1.0),
        ricci_symmetry_residual_per_m2=float(np.max(np.abs(ricci - ricci.T))),
        metric_condition_number=float(np.linalg.cond(metric)),
    )


def compare_invariant(
    geometry,
    point_m,
    steps_m=(0.02, 0.01, 0.005),
    *,
    relative_tolerance: float = 1e-4,
    absolute_tolerance_per_m2: float = 1e-8,
) -> dict:
    """Compare the independent tensor route with the reduced invariant.

    Tolerances are diagnostic acceptance thresholds, not rigorous error bounds.
    The report exposes every resolution and the observed refinement behavior.
    """
    steps = tuple(float(step) for step in steps_m)
    if len(steps) < 2 or any(not math.isfinite(h) or h <= 0 for h in steps):
        raise ValueError("At least two finite positive refinement steps are required.")
    if any(a <= b for a, b in zip(steps, steps[1:])):
        raise ValueError("Refinement steps must be strictly decreasing.")
    if (not math.isfinite(relative_tolerance) or relative_tolerance < 0
            or not math.isfinite(absolute_tolerance_per_m2)
            or absolute_tolerance_per_m2 <= 0):
        raise ValueError("Use finite nonnegative relative and positive absolute tolerances.")
    point = np.asarray(point_m, dtype=float)
    direct = [direct_einstein_tensor(geometry, point, step) for step in steps]
    # The reference is intentionally read only after the direct tensor route.
    reduced = float(geometry.invariant(point))
    if not math.isfinite(reduced):
        raise ValueError("The reduced invariant is non-finite.")
    tolerance = absolute_tolerance_per_m2 + relative_tolerance * abs(reduced)
    samples = []
    errors = []
    for result in direct:
        error = abs(result.twice_Gnn_per_m2 - reduced)
        errors.append(error)
        samples.append({
            "step_m": result.step_m,
            "direct_2Gnn_per_m2": result.twice_Gnn_per_m2,
            "absolute_residual_per_m2": error,
            "relative_residual": error / abs(reduced) if reduced else None,
            "metric_inverse_residual": result.inverse_residual,
            "normal_norm_residual": result.normal_norm_residual,
            "ricci_symmetry_residual_per_m2": result.ricci_symmetry_residual_per_m2,
            "metric_condition_number": result.metric_condition_number,
        })
    orders = [
        math.log(a / b) / math.log(ha / hb) if a > 0 and b > 0 else None
        for a, b, ha, hb in zip(errors, errors[1:], steps, steps[1:])
    ]
    # Below the absolute threshold, rounding may obscure the refinement order.
    refinement_consistent = (
        max(errors) <= absolute_tolerance_per_m2
        or errors[-1] <= 0.6 * errors[0]
    )
    structural = all(
        row["metric_inverse_residual"] <= 1e-10
        and row["normal_norm_residual"] <= 1e-10
        and row["ricci_symmetry_residual_per_m2"] <= 1e-8
        for row in samples
    )
    return {
        "point_m": point.tolist(),
        "reduced_invariant_per_m2": reduced,
        "samples": samples,
        "observed_error_orders": orders,
        "final_absolute_tolerance_per_m2": tolerance,
        "relative_tolerance": relative_tolerance,
        "absolute_tolerance_floor_per_m2": absolute_tolerance_per_m2,
        "refinement_consistent": bool(refinement_consistent),
        "passed": bool(errors[-1] <= tolerance and structural and refinement_consistent),
    }


def crosscheck_geometry(geometry, points_m=None) -> dict:
    """Return a JSON-ready, sampled numerical check of the metric/energy bridge.

    Default points deliberately avoid the axes and density-zero surfaces. Both
    positive and negative density regions and the perturbation shell are
    sampled. No finite collection of points establishes a global property.
    """
    if points_m is None:
        points = float(geometry.radius) * np.array([
            [0.85, 0.30, 0.40],
            [1.00, 0.25, 0.15],
            [-0.90, 0.35, 0.10],
            [0.20, 0.95, 0.25],
            [1.40, 0.55, 0.15],
        ])
    else:
        points = np.asarray(points_m, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) == 0:
        raise ValueError("Provide a nonempty array of three-dimensional points.")
    sigma = float(geometry.sigma)
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("A positive finite profile steepness is required.")
    checks = [
        compare_invariant(geometry, point, steps_m=(0.02 / sigma, 0.01 / sigma, 0.005 / sigma))
        for point in points
    ]
    return {
        "method": "stationary_4d_metric_central_differences_christoffel_ricci_einstein",
        "status": "numerical_only",
        "formal_certification": False,
        "units": "m^-2 before multiplying by c^4/(16*pi*G)",
        "coordinate_order": ["u=ct", "x", "y", "z"],
        "comparison": "2*G(n,n) versus the reduced Hessian invariant",
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
        "limitations": [
            "Finite metric samples and second-order finite differences are not a formal GR proof.",
            "The reference and tensor route share the metric's profile and shift implementation.",
            "The numerical thresholds are not certified error bounds or global admissibility tests.",
        ],
    }
