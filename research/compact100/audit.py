# SPDX-License-Identifier: Apache-2.0
"""Independent formula/core audit; full source replays are in validate.py."""
from __future__ import annotations

import argparse
from fractions import Fraction as F
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import quad
from scipy.special import betainc

ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from research.compact100.bounds import (
    A, BETA, C, G, EPSILON, REFERENCE_REPORTED, CANDIDATE_REPORTED_UPPER,
    compact_floor, tail_floor, necessary_radius, radius_lhs, outward,
)
from warpproof.geometry import radial_profile
from research.compact100.geometry import CANDIDATE

PDF_HASH = "3d2380fd34fd99edcc41cf6b98e439066afebc6fc4ac0ca03771f68bf00b85f2"
CANDIDATE_HASH = "6c0cdb24b7e376f3670c294647f49c57420ded22f57b5083f00900c6da0eb041"


def core_profile(r):
    """g_core, g_core', g_core'' for Phi_core = beta*x*g_core(r).

    This shares the existing reference profile, but independently implements
    the PDF's cutoff and its analytic derivatives. It is floating-point code.
    """
    r = np.asarray(r, dtype=float)
    if np.any(~np.isfinite(r)) or np.any(r < 0):
        raise ValueError("Use finite nonnegative radii.")
    _, g, _, gp, gpp = radial_profile(r)
    t = np.clip(r-10, 0, 1)
    eta = betainc(6, 6, 1-t)
    ep = -2772*t**5*(1-t)**5
    epp = -13860*t**4*(1-t)**4*(1-2*t)
    return eta*g, eta*gp+ep*g, eta*gpp+2*ep*gp+epp*g


def core_energy():
    """Whole isolated core correction, using analytic angular integration.

    Only the adaptive quadrature error estimate is returned, not a rigorous
    enclosure of the transcendental core or its rounding errors.
    """
    def radial(r, signed=False):
        _, gp, gpp = core_profile(r)
        p, q = float(4*gp*(3*gp+r*gpp)), float(2*gp*gp)
        if signed:
            h = p/3-q
        else:
            h = q-p/3 if p <= q else p/3-q+4*q/3*math.sqrt(q/p)
        return r*r*h
    absolute, signed, error = 0., 0., 0.
    for a, b in [(0, 10), (10, 11)]:
        value, estimate = quad(radial, a, b, epsabs=1e-30, epsrel=1e-10, limit=300)
        absolute += value
        error += estimate
        value, _ = quad(lambda r: radial(r, True), a, b, epsabs=1e-30, epsrel=1e-10, limit=300)
        signed += value
    scale = float(C**4*BETA**2/(4*G))
    return {"status": "numerical_only", "absolute_energy_J": scale*absolute,
            "signed_energy_J": scale*signed, "quadrature_error_estimate_J": scale*error,
            "certified_bounds_J": None, "rounding_certified": False}


def report(source_pdf=None):
    if source_pdf is not None and sha256(Path(source_pdf).read_bytes()).hexdigest() != PDF_HASH:
        raise ValueError("PDF differs from the audited source. Review it before replay.")
    radii = [100, 300, 500, 1000, 1000000]
    floors = [{"radius_m": r, "conditional_formula_J": outward(compact_floor(F(r))),
               "conditional_reference_factor_ceiling": outward(tuple(
                   REFERENCE_REPORTED[1]/v for v in reversed(compact_floor(F(r)))))}
              for r in radii]
    saving = 100*(1-CANDIDATE_REPORTED_UPPER/REFERENCE_REPORTED[0])
    target1000 = C**4*(BETA-EPSILON)**2*A*1000/(3*G*REFERENCE_REPORTED[1])
    threshold1000 = F("7.1214e165")
    return {
        "schema_version": 1,
        "status": "independent_formula_and_core_audit_only",
        "source_pdf_sha256": PDF_HASH, "source_pdf_identity_checked": source_pdf is not None,
        "expected_candidate_sha256": CANDIDATE_HASH,
        "candidate_source_available": CANDIDATE.exists() and sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH,
        "candidate_reproduced": False, "candidate_admitted": False,
        "formal_certification": False, "existing_benchmark_eligible": False,
        "scenario": "proposed compact-100 class; not rodal-2c-v1-draft",
        "reason_not_original_benchmark": "Changes the allowed representation and the geometry outside 40 m, replacing the required reference tail.",
        "reported_candidate_upper_J_unverified": str(CANDIDATE_REPORTED_UPPER),
        "reported_reference_interval_J_unverified": [str(v) for v in REFERENCE_REPORTED],
        "conditional_saving_percent_arithmetic": outward((saving, saving)),
        "compact_formula_evaluations": floors,
        "conditional_noncompact_formula_at_150m_with_surface_upper_1067_J": outward(tail_floor(F(150), F(1067))),
        "conditional_necessary_radius_m": {
            str(f): outward(necessary_radius(F(f))) for f in (10, 100)},
        "conditional_1000fold_reported_radius_obstruction_confirmed": radius_lhs(threshold1000)[1] < target1000,
        "core_correction": core_energy(),
        "limitations": [
            "Exact rational arithmetic encloses the displayed bound formulas; their continuum hypotheses and GR bridge are not machine-certified here.",
            "This command audits the printed formulas/core only; use research/compact100/validate.py --full to replay the supplied candidate and verification sources.",
            "No new candidate or score is added to the existing app or README history.",
            "An engineered source, stability, formation, and causal control are not established.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report(args.source_pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(f"Wrote formula/core audit: {args.output}; full candidate validation is a separate command.")
