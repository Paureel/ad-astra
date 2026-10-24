"""Generate display-only selected-metric surfaces, density samples and audits.

Scientific reports and scores are never rewritten. Geometry is evaluated by the
existing reference Python implementation. Run with the reference virtualenv.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from warpproof.geometry import Geometry
from warpproof.model import load_candidate
from warpproof.reporting import source_hash

ROOT = Path(__file__).resolve().parents[1]


def far_optical_reference(geometry):
    """Independent raw-momentum Hamilton equations for a sensitive off-axis ray."""
    origin = np.array([-220., 0., 0.])
    view = np.array([.9022466247443952, -.3715129547666677, .21892727691607194])
    view /= np.linalg.norm(view)
    n = -view
    p0 = float(geometry.fields(origin)[1] @ n - 1)
    def rhs(_l, state):
        q, p = state[:3], state[3:]
        _, W, K = geometry.fields(q)
        omega = -p0 + W @ p
        return np.concatenate((W-p/omega, -K.T @ p))
    def stop_at(radius):
        def event(_l, state):
            return np.linalg.norm(state[:3])-radius
        event.terminal = True
        event.direction = 1
        return event
    near = solve_ivp(rhs, (0,10000), np.concatenate((origin,n)), method="DOP853",
                     rtol=2e-11, atol=1e-12, max_step=.25, events=stop_at(256))
    if not near.success or not len(near.t_events[0]):
        raise ValueError("Near-field Hamiltonian optical audit failed.")
    far = solve_ivp(rhs, (near.t[-1],200000), near.y[:,-1], method="DOP853",
                    rtol=2e-11, atol=1e-12, max_step=4096, events=stop_at(65536))
    if not far.success or not len(far.t_events[0]):
        raise ValueError("Finite-boundary Hamiltonian optical audit failed.")
    q,p = far.y[:3,-1],far.y[3:,-1]
    omega = -p0 + geometry.fields(q)[1] @ p
    return {"origin":origin.tolist(),"view":view.tolist(),"source_direction":(-p/omega).tolist(),
            "boundary_m":65536,"ct_m":float(far.t[-1]),
            "null_residual":float(abs(p@p-omega**2)/(p@p+omega**2)),
            "method":"DOP853 raw covariant momentum, fixed p0, exact boundary event",
            "rtol":2e-11,"atol":1e-12,"near_max_step_ct_m":.25,"far_max_step_ct_m":4096}


def build(candidate_path):
    candidate = load_candidate(ROOT / candidate_path)
    geometry = Geometry(candidate)
    theta = np.linspace(0, np.pi, 129)
    directions = np.stack((np.cos(theta), np.sin(theta), np.zeros_like(theta)), axis=-1)
    low, high = np.zeros(len(theta)), np.full(len(theta), 128.)
    for _ in range(48):
        middle = (low + high) / 2
        values = np.linalg.norm(geometry.fields(directions * middle[:, None])[1], axis=-1)
        low = np.where(values < 1, middle, low)
        high = np.where(values >= 1, middle, high)
    radius = (low + high) / 2
    surface = directions * radius[:, None]
    residual = np.max(np.abs(np.linalg.norm(geometry.fields(surface)[1], axis=-1) - 1))
    # Check the resolved radial topology instead of silently choosing among
    # several sampled branches for a future, substantially different candidate.
    scan = directions[:, None, :] * np.linspace(0, 128, 513)[None, :, None]
    sign = np.linalg.norm(geometry.fields(scan)[1], axis=-1) >= 1
    if not np.all(np.count_nonzero(sign[:, 1:] != sign[:, :-1], axis=1) == 1):
        raise ValueError("Stationary-limit surface has multiple/unresolved sampled branches; use a general contour mesh.")
    radial = np.unique(np.concatenate((np.linspace(0, 40, 81), np.linspace(17, 23, 49))))
    angle = np.linspace(0, np.pi, 49)
    rr, aa = np.meshgrid(radial, angle, indexing="ij")
    points = np.stack((rr*np.cos(aa), rr*np.sin(aa), np.zeros_like(rr)), axis=-1)
    rho = geometry.density(points)
    default = json.loads((ROOT / "web/default-result.js").read_text().removeprefix("window.WARP_DEFAULT_RESULT = ").strip().removesuffix(";"))
    scale = default["display"]["rho_scale_abs_J_m3"]
    cloud = [[round(float(x), 7), round(float(y), 7), float(f"{value/scale:.8g}")]
             for (x, y, _), value in zip(points.reshape(-1, 3), rho.ravel()) if abs(value/scale) >= .00005]
    audit_points = np.array([[0,0,0],[.0001,.0002,-.0001],[9.9,.1,0],[10.1,0,0],
                             [19.9,0,0],[20,0,0],[20.1,.4,.2],[0,20,0],[-17,9,7],
                             [21,12,-8],[31,-4,16],[39.9,0,.1],[40.1,2,0],[120,-40,50],[1024,0,0]], dtype=float)
    _, W, K = geometry.fields(audit_points)
    fixtures = [{"q":q.tolist(),"W":w.tolist(),"K":k.ravel().tolist()} for q,w,k in zip(audit_points,W,K)]
    # A short, independently adaptive backward integration for browser RK4 audits.
    origin = np.array([-46.,-65.,43.])
    view = -origin / np.linalg.norm(origin)
    n0 = -view
    def rhs(_s, state):
        q, n = state[:3], state[3:6]
        _, w, k = geometry.fields(q)
        kn = k @ n
        rate = float(n @ kn)
        return np.concatenate((w-n, -kn+n*rate, [-rate]))
    solution = solve_ivp(rhs, (0,48), np.concatenate((origin,n0,[0.])),
                         method="DOP853", rtol=2e-11, atol=1e-12, max_step=.25)
    if not solution.success:
        raise ValueError("Independent optical reference integration failed.")
    return {
        "candidate_id":candidate.id,"parameter_hash":candidate.parameter_hash,
        "evaluator_source_sha256":source_hash(),
        "surface_quantity":"norm(grad(Phi)) = 1; g_00 = 0 stationary limit, not an event horizon",
        "surface_meridian":np.round(surface[:,:2],10).tolist(),
        "surface_max_sample_residual":float(residual),
        "density_scale_J_m3":scale,"density_meridian":cloud,
        "density_sampling":"Direct Python fields on an adaptive radial/angle grid; 12 azimuth samples per meridional point in the viewer",
        "field_audit":fixtures,
        "optical_reference":{"origin":origin.tolist(),"view":view.tolist(),"past_ct_m":48,
                             "state":solution.y[:,-1].tolist(),"method":"DOP853", "rtol":2e-11,"atol":1e-12},
        "optical_far_reference":far_optical_reference(geometry),
    }


def main():
    manifest = json.loads((ROOT / "records/history.json").read_text())
    paths = {sha256(p.read_bytes()).hexdigest(): p for p in sorted((ROOT / "candidates").glob("*.json"))}
    rows = []
    for entry in manifest["evaluations"]:
        report = json.loads((ROOT / entry["report_path"]).read_text())
        path = paths.get(report["provenance"]["candidate_file_sha256"])
        if path is None:
            raise ValueError(f"Missing exact candidate file for {entry['id']}")
        row = build(path)
        if row["parameter_hash"] != report["candidate"]["parameter_hash"] or row["evaluator_source_sha256"] != report["provenance"]["evaluator_source_sha256"]:
            raise ValueError(f"Candidate/evaluator identity mismatch for {entry['id']}")
        if not any(r["parameter_hash"] == row["parameter_hash"] for r in rows):
            rows.append(row)
    payload = {"schema_version":1,"solutions":rows,"generator_sha256":sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT / "web/solution-data.js").write_text("window.AD_ASTRA_SOLUTIONS = " + json.dumps(payload,separators=(",",":"),allow_nan=False) + ";\n")
    for row in rows:
        print(row["candidate_id"], "surface residual", row["surface_max_sample_residual"], "density samples",len(row["density_meridian"]))


if __name__ == "__main__":
    main()
