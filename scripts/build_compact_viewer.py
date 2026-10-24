# SPDX-License-Identifier: Apache-2.0
"""Display artifacts for the exact compact100 candidate; never rescore history."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.compact100.geometry import CompactGeometry, CANDIDATE, EXPECTED_HASH, CONTRACT
from research.compact100.validate import check_sources

HERE = ROOT/"research/compact100"
CACHE_PATH = ROOT/"web/compact100-fields.bin"
NR, NM = 1025, 513


def read(path): return json.loads(Path(path).read_text())
def digest(path): return sha256(Path(path).read_bytes()).hexdigest()
def write(path, data): Path(path).write_text(json.dumps(data, separators=(",", ":"), allow_nan=False)+"\n")


def identity():
    check_sources()
    result = read(HERE/"result.json")
    if result["candidate_sha256"] != EXPECTED_HASH or result["model_source_sha256"] != digest(HERE/"geometry.py"):
        raise ValueError("Compact100 result/model identity differs; replay it first.")
    if not result["full_main_core_and_reference_replayed"] or result["formal_certification"]:
        raise ValueError("Expected the reproduced research result, without formal certification.")
    return result


def coefficients(model, r, mu):
    """Nonsingular Cartesian dyad coefficients of exact spline W and Hess Phi.

    W=A*e_x+B*n; H=C*nn+D*(en+ne)+E*ee+F*I. Both poles are regular.
    The cache only approximates display optics; all surfaces/densities use exact
    numerical spline fields, and the energy stays bound to the research replay.
    """
    r, mu = np.broadcast_arrays(r, mu)
    j = model._jets(r.ravel(), mu.ravel())
    h, hr, hu, hrr, hru, huu = (j[k].reshape(r.shape) for k in [(0,0),(1,0),(0,1),(2,0),(1,1),(0,2)])
    fr, frr = 2*(h+r*hr), 2*(2*hr+r*hrr)
    a, b, c = 2*hru, 2*huu/r, (fr-2*mu*hu)/r
    return np.stack([2*hu, fr-2*mu*hu, frr-2*mu*a+mu*mu*b-c, a-mu*b, b, c], axis=-1)


def build_cache(model):
    t, angular = np.linspace(0,1,NR), np.linspace(0,1,NM)
    mu = -np.cos(np.pi*angular)
    table = np.empty((NM,NR,8), dtype="<f4")
    for start in range(0, NM, 16):
        r, mm = np.meshgrid(11+89*t**3, mu[start:start+16])
        table[start:start+16,:,:6] = coefficients(model, r, mm)
    table[:,:,6:] = 0
    table[:,0,:] = 0
    table[:,-1,:] = [2,0,0,0,0,0,0,0]
    # Two RGBA textures, radial columns and angular rows; no runtime CDN.
    packed = np.concatenate([table[:,:,:4].ravel(),table[:,:,4:].ravel()])
    CACHE_PATH.write_bytes(packed.tobytes())
    rng = np.random.default_rng(26024)
    # Include a dense sample of the narrow inner wall and the regular poles.
    r = np.r_[rng.uniform(11,100,4096), rng.uniform(12,24,4096)]
    mu_test = np.r_[rng.uniform(-1,1,4096), rng.choice([-1.,1.],4096)]
    lookup = RegularGridInterpolator((angular,t), table[:,:,:6].astype(float))
    cached = lookup(np.stack([np.arccos(-mu_test)/np.pi, np.cbrt((r-11)/89)], axis=-1))
    exact = coefficients(model,r,mu_test)
    def fields(c):
        n=np.stack([mu_test,np.sqrt(1-mu_test**2),np.zeros_like(r)],axis=-1); e=np.array([1.,0,0])
        w=c[:,0,None]*e+c[:,1,None]*n
        h=(c[:,2,None,None]*n[:,:,None]*n[:,None,:]+c[:,3,None,None]*(n[:,:,None]*e[None,None,:]+e[None,:,None]*n[:,None,:])
           +c[:,4,None,None]*np.outer(e,e)+c[:,5,None,None]*np.eye(3))
        return w,h
    wc,hc=fields(cached); we,he=fields(exact)
    audit={"sample_count":len(r), "max_shift_abs_error":float(np.max(np.abs(wc-we))),
           "max_hessian_abs_error_per_m":float(np.max(np.abs(hc-he))),
           "scope":"Seeded off-grid samples, including poles/inner wall; not global error bounds."}
    if audit["max_shift_abs_error"] > .002 or audit["max_hessian_abs_error_per_m"] > .003:
        raise ValueError("Refine the optical cache: "+str(audit))
    return {"path":"compact100-fields.bin","sha256":digest(CACHE_PATH),"radial_nodes":NR,"angular_nodes":NM,
            "encoding":"two RGBA float32 little-endian textures; A,B,C,D / E,F,0,0",
            "radial_coordinate":"t=cbrt((r-11)/89)","angular_coordinate":"s=acos(-mu)/pi","audit":audit}


def build_solution():
    from build_optics import build
    result=identity(); model=CompactGeometry()
    radial=np.unique(np.r_[np.linspace(0,100,201),np.linspace(11,25,113),model.radial_edges])
    solution=build(geometry=model, identity=(model.data["id"],EXPECTED_HASH,result["model_source_sha256"]),radial=radial,
                   optical_precision={"rtol":2e-13,"atol":1e-14,"max_step":.1},coordinate_digits=10)
    origin=np.array([-4.,-5.,3.]); view=-origin/np.linalg.norm(origin)
    def rhs(_ct,state):
        _,w,h=model.fields(state[:3]); n=state[3:6];kn=h@n;rate=n@kn
        return np.r_[w-n,-kn+n*rate,-rate]
    inside=solve_ivp(rhs,(0,48),np.r_[origin,-view,0.],method="DOP853",rtol=2e-12,atol=1e-13,max_step=.1)
    if not inside.success: raise ValueError("Cabin optical reference failed.")
    solution["optical_inside_reference"]={"origin":origin.tolist(),"view":view.tolist(),"past_ct_m":48,
        "state":inside.y[:,-1].tolist(),"method":"DOP853","rtol":2e-12,"atol":1e-13,"max_step_ct_m":.1}
    return solution


def main():
    result=identity(); model=CompactGeometry()
    default=json.loads((ROOT/"web/default-result.js").read_text().removeprefix("window.WARP_DEFAULT_RESULT = ").strip().removesuffix(";"))
    cache=build_cache(model)
    axis=np.unique(np.r_[np.arange(-100,101,5),np.arange(-30,30.01,.5)])
    slices=[]
    for plane,offset in [("xy",0),("yz",0),("yz",-13.5),("yz",13.5),("yz",30)]:
        u,v=np.meshgrid(axis,axis)
        points=np.stack([u,v,np.full_like(u,offset)] if plane=="xy" else [np.full_like(u,offset),u,v],axis=-1)
        slices.append({"id":f"{plane}-{offset}","plane":plane,"offset_m":offset,"u_m":axis.tolist(),"v_m":axis.tolist(),
                       "rho_J_m3":model.density(points).ravel().tolist()})
    estimate=result["independent_energy_refinement"][-1]["absolute_energy_J"]
    benchmark={**default["benchmark"],"id":"compact100-research","version":"1","scenario_label":"Compact 100 m"}
    energy={"quantity":default["energy"]["quantity"],"value_J":estimate,"value_kind":"estimate","significant_digits":8,
        "estimate_J":estimate,"interval_J":list(map(float,result["energy_J_interval"])),
        "positive_J":estimate/2,"negative_J":estimate/2,"tail":{"absolute_J":0},"error_estimate_J":None,
        "error_kind":"Displayed value: refined 40/48 per-cell numerical quadrature estimate. Separate replayed outward continuum enclosure; no formal Lean GR certificate.",
        "guaranteed_saving_percent":float(result["guaranteed_saving_percent"]["lower"])}
    provenance={"created_utc":result["evaluated_utc"],"candidate_file_sha256":EXPECTED_HASH,
        "evaluator_source_sha256":result["model_source_sha256"],"benchmark_sha256":digest(CONTRACT),
        "generator_sha256":digest(__file__),"research_result_sha256":digest(HERE/"result.json"),
        "git_author":{"name":"Paureel"},"optical_cache":cache}
    artifact={"schema_version":1,"benchmark":benchmark,"candidate":{"id":model.data["id"],"parameter_hash":EXPECTED_HASH,
        "parameters":{"family":"compact100","speed_c":2,"R_m":20,"sigma_per_m":1,"outer_radius_m":100,
                      "radial_knots_m":model.data["radial_knots_m"],"angular_knots":model.data["angular_knots"],
                      "tensor_coefficients":model.data["coefficients"],"coefficients":[]}},
        "energy":energy,"geometry":{**default["geometry"],"extent_m":100,"isosurfaces":[]},
        "display":default["display"],"slices":slices,"rays":[],"provenance":provenance,
        "status":{"numerical":"Replayed continuum bounds and geometric caps; separate research scenario","formal_certification":False}}
    write(ROOT/"results/compact100-viewer.json",artifact)
    write(ROOT/"results/compact100-display-report.json",{k:artifact[k] for k in ["schema_version","benchmark","candidate","energy","provenance","status"]})
    print("Generated compact100 viewer, report and optical cache",cache["audit"],flush=True)


if __name__=="__main__": main()
