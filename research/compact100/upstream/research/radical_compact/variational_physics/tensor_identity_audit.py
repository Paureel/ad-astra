"""Independent Cartesian algebra audit of the tensor-spline verifier.

Uses a Laurent polynomial ring in r,mu,s with s^2=1-mu^2. Direct Cartesian
derivatives of 2*x^q*r^(p+1-q) cover every bivariate monomial h=r^p*mu^q
through degree 6 in each variable. In-memory instrumentation changes only
the builder's return statement to expose its intermediate fields.
No producer source or receipt is modified.
"""
from pathlib import Path
from fractions import Fraction as F
from math import comb
from itertools import product
from bisect import bisect_right
import ast
import inspect
import importlib.util
import hashlib
import json
import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SOURCE = ROOT/'research/radical_compact/tensor_validation/bernstein_replay.py'
CANDIDATE = ROOT/'research/radical_compact/global_search/tensor-polished-candidate.json'
RECEIPT = ROOT/'research/radical_compact/tensor_validation/tensor-polished-final-verified.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(*ps):
    out = {}
    for p in ps:
        for k,v in p.items():
            out[k] = out.get(k,F(0))+v
    return {k:v for k,v in out.items() if v}


def scale(p,c):
    return {k:v*c for k,v in p.items() if v*c}


def mon(r=0,m=0,s=0,c=1):
    return {(r,m,s):F(c)} if c else {}


def mul(p,q):
    out = {}
    for (r,m,s),v in p.items():
        for (R,M,S),w in q.items():
            if s+S < 2:
                key = (r+R,m+M,s+S)
                out[key] = out.get(key,F(0))+v*w
            else:
                assert s+S == 2
                for dm,sign in ((0,1),(2,-1)):
                    key = (r+R,m+M+dm,0)
                    out[key] = out.get(key,F(0))+sign*v*w
    return {k:v for k,v in out.items() if v}


def cartesian_jet(p,q):
    """Exact derivatives of Phi=2*x^q*r^d, d=p+1-q."""
    d = p+1-q
    X = [mon(1,1),mon(1,0,1),{}]
    radial = mon(d)
    dr = [scale(mul(mon(d-2),X[i]),d) for i in range(3)]
    ddr = [[add(mon(d-2,c=d*int(i==j)),
                scale(mul(mon(d-4),mul(X[i],X[j])),d*(d-2)))
            for j in range(3)] for i in range(3)]
    dddr = [[[add(scale(mul(mon(d-4),add(
                    scale(X[k],int(i==j)),scale(X[j],int(i==k)),scale(X[i],int(j==k)))),d*(d-2)),
                    scale(mul(mon(d-6),mul(mul(X[i],X[j]),X[k])),d*(d-2)*(d-4)))
              for k in range(3)] for j in range(3)] for i in range(3)]
    xder = []
    for order in range(4):
        coefficient = 1
        for j in range(order):
            coefficient *= q-j
        xder.append(mon(q-order,q-order,c=coefficient) if q>=order else {})
    W = [scale(add(mul(xder[0],dr[i]),scale(mul(xder[1],radial),int(i==0))),2) for i in range(3)]
    H = [[scale(add(mul(xder[0],ddr[i][j]),
            mul(xder[1],add(scale(dr[j],int(i==0)),scale(dr[i],int(j==0)))),
            scale(mul(xder[2],radial),int(i==j==0))),2) for j in range(3)] for i in range(3)]
    T = [[[scale(add(mul(xder[0],dddr[i][j][k]),
             mul(xder[1],add(scale(ddr[j][k],int(i==0)),scale(ddr[i][k],int(j==0)),scale(ddr[i][j],int(k==0)))),
             mul(xder[2],add(scale(dr[k],int(i==j==0)),scale(dr[j],int(i==k==0)),scale(dr[i],int(j==k==0)))),
             scale(mul(xder[3],radial),int(i==j==k==0))),2)
          for k in range(3)] for j in range(3)] for i in range(3)]
    rotation = [[mon(0,1),mon(0,0,1,c=-1),{}],
                [mon(0,0,1),mon(0,1),{}],[{},{},mon()]]

    def rotate(tensor,indices):
        result = {}
        for cart in product(range(3),repeat=len(indices)):
            v = tensor
            for i in cart:
                v = v[i]
            for i,j in zip(cart,indices):
                v = mul(v,rotation[i][j])
            result = add(result,v)
        return result

    Ws = [rotate(W,(i,)) for i in range(3)]
    Hs = [[mul(mon(1),rotate(H,(i,j))) for j in range(3)] for i in range(3)]
    Ts = [[[mul(mon(2),rotate(T,(i,j,k))) for k in range(3)] for j in range(3)] for i in range(3)]
    return Ws,Hs,Ts


def no_s(p):
    assert all(s==0 for r,m,s in p)
    assert all(r>=0 and m>=0 for r,m,s in p)
    return {(r,m):v for (r,m,s),v in p.items()}


def polynomial_invariants(W,H,T):
    w2 = add(*(mul(v,v) for v in W))
    h2 = add(*(mul(v,v) for row in H for v in row))
    t2 = add(*(mul(v,v) for plane in T for row in plane for v in row))
    tr = add(*(H[i][i] for i in range(3)))
    Q = add(mul(tr,tr),scale(h2,-1))
    return [no_s(Q),no_s(add(mon(c=16),scale(w2,-1))),
            no_s(add(mon(2,c=4),scale(h2,-1))),no_s(add(mon(4,c=16),scale(t2,-1)))]


def compose(p,rl,rw,ml,mw):
    out = {}
    for (i,j),v in p.items():
        for k in range(i+1):
            for l in range(j+1):
                key = (k,l)
                value = v*comb(i,k)*rl**(i-k)*rw**k*comb(j,l)*ml**(j-l)*mw**l
                out[key] = out.get(key,F(0))+value
    return {k:v for k,v in out.items() if v}


def deboor(knots,co,degree,x):
    n = len(co)
    span = n-1 if x==knots[n] else bisect_right(knots,x)-1
    assert degree<=span<n
    d = [co[span-degree+j] for j in range(degree+1)]
    for k in range(1,degree+1):
        for j in range(degree,k-1,-1):
            den = knots[span+1+j-k]-knots[span-degree+j]
            alpha = (x-knots[span-degree+j])/den
            d[j] = (1-alpha)*d[j-1]+alpha*d[j]
    return d[degree]


def main():
    assert sha(SOURCE)=='e36bad6c6fd8a64e2690164779640ad528f18a13001d318d824e27a39c97c754'
    assert sha(CANDIDATE)=='6c0cdb24b7e376f3670c294647f49c57420ded22f57b5083f00900c6da0eb041'
    assert sha(RECEIPT)=='fe61e644bacfdca3f5d0142968db571c18f3fda3789a92b7ab323057d5598ee8'
    spec = importlib.util.spec_from_file_location('audited_tensor_verifier',SOURCE)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    tree = ast.parse(inspect.getsource(verifier.build_polynomials))
    ret = tree.body[0].body[-1]
    assert isinstance(ret,ast.Return) and ast.dump(ret.value)==ast.dump(ast.Tuple(elts=[ast.Name(id='Q',ctx=ast.Load()),ast.Name(id='residuals',ctx=ast.Load())],ctx=ast.Load()))
    ret.value.elts.append(ast.Name(id='fields',ctx=ast.Load()))
    ast.fix_missing_locations(tree)
    namespace = dict(vars(verifier))
    exec(compile(tree,'<return-only-audit-instrumentation>','exec'),namespace)
    build = namespace['build_polynomials']
    identity = np.array([[F(i==j) for j in range(7)] for i in range(7)],dtype=object)
    span = (F(0),F(1),list(range(7)),identity)
    basis = {}
    component_checks = invariant_checks = 0
    for p in range(7):
        for q in range(7):
            co = np.full((7,7),F(0),dtype=object)
            co[q,p] = F(1)
            Q,residuals,fields = build(span,span,co)
            W,H,T = cartesian_jet(p,q)
            basis[p,q] = (W,H,T)
            expected = {'Wr':W[0],'Wt':W[1],
                'A':H[0][0],'B':H[0][1],'C':H[1][1],'D':H[2][2],
                'Ar':T[0][0][0],'Br':T[0][0][1],'Cr':T[0][1][1],
                'Dr':T[0][2][2],'Tt':T[1][1][1],'Tp':T[1][2][2]}
            for name,actual in expected.items():
                proposed = {(i,j,0):v for (i,j),v in fields[name].items()}
                if name in ('Wt','B','Br','Tt','Tp'):
                    proposed = mul(proposed,mon(0,0,1))
                assert proposed==actual,(p,q,name,proposed,actual)
                component_checks += 1
            assert [Q]+residuals == polynomial_invariants(W,H,T)
            invariant_checks += 4
    local_checks = 0
    for rl,rr,ml,mr in ((F(11),F(23,2),F(-99,100),F(-97,100)),
                       (F(40),F(45),F(1,10),F(1,5))):
        rw,mw = rr-rl,mr-ml
        local = {(i,j):F((i+1)*(j+2)-13,17+i+j) for i in range(7) for j in range(7)}
        global_h = compose(local,-rl/rw,1/rw,-ml/mw,1/mw)
        W = [{} for i in range(3)]
        H = [[{} for j in range(3)] for i in range(3)]
        T = [[[{} for k in range(3)] for j in range(3)] for i in range(3)]
        for key,c in global_h.items():
            w,h,t = basis[key]
            for i in range(3):
                W[i] = add(W[i],scale(w[i],c))
                for j in range(3):
                    H[i][j] = add(H[i][j],scale(h[i][j],c))
                    for k in range(3):
                        T[i][j][k] = add(T[i][j][k],scale(t[i][j][k],c))
        co = np.array([[local[i,j] for i in range(7)] for j in range(7)],dtype=object)
        Q,residuals,fields = build((rl,rr,list(range(7)),identity),(ml,mr,list(range(7)),identity),co)
        expected = [compose(v,rl,rw,ml,mw) for v in polynomial_invariants(W,H,T)]
        assert [Q]+residuals == expected
        local_checks += 4
    data = json.loads(CANDIDATE.read_text())
    assert data['radial_degree']==data['angular_degree']==6
    kr = list(map(F,data['radial_knots_m']))
    km = list(map(F,data['angular_knots']))
    for knots,left,right in ((kr,F(11),F(100)),(km,F(-1),F(1))):
        assert knots[:7]==[left]*7 and knots[-7:]==[right]*7
        assert all(left<x<right for x in knots[7:-7])
        assert all(x<y for x,y in zip(knots[7:-7],knots[8:-7]))
    coefficients = [list(map(F,row)) for row in data['coefficients']]
    assert len(coefficients)==len(km)-7
    assert all(len(row)==len(kr)-7 for row in coefficients)
    greville = [sum(km[j+1:j+7],F(0))/6 for j in range(len(coefficients))]
    endpoint_checks = 0
    for j,row in enumerate(coefficients):
        controls = row
        knots = kr
        degree = 6
        for order in range(6):
            assert controls[0]==0
            assert controls[-1]==(greville[j] if order==0 else 0)
            endpoint_checks += 2
            if order<5:
                controls = [degree*(controls[i+1]-controls[i])/(knots[i+degree+1]-knots[i+1])
                            for i in range(len(controls)-1)]
                knots = knots[1:-1]
                degree -= 1
    reproduction_checks = 0
    edges = sorted(set(km))
    for left,right in zip(edges,edges[1:]):
        for j in range(1,8):
            x = left+(right-left)*F(j,8)
            assert deboor(km,greville,6,x)==x
            reproduction_checks += 1
    proof = json.loads(RECEIPT.read_text())
    assert proof['candidate_sha256']==sha(CANDIDATE)
    assert proof['verifier_sha256']==sha(SOURCE)
    assert proof['contract_sha256']==sha(ROOT/'research/expanded_family/localized-exterior-contract.json')
    assert proof['original_benchmark_sha256']==sha(ROOT/'benchmarks/rodal-2c-v1.json')
    assert proof['core_receipt_sha256']==sha(ROOT/'research/expanded_family/radial_control/log-cylinder-caps-core-level-9.json')
    assert proof['complete_domain_covered'] and proof['all_global_caps_pass']
    assert proof['angular_domain']==['-1','1'] and proof['reflection_symmetry_assumed'] is False
    assert len(proof['cells'])==proof['radial_spans']*proof['angular_spans']==1040
    assert all(all(c['pass'] for c in row['cap_results']) for row in proof['cells'])
    lo = sum((F(row['polynomial_integral_exact'][0]) for row in proof['cells']),F(0))
    hi = sum((F(row['polynomial_integral_exact'][1]) for row in proof['cells']),F(0))
    factor = F(299792458)**4/(8*F(66743,10**15))
    assert F(proof['energy_prefactor_exact'])==factor
    total = factor*hi+F(proof['core_energy_upper_J_exact'])
    assert total==F(proof['total_energy_upper_J_exact'])
    assert F(proof['main_energy_J_interval_outward'][0])<=factor*lo
    assert F(proof['main_energy_J_interval_outward'][1])>=factor*hi
    assert F(proof['total_energy_upper_J_outward'])>=total
    assert F(proof['guaranteed_reduction_fraction_lower'])<=1-total/F(proof['reference_lower_J_exact'])
    out = {
        'status':'independently_reproduced','formal_certification':False,
        'evidence_kind':'exact_symbolic_Cartesian_tensor_and_endpoint_audit_plus_receipt_arithmetic',
        'script_sha256':sha(Path(__file__)),
        'verifier_sha256':sha(SOURCE),'candidate_sha256':sha(CANDIDATE),'receipt_sha256':sha(RECEIPT),
        'symbolic_bivariate_basis_monomials':49,
        'symbolic_field_component_identities':component_checks,
        'symbolic_invariant_identities':invariant_checks,
        'dense_mixed_local_coordinate_invariant_identities':local_checks,
        'exact_radial_endpoint_jet_checks':endpoint_checks,
        'exact_angular_linear_reproduction_checks':reproduction_checks,
        'independent_simple_knot_clamping_and_coefficient_shape_checks':True,
        'endpoint_argument':'Degree 6 with simple interior knots is C5. The first 6 radial coefficients vanish, and the last 6 equal angular Greville values, giving the required value and radial derivatives through order 5. Seven exact distinct checks per degree 6 angular span prove reproduction of mu. Composing the one-sided endpoint polynomials with mu=x/r is smooth at the axes for r>=11.',
        'instrumentation':'Only the in-memory return expression is extended to expose intermediate fields; the producer source is unchanged. All Cartesian derivatives and Laurent polynomial algebra are independent.',
        'full_sphere_energy_prefactor_verified':True,
        'exact_cell_energy_sum_and_core_addition_verified':True,
        'main_energy_J_interval_outward':proof['main_energy_J_interval_outward'],
        'total_energy_upper_J_outward':proof['total_energy_upper_J_outward'],
        'guaranteed_reduction_fraction_lower':proof['guaranteed_reduction_fraction_lower'],
        'independent_full_Bernstein_subdivision_rerun':False,
        'limitations':'The frozen Bernstein subdivision engine and core enclosure have earlier separate audits. This audit establishes the new generic tensor identities, coordinate scaling, endpoint construction and final exact energy arithmetic; it does not rerun all subdivision cells or establish material realization.'
    }
    path = HERE/'tensor-identity-audit.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    print('audit_receipt_sha256',sha(path))


if __name__=='__main__':
    main()
