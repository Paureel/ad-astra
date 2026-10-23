"""Reproducible report and scientific-viewer data generation."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
from scipy.optimize import brentq

from . import __version__
from .diagnostics import sampled_constraints
from .energy import baseline_energy, evaluate_energy
from .geometry import Geometry, radial_profile
from .model import ROOT, benchmark, baseline_candidate, canonical_hash, exact


def source_hash() -> str:
    """Hash exact evaluator files, independent of installation paths."""
    digest = sha256()
    for path in sorted((ROOT / "src" / "warpproof").glob("*.py")):
        digest.update(path.name.encode()+b"\0"+path.read_bytes()+b"\0")
    return digest.hexdigest()


def provenance(candidate) -> dict:
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": __version__,
        "evaluator_source_sha256": source_hash(),
        "benchmark_sha256": canonical_hash(benchmark()),
        "candidate_canonical_sha256": candidate.candidate_hash,
        "candidate_file_sha256": candidate.raw_input_sha256,
        "parameter_sha256": candidate.parameter_hash,
        "python_version": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
    }


def evaluate_report(candidate, *, crosscheck=True) -> dict:
    spec = benchmark()
    geometry = Geometry(candidate)
    primary = evaluate_energy(geometry, tolerance=1e-8)
    refined = evaluate_energy(geometry, tolerance=1e-10, refinement=True)
    relative_change = abs(primary["value_J"]-refined["value_J"])/refined["value_J"]
    constraints = sampled_constraints(geometry)
    independent = {"passed": None, "message": "Not requested in this invocation."}
    if crosscheck:
        from .independent import crosscheck_geometry
        independent = crosscheck_geometry(geometry)
    good = (relative_change < 1e-6 and constraints["passed_on_samples"]
            and independent["passed"] is True and not refined["warnings"])
    # Numerical uncertainty stays heuristic. No positive formal status is parsed
    # from input or inferred from a score, JSON file, or CI outcome.
    refined["error_estimate_J"] = max(refined["error_estimate_J"],
                                      abs(primary["value_J"]-refined["value_J"]))
    return {
        "schema_version": 1,
        "benchmark": {"id": spec["id"], "version": "1-draft", "metric_name": spec["family"]["name"],
            "speed_c": geometry.beta, "source": spec["source"],
            "units": {"energy": "J", "length": "m", "time": "s", "density": "J/m^3"},
            "coordinate_frame": "comoving q=(x_lab-2ct,y,z); ray times in SI seconds"},
        "candidate": {"id": candidate.id, "parameter_hash": candidate.parameter_hash,
            "parameters": {"R_m": geometry.radius, "sigma_per_m": geometry.sigma,
                "speed_c": geometry.beta, "coefficients": candidate.source["coefficients"]}},
        "status": {"formal": "not_implemented", "formal_certification": False,
            "numerical": "passed" if good else "inconclusive",
            "evidence_level": "numerical_only",
            "message": "Numerical diagnostics only. Global admissibility and a whole-space energy enclosure remain unproved; record promotion is disabled."},
        "energy": refined,
        "diagnostics": {"relative_energy_change": relative_change,
            "quadrature_relative_tolerances": [1e-8, 1e-10],
            "angular_fit_degrees": [10, 12] if candidate.terms else None,
            "sampled_constraints": constraints, "independent_einstein_check": independent},
        "provenance": provenance(candidate),
    }


def reproduce_report() -> dict:
    """Reproduce Rodal Table 6's spherical integration window, L=12R.

    The paper's table is a spherical integration to L=60 m, at R=5 m,
    sigma=4/m, beta=1. Its quoted values are rounded numerical estimates.
    """
    candidate = baseline_candidate()
    geometry = Geometry(candidate, radius=5, sigma=4, beta=1)
    energy = baseline_energy(geometry, tail_start=60, tolerance=1e-11)
    published = {"positive_J": 1.29e44, "negative_J": 1.21e44,
                 "absolute_J": 2.50e44, "signed_J": 8.37e42}
    computed = {"positive_J": energy["body_positive_J"], "negative_J": energy["body_negative_J"],
                "absolute_J": energy["body_absolute_J"], "signed_J": energy["body_signed_J"]}
    differences = {key: abs(computed[key]/value-1) for key, value in published.items()}
    normalized = baseline_energy(Geometry(candidate), tolerance=1e-11)
    return {
        "schema_version": 1, "source": benchmark()["source"],
        "fixture": {"table": 6, "profile_radius_m": 5, "sigma_per_m": 4,
                    "speed_c": 1, "finite_integration_radius_m": 60},
        "published_rounded_values": published, "reproduced_finite_domain_values": computed,
        "relative_differences": differences, "comparison_tolerance": 0.005,
        "comparison_passed": all(d <= 0.005 for d in differences.values()),
        "whole_space_absolute_energy_J": energy["value_J"],
        "whole_space_tail_J": energy["tail"]["absolute_J"],
        "standardized_2c_absolute_energy_J": normalized["value_J"],
        "scale_factor_from_original_whole_space": normalized["value_J"]/energy["value_J"],
        "formal_certification": False,
        "interpretation": "Reproduction of rounded finite-domain figures, with a separately derived exterior-tail correction. The standardized 2c score is this repository's calculation, not a number claimed by the paper.",
        "provenance": provenance(candidate),
    }


def viewer_report(candidate) -> dict:
    from .geodesics import generate_rays
    out = evaluate_report(candidate)
    geometry = Geometry(candidate)
    spec = benchmark()
    size = int(spec["numerics"]["slice_grid_size"])
    extent = float(exact(spec["numerics"]["display_extent_m"]))
    axis = np.linspace(-extent, extent, size)
    u, v = np.meshgrid(axis, axis, indexing="xy")
    slices = []
    for plane in ("xy", "yz"):
        for offset_string in spec["numerics"]["slice_offsets_m"]:
            offset = float(exact(offset_string))
            offset_array = np.full_like(u, offset)
            points = np.stack((u, v, offset_array) if plane == "xy" else (offset_array, u, v), axis=-1)
            slices.append({"id": f"{plane}_{offset:g}", "plane": plane, "offset_m": offset,
                "u_m": axis.tolist(), "v_m": axis.tolist(),
                "rho_J_m3": geometry.density(points).ravel().tolist()})
    # Always derive the color scale from the same reference, not from the import.
    reference = Geometry(baseline_candidate())
    reference_points = np.stack((u, v, np.zeros_like(u)), axis=-1)
    color_scale = float(np.max(np.abs(reference.density(reference_points))))
    radial_axis = np.linspace(0, 2*extent, 321)
    F = 1-radial_profile(radial_axis, geometry.radius, geometry.sigma)[0]
    contours = [{"f": level, "radius_m": brentq(
        lambda r: 1-float(radial_profile(r, geometry.radius, geometry.sigma)[0])-level,
        0, 2*extent)} for level in (0.1, 0.5, 0.9)]
    out["display"] = {"rho_scale_abs_J_m3": color_scale, "reference_candidate": "rodal-reference-2c"}
    out["geometry"] = {"radial_profile": [{"r_m": float(r), "f": float(f)} for r, f in zip(radial_axis, F)],
        "isosurfaces": contours, "cabin_radius_m": 10, "ship_length_m": 8,
        "extent_m": extent, "contour_meaning": "Reference F levels only. A perturbed geometry need not have spherical shift or density contours."}
    out["slices"] = slices
    out["rays"] = generate_rays(geometry)
    residuals = [ray["max_null_residual"] for ray in out["rays"] if ray.get("max_null_residual") is not None]
    out["diagnostics"]["max_null_residual"] = max(residuals, default=0)
    out["diagnostics"]["mesh_sizes"] = [size, size]
    out["diagnostics"]["ray_residual_threshold"] = 1e-6
    if (any(ray["status"] == "failed" for ray in out["rays"])
            or len(residuals) != len(out["rays"])
            or max(residuals, default=0) > 1e-6):
        out["status"]["numerical"] = "inconclusive"
        out["status"]["message"] += " At least one numerical ray integration or null-residual check did not pass."
    return out


def write_report(path, value, *, javascript=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, allow_nan=False)+"\n"
    path.write_text("window.WARP_DEFAULT_RESULT = "+payload+";\n" if javascript else payload)
