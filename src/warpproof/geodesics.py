"""Finite-interval null rays in the prescribed stationary comoving metric.

The metric is ds²=-du²+|dq+W(q)du|², where u=ct is in metres. With constant
covariant momentum p0, H=1/2[-(p0-W.p)²+p.p] and omega=-p0+W.p. Reparameterizing
Hamilton's equations by u gives dq/du=p/omega-W and dp/du=(DW).T p.

This is test-light propagation in a supplied metric, not an Einstein-matter
evolution. An 'escaped' status means only that a ray reached the explicit
numerical stopping sphere. It makes no claim about null infinity or a horizon.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp


FINAL_CT_M = 60.0
SAMPLE_COUNT = 121
STOP_RADIUS_M = 80.0
RTOL = 1e-10
ATOL = 1e-12
MAX_STEP_CT_M = 0.25


def integrate_null_ray(
    geometry,
    direction,
    *,
    ray_id: str = "ray",
    label: str = "Null ray",
    final_ct_m: float = FINAL_CT_M,
    sample_count: int = SAMPLE_COUNT,
    stop_radius_m: float = STOP_RADIUS_M,
    rtol: float = RTOL,
    atol: float = ATOL,
    max_step_ct_m: float = MAX_STEP_CT_M,
) -> dict:
    """Launch one future null ray at q=0 in an Eulerian unit direction.

    Output positions are comoving metres, and t_s=u/c is physical time in
    seconds. The supplied direction is normalized. Its initial Eulerian
    frequency fixes an arbitrary affine-momentum scale to omega(0)=1.
    Samples follow a common uniform u-grid; an early stop retains the exact
    event point as an additional final sample. Failed runs are retained.
    """
    vector = np.asarray(direction, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError("Direction must be three finite Cartesian components.")
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError("Direction must have finite nonzero length.")
    if not (math.isfinite(final_ct_m) and final_ct_m > 0
            and type(sample_count) is int and sample_count >= 2
            and math.isfinite(stop_radius_m) and stop_radius_m > 0
            and 0 < rtol < 1 and 0 < atol < 1
            and math.isfinite(max_step_ct_m) and max_step_ct_m > 0):
        raise ValueError("Invalid finite integration interval or tolerances.")
    initial_q = np.zeros(3)
    initial_p = vector / norm
    _, initial_W, _ = geometry.fields(initial_q)
    initial_W = np.asarray(initial_W, dtype=float)
    if initial_W.shape != (3,) or not np.all(np.isfinite(initial_W)):
        raise ValueError("Geometry returned an invalid initial shift.")
    p0 = float(initial_W @ initial_p - 1.0)
    initial_state = np.concatenate((initial_q, initial_p))
    counters = {"rhs_evaluations": 0}

    def rhs(_u, state):
        counters["rhs_evaluations"] += 1
        q, p = state[:3], state[3:]
        _, W, K = geometry.fields(q)
        W, K = np.asarray(W, dtype=float), np.asarray(K, dtype=float)
        omega = float(-p0 + W @ p)
        if not (math.isfinite(omega) and omega > 0
                and np.all(np.isfinite(W)) and np.all(np.isfinite(K))):
            raise FloatingPointError("Ray left the numerically resolved future-directed branch.")
        result = np.concatenate((p / omega - W, K.T @ p))
        if not np.all(np.isfinite(result)):
            raise FloatingPointError("Non-finite geodesic derivative.")
        return result

    def stop_event(_u, state):
        return float(np.linalg.norm(state[:3]) - stop_radius_m)

    stop_event.terminal = True
    stop_event.direction = 1
    sample_u = np.linspace(0.0, final_ct_m, sample_count)
    message = ""
    integration_success = False
    try:
        solution = solve_ivp(
            rhs, (0.0, final_ct_m), initial_state, method="DOP853",
            t_eval=sample_u, rtol=rtol, atol=atol, max_step=max_step_ct_m,
            events=stop_event,
        )
        times = np.asarray(solution.t, dtype=float)
        states = np.asarray(solution.y, dtype=float).T
        integration_success = bool(solution.success)
        event_hit = bool(len(solution.t_events[0]))
        if event_hit:
            event_u = float(solution.t_events[0][0])
            event_state = np.asarray(solution.y_events[0][0], dtype=float)
            if not len(times) or event_u > times[-1] + 1e-12:
                times = np.append(times, event_u)
                states = np.vstack((states, event_state))
        status = "escaped" if integration_success and event_hit else (
            "finite_interval_complete" if integration_success else "failed")
        message = str(solution.message)
    except (FloatingPointError, ValueError, OverflowError) as error:
        # No rejected/internal solver stages are presented as accepted samples.
        times = np.array([0.0])
        states = initial_state[None, :]
        status = "failed"
        message = str(error)

    points = []
    residuals = []
    frequencies = []
    for u, state in zip(times, states):
        q, p = state[:3], state[3:]
        _, W, _ = geometry.fields(q)
        omega = float(-p0 + np.asarray(W) @ p)
        # Scale first, to avoid overflow when a large blueshift develops.
        scale = max(float(np.max(np.abs(p))), abs(omega), np.finfo(float).tiny)
        pp = float((p / scale) @ (p / scale))
        oo = (omega / scale) ** 2
        residual = abs(pp - oo) / (pp + oo) if pp + oo > 0 else math.inf
        if not (np.all(np.isfinite(state)) and math.isfinite(omega)
                and math.isfinite(residual) and omega > 0):
            status = "failed"
            message = "A returned ray sample is non-finite or not future-directed."
            break
        residuals.append(residual)
        frequencies.append(omega)
        points.append({
            "t_s": float(u / geometry.c),
            "x_m": float(q[0]), "y_m": float(q[1]), "z_m": float(q[2]),
            "p_x": float(p[0]), "p_y": float(p[1]), "p_z": float(p[2]),
            "eulerian_frequency_ratio": omega,
        })
    if not points:
        # The valid initial condition is retained explicitly when no later
        # numerical sample can be trusted. No trajectory segment is invented.
        points = [{"t_s": 0.0, "x_m": 0.0, "y_m": 0.0, "z_m": 0.0,
                   "p_x": float(initial_p[0]), "p_y": float(initial_p[1]),
                   "p_z": float(initial_p[2]), "eulerian_frequency_ratio": 1.0}]
        residuals = [0.0]
        frequencies = [1.0]
        status = "failed"

    description = {
        "escaped": f"Reached the r={stop_radius_m:g} m numerical stopping sphere; no claim about escape to infinity.",
        "finite_interval_complete": f"Integrated through u=ct={final_ct_m:g} m; no horizon diagnosis.",
        "failed": "Integration failed or became numerically unresolved; retained samples are not a successful full trajectory.",
    }[status]
    return {
        "id": ray_id, "label": label, "kind": "null", "status": status,
        "status_description": description, "solver_message": message,
        "coordinate_frame": "comoving", "time_unit": "s",
        "launch_direction_eulerian": initial_p.tolist(),
        "initial_covariant_p0": p0,
        "event_radius_m": float(stop_radius_m),
        "event_scope": "finite numerical stopping sphere, not null infinity",
        "max_null_residual": float(max(residuals)),
        "null_residual_definition": "abs(p.p-omega^2)/(p.p+omega^2), sampled at stored points",
        "max_eulerian_frequency_ratio": float(max(frequencies)),
        "points": points,
        "integrator": {"method": "DOP853", "rtol": rtol, "atol": atol,
                       "max_step_ct_m": max_step_ct_m,
                       "requested_final_ct_m": float(final_ct_m),
                       "requested_samples": sample_count,
                       "rhs_evaluations": counters["rhs_evaluations"],
                       "success": integration_success and status != "failed"},
    }


def generate_rays(geometry) -> list[dict]:
    """Nine test rays for the fixed benchmark in the xy half-plane.

    Angles 0..180 degrees include forward, transverse, and backward launch.
    The axisymmetric candidate family has reflection symmetry; the reflected
    half-plane need not be duplicated in this standardized display dataset.
    """
    rays = []
    for index, angle_deg in enumerate(np.linspace(0.0, 180.0, 9)):
        angle = math.radians(float(angle_deg))
        suffix = " · forward" if index == 0 else " · transverse" if index == 4 else " · backward" if index == 8 else ""
        rays.append(integrate_null_ray(
            geometry, [math.cos(angle), math.sin(angle), 0.0],
            ray_id=f"null-{index:02d}", label=f"{angle_deg:g}°{suffix}",
        ))
    return rays
