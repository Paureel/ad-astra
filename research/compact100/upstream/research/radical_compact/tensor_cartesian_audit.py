"""Independent Cartesian chain-rule audit for a rational tensor spline.

This intentionally does not call the searcher's field or energy functions.
Continuum claims belong to the separate exact Bernstein replay.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import argparse
import hashlib
import json
import time

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.interpolate import BSpline

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class IndependentDecoder:
    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text())
        d = self.data
        assert d["representation"]=="tensor_product_radial_angular_bspline"
        assert d["radial_degree"]==d["angular_degree"]==6
        self.rk = np.array([float(F(v)) for v in d["radial_knots_m"]])
        self.uk = np.array([float(F(v)) for v in d["angular_knots"]])
        self.C = np.array([[float(F(v)) for v in row] for row in d["coefficients"]])
        self.rb = BSpline(self.rk, np.eye(self.C.shape[1]), 6, extrapolate=False)
        self.ub = BSpline(self.uk, np.eye(self.C.shape[0]), 6, extrapolate=False)
        self.re = np.unique(self.rk)
        self.ue = np.unique(self.uk)

    def jets(self, r, mu):
        R = [self.rb(r,k) for k in range(3)]
        U = [self.ub(mu,k) for k in range(3)]
        return {(i,j):R[i]@self.C.T@U[j].T
                for i,j in ((0,0),(1,0),(0,1),(2,0),(1,1),(0,2))}

    def cartesian_hessian(self, r, mu, azimuth=.417):
        r = np.asarray(r)
        mu = np.asarray(mu)
        h = self.jets(r,mu)
        # The potential F(r,mu)=2*r*h(r,mu).
        Fr = 2*(h[0,0]+r[:,None]*h[1,0])
        Fu = 2*r[:,None]*h[0,1]
        Frr = 2*(2*h[1,0]+r[:,None]*h[2,0])
        Fru = 2*(h[0,1]+r[:,None]*h[1,1])
        Fuu = 2*r[:,None]*h[0,2]
        s = np.sqrt(np.maximum(0,1-mu*mu))
        n = np.stack((mu,s*np.cos(azimuth),s*np.sin(azimuth)),axis=-1)
        m = np.array([1.,0.,0.])-mu[:,None]*n
        nn = n[:,:,None]*n[:,None,:]
        nm = n[:,:,None]*m[:,None,:]+m[:,:,None]*n[:,None,:]
        mm = m[:,:,None]*m[:,None,:]
        transverse = np.eye(3)-nn
        H = Frr[:,:,None,None]*nn
        H += (Fru/r[:,None])[:,:,None,None]*nm
        H += (Fuu/r[:,None]**2)[:,:,None,None]*mm
        H += (Fr/r[:,None])[:,:,None,None]*transverse
        H -= (Fu/r[:,None]**2)[:,:,None,None]*(nm+mu[:,None,None]*transverse)
        return H

    def potential(self, q):
        q = np.asarray(q)
        r = np.linalg.norm(q)
        mu = q[0]/r
        return float(2*r*(self.rb(r)@self.C.T@self.ub(mu)))

    def energy(self, order_r, order_u):
        qr, wr = leggauss(order_r)
        qu, wu = leggauss(order_u)
        mu = np.concatenate([(a+b)/2+(b-a)*qu/2 for a,b in zip(self.ue[:-1],self.ue[1:])])
        weights_u = np.concatenate([(b-a)*wu/2 for a,b in zip(self.ue[:-1],self.ue[1:])])
        absolute = 0.
        signed = 0.
        for a,b in zip(self.re[:-1],self.re[1:]):
            r = (a+b)/2+(b-a)*qr/2
            H = self.cartesian_hessian(r,mu)
            Q = np.trace(H,axis1=-2,axis2=-1)**2-np.sum(H*H,axis=(-2,-1))
            weight = ((b-a)*wr/2*r*r)[:,None]*weights_u
            absolute += np.sum(weight*np.abs(Q))
            signed += np.sum(weight*Q)
        factor = 299792458.**4/(8*float(F(66743,10**15)))
        return {"radial_gauss_order":order_r,"angular_gauss_order":order_u,
                "absolute_energy_J":float(factor*absolute),
                "signed_energy_J":float(factor*signed),
                "absolute_polynomial_integral":float(absolute),
                "signed_polynomial_integral":float(signed)}


def point_checks(decoder):
    # Fixed points avoid knots and poles. Compare an independently rotated
    # Cartesian chain rule with direct finite differences of the potential.
    rows = []
    for r,mu,phi in ((12.72,.817,.31),(15.27,-.351,1.17),
                     (24.4,.637,2.07),(57.2,-.237,.77)):
        s = np.sqrt(1-mu*mu)
        q = r*np.array([mu,s*np.cos(phi),s*np.sin(phi)])
        analytic = decoder.cartesian_hessian([r],[mu],phi)[0,0]
        errors = []
        for step in (1e-3,5e-4,2e-4):
            fd = np.zeros((3,3))
            for i,j in product(range(3),repeat=2):
                ei = np.eye(3)[i]*step
                ej = np.eye(3)[j]*step
                if i==j:
                    fd[i,i] = (decoder.potential(q+ei)-2*decoder.potential(q)
                               +decoder.potential(q-ei))/step**2
                else:
                    fd[i,j] = (decoder.potential(q+ei+ej)-decoder.potential(q+ei-ej)
                               -decoder.potential(q-ei+ej)+decoder.potential(q-ei-ej))/(4*step**2)
            errors.append({"step_m":step,"max_absolute_error":float(np.max(np.abs(fd-analytic)))})
        values = []
        for angle in (0.,.317,1.71,2.37):
            H = decoder.cartesian_hessian([r],[mu],angle)[0,0]
            values.append(float(np.trace(H)**2-np.sum(H*H)))
        rows.append({"r_m":r,"mu":mu,"azimuth":phi,"finite_difference_checks":errors,
                     "rotation_Q_spread":float(max(values)-min(values))})
    assert all(min(v["max_absolute_error"] for v in row["finite_difference_checks"])<2e-5
               for row in rows)
    assert all(row["rotation_Q_spread"]<1e-11 for row in rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--receipt")
    args = parser.parse_args()
    started = time.monotonic()
    decoder = IndependentDecoder(args.candidate)
    checks = point_checks(decoder)
    rows = []
    for order_r,order_u in ((16,20),(28,32),(40,48)):
        row = decoder.energy(order_r,order_u)
        rows.append(row)
        print(json.dumps(row),flush=True)
    # A signed-zero check is informative because the true signed integral
    # is exactly zero for any compact perturbation, independently of fit.
    assert all(abs(row["signed_polynomial_integral"])<1e-8 for row in rows)
    out = {
        "status":"independent_numerical_audit","formal_certification":False,
        "candidate_path":str(decoder.path),"candidate_sha256":sha(decoder.path),
        "source_sha256":sha(Path(__file__)),
        "independence":"Cartesian r/mu chain rule and direct BSpline decoder; no search field or objective imports.",
        "potential_second_difference_checks":checks,"energy_refinement":rows,
        "signed_compact_integral_numerical_check":True,
        "core_correction":"Unchanged separately certified eta*Phi0 patch, not included in these shell estimates.",
        "elapsed_seconds":time.monotonic()-started,
    }
    if args.receipt:
        path = Path(args.receipt)
        proof = json.loads(path.read_text())
        assert proof["candidate_sha256"]==sha(decoder.path)
        lo,hi = map(float,proof["main_energy_J_interval_outward"])
        assert all(lo<row["absolute_energy_J"]<hi for row in rows)
        out["continuum_receipt_sha256"]=sha(path)
        out["all_three_estimates_inside_continuum_energy_interval"]=True
    target = HERE/(decoder.path.stem+"-cartesian-audit.json")
    target.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"audit":str(target),"sha256":sha(target),
                      "elapsed_seconds":out["elapsed_seconds"]}),flush=True)


if __name__=="__main__":
    main()
