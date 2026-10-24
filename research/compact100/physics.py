# SPDX-License-Identifier: Apache-2.0
"""Sample stationary-gradient Einstein stress and tidal fields, in SI metres.

The candidate's frozen analytic 3-jet has a separate exact monomial audit.
The reference 3-jet is independently built from the smooth radial profile.
Peaks are mesh diagnostics, not certified extrema or engineering limits.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from research.compact100.geometry import UPSTREAM, CANDIDATE
from warpproof.geometry import radial_profile


def reference_jet(r, mu):
    r = np.asarray(r)[:, None]; mu = np.asarray(mu)[None, :]
    _, g, _, gp, gpp = radial_profile(r)
    sech2 = lambda x: 4*np.exp(-2*np.abs(x))/(1+np.exp(-2*np.abs(x)))**2
    fpp = (sech2(r+20)*np.tanh(r+20)-sech2(r-20)*np.tanh(r-20))/np.tanh(20)
    gppp = fpp/r-3*gpp/r
    s = np.sqrt(np.maximum(0, 1-mu*mu))
    shape = np.broadcast_shapes(r.shape, mu.shape)
    w = np.zeros(shape+(3,)); h = np.zeros(shape+(3, 3)); t = np.zeros(shape+(3, 3, 3))
    w[..., 0] = 2*mu*(g+r*gp); w[..., 1] = -2*s*g
    h[..., 0, 0] = 2*mu*(2*gp+r*gpp)
    h[..., 0, 1] = h[..., 1, 0] = -2*s*gp
    h[..., 1, 1] = h[..., 2, 2] = 2*mu*gp
    for indices, values in [((0, 0, 0), 2*mu*(3*gpp+r*gppp)), ((0, 0, 1), -2*s*gpp),
        ((0, 1, 1), 2*mu*gpp), ((0, 2, 2), 2*mu*gpp),
        ((1, 1, 1), -6*s*gp/r), ((1, 2, 2), -2*s*gp/r)]:
        for p in set(permutations(indices)): t[(...,)+p] = values
    return {"W": w, "H": h, "T": t}


def curvature_fields(jet):
    w, h, t = (jet[k] for k in ("W", "H", "T"))
    flow = np.einsum("...k,...ijk->...ij", w, t)
    theta = np.trace(h, axis1=-2, axis2=-1)
    h2 = np.sum(h*h, axis=(-2, -1)); tr_flow = np.trace(flow, axis1=-2, axis2=-1)
    density = (theta*theta-h2)/2
    stress = flow+theta[..., None, None]*h-(tr_flow+(h2+theta*theta)/2)[..., None, None]*np.eye(3)
    return density, stress, flow+h@h, 2*tr_flow+h2+theta*theta


def source_fields(jet):
    density, stress, tidal, scalar = curvature_fields(jet)
    stress_eig = np.linalg.eigvalsh(stress)
    tidal_eig = np.linalg.eigvalsh(tidal)
    return {"absolute_density": np.abs(density), "negative_density": np.maximum(-density, 0),
        "principal_stress": np.max(np.abs(stress_eig), axis=-1),
        "tidal": np.max(np.abs(tidal_eig), axis=-1),
        "NEC_deficit": np.maximum(-(density+stress_eig[..., 0]), 0),
        "absolute_Ricci_scalar": np.abs(scalar)}


def candidate_jet_model():
    from research.compact100.validate import check_sources
    check_sources()
    path = UPSTREAM/"research/radical_compact/global_search/tensor_jet.py"
    spec = importlib.util.spec_from_file_location("compact100_frozen_jet", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.TensorPotential(CANDIDATE)


def sample(output):
    model = candidate_jet_model()
    path = UPSTREAM/"research/radical_compact/global_search/tensor_jet.py"
    r = np.unique(np.concatenate([np.linspace(float(a), float(b), 101)
        for a, b in zip(model.radial_edges[:-1], model.radial_edges[1:])]))
    mu = np.unique(np.r_[np.linspace(-1, 1, 801), list(map(float, model.angular_edges))])
    maxima = {"candidate": {}, "reference": {}}
    for start in range(0, len(r), 64):
        rr = r[start:start+64]
        for label, jet in [("candidate", model.spherical_jet(rr, mu)), ("reference", reference_jet(rr, mu))]:
            for name, values in source_fields(jet).items():
                pos = np.unravel_index(np.argmax(values), values.shape)
                if name not in maxima[label] or values[pos] > maxima[label][name]["value_per_m2"]:
                    maxima[label][name] = {"value_per_m2": float(values[pos]),
                        "r_m": float(rr[pos[0]]), "mu": float(mu[pos[1]])}
    result = {"schema_version": 1, "status": "numerical_only", "certified_extrema": False,
        "candidate_sha256": sha256(CANDIDATE.read_bytes()).hexdigest(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "candidate_jet_source_sha256": sha256(path.read_bytes()).hexdigest(),
        "grid": {"radial_nodes": len(r), "angular_nodes": len(mu), "domain": "11<=r<=100; full sphere"},
        "maxima": maxima, "candidate_to_reference_peak_ratios": {
            k: v["value_per_m2"]/maxima["reference"][k]["value_per_m2"] for k, v in maxima["candidate"].items()},
        "scope": "Same mesh for both models. Density/stress entries are Einstein-tensor quantities; SI stress multiplies by c^4/(8pi G), and tidal acceleration by c^2. Exterior of the candidate is exactly flat, but the mesh peaks are not certified global extrema."}
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps(result["candidate_to_reference_peak_ratios"], indent=2), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"results/local/compact100/physics.json")
    args = parser.parse_args(); sample(args.output)
