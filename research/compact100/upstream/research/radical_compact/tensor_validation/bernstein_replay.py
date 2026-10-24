"""Full-sphere exact Bernstein replay of radial/angular tensor splines.

The data contain h(r,mu), with Phi_main=2*r*h. Every polynomial cell is
reconstructed by exact Cox-de Boor arithmetic in both coordinates. There
is no reflection assumption. The frozen phase1 integer Bernstein engine
is reused read-only, with its source bound explicitly below.
"""
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
import argparse,hashlib,importlib.util,json,time
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
ENGINE=ROOT/'research/expanded_family/angular_search/localized/bernstein_replay.py'
ENGINE_SHA='09b1efbb736cc5c04b657449a3493f75becb398d4d6f98aff1121c032db1975b'
PRIMITIVES=ROOT/'research/radial_extension/interval_verify.py'
PRIMITIVES_SHA='09f847537a935ca437bfd41fb72df57b7752a8a3f5c80a948bf705df0a1d981e'
CONTRACT=ROOT/'research/expanded_family/localized-exterior-contract.json'
BENCHMARK=ROOT/'benchmarks/rodal-2c-v1.json'
BENCHMARK_SHA='dec6cdcc48e234a581dc1068f3c3bee62c73c41f14ac10c37908f5d85d6cd3e4'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(ENGINE)==ENGINE_SHA and sha(PRIMITIVES)==PRIMITIVES_SHA
spec=importlib.util.spec_from_file_location('frozen_bernstein_engine',ENGINE)
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
pa,ps,pm=engine.pa,engine.ps,engine.pm


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON key: '+key)
        result[key]=value
    return result


def rational(value):
    assert isinstance(value,str),'Exact values must be rational strings.'
    return F(value)


def knots_check(values,degree,left,right):
    assert type(degree) is int and degree==6
    knots=list(map(rational,values))
    assert len(knots)>=14 and knots[:7]==[left]*7 and knots[-7:]==[right]*7
    inside=knots[7:-7]
    assert all(left<x<right for x in inside)
    assert all(x<y for x,y in zip(inside,inside[1:])), 'Interior knots must be simple.'
    return knots


def decode(path):
    data=json.loads(path.read_text(),object_pairs_hook=unique_object)
    expected={'schema_version','id','status','formal_certification','contract_id','contract_sha256',
       'scenario','outer_radius_m','representation','radial_degree','angular_degree',
       'radial_knots_m','angular_knots','coefficients','coefficient_order','main_definition',
       'core_correction','symmetry','regularity','admission_status'}
    assert set(data)==expected
    assert type(data['schema_version']) is int and data['schema_version']==1
    assert data['status']=='numerical_only' and data['formal_certification'] is False
    assert data['contract_id']=='rodal-2c-localized-exterior-research'
    assert data['contract_sha256']==sha(CONTRACT) and sha(BENCHMARK)==BENCHMARK_SHA
    assert data['scenario']=='compact_spherical_exterior' and rational(data['outer_radius_m'])==100
    assert data['representation']=='tensor_product_radial_angular_bspline'
    assert data['coefficient_order']=='Rows angular basis index, columns radial basis index'
    assert data['core_correction']=='eta(r)*Phi0, eta=1 onr<=10, eta=1-S(r-10) on10<r<11, eta0beyond11; degree11 smootherstepS'
    kr=knots_check(data['radial_knots_m'],data['radial_degree'],F(11),F(100))
    km=knots_check(data['angular_knots'],data['angular_degree'],F(-1),F(1))
    nr,nm=len(kr)-7,len(km)-7
    assert len(data['coefficients'])==nm
    co=np.array([list(map(rational,row)) for row in data['coefficients']],dtype=object)
    assert co.shape==(nm,nr)
    for j,row in enumerate(co):
        greville=sum(km[j+1:j+7],F(0))/6
        assert list(row[:6])==[F(0)]*6
        assert list(row[-6:])==[greville]*6
    return data,kr,km,co


def extraction(knots):
    """Each span: exact local power coefficients of its seven active bases."""
    out=[];n=len(knots)-7
    for span in range(6,n):
        left,right=knots[span:span+2]
        if left==right:continue
        width=right-left
        @lru_cache(None)
        def basis(i,degree):
            if degree==0:return (F(i==span),)
            value=[F(0)]
            den=knots[i+degree]-knots[i]
            if den:value=engine.iv.poly_add(value,engine.iv.poly_linear(basis(i,degree-1),(left-knots[i])/den,width/den))
            den=knots[i+degree+1]-knots[i+1]
            if den:value=engine.iv.poly_add(value,engine.iv.poly_linear(basis(i+1,degree-1),(knots[i+degree+1]-left)/den,-width/den))
            return tuple(value)
        indices=list(range(span-6,span+1))
        power=np.array([list(basis(i,6))+[F(0)]*(7-len(basis(i,6))) for i in indices],dtype=object).T
        assert all(sum(power[k,j] for j in range(7))==F(k==0) for k in range(7))
        out.append((left,right,indices,power))
    return out


def derivative(p,axis,width):
    out={}
    for (i,j),value in p.items():
        degree=(i,j)[axis]
        if degree:out[(i-int(axis==0),j-int(axis==1))]=value*degree/width
    return out


def build_polynomials(radial,angular,co):
    left,right,ri,Er=radial;mleft,mright,mi,Em=angular
    coefficients=Er@co[np.ix_(mi,ri)].T@Em.T
    h={(i,j):coefficients[i,j] for i in range(7) for j in range(7) if coefficients[i,j]}
    hr=derivative(h,0,right-left);hrr=derivative(hr,0,right-left);hrrr=derivative(hrr,0,right-left)
    hm=derivative(h,1,mright-mleft);hmm=derivative(hm,1,mright-mleft);hmmm=derivative(hmm,1,mright-mleft)
    hrm=derivative(hr,1,mright-mleft);hrmm=derivative(hrm,1,mright-mleft);hrrm=derivative(hrr,1,mright-mleft)
    one={(0,0):F(1)};r={(0,0):left,(1,0):right-left};mu={(0,0):mleft,(0,1):mright-mleft}
    r2=pm(r,r);r4=pm(r2,r2);s2=pa(one,ps(pm(mu,mu),-1))
    rh=pm(r,hr);K=pa(rh,ps(h,-1));Km=pa(pm(r,hrm),ps(hm,-1));Kmm=pa(pm(r,hrmm),ps(hmm,-1))
    fields={
        'Wr':ps(pa(h,rh),2),'Wt':ps(hm,-2),
        'A':ps(pm(r,pa(ps(hr,2),pm(r,hrr))),2),
        'B':ps(pm(r,hrm),-2),
        'C':ps(pa(rh,h,pm(s2,hmm),ps(pm(mu,hm),-1)),2),
        'D':ps(pa(rh,h,ps(pm(mu,hm),-1)),2),
        'Ar':ps(pm(r2,pa(ps(hrr,3),pm(r,hrrr))),2),
        'Br':ps(pm(r2,hrrm),-2),
        'Cr':ps(pa(pm(r2,hrr),K,pm(s2,Kmm),ps(pm(mu,Km),-1)),2),
        'Dr':ps(pa(pm(r2,hrr),K,ps(pm(mu,Km),-1)),2),
        'Tt':ps(pa(ps(pm(r,hrm),3),pm(s2,hmmm),ps(pm(mu,hmm),-3)),-2),
        'Tp':ps(pa(pm(r,hrm),ps(pm(mu,hmm),-1)),-2),
    }
    sq=lambda name:pm(fields[name],fields[name])
    B2=sq('B')
    W2=pa(sq('Wr'),pm(s2,sq('Wt')))
    H2=pa(sq('A'),ps(pm(s2,B2),2),sq('C'),sq('D'))
    T2=pa(sq('Ar'),ps(pm(s2,sq('Br')),3),ps(sq('Cr'),3),ps(sq('Dr'),3),pm(s2,sq('Tt')),ps(pm(s2,sq('Tp')),3))
    Q=ps(pa(pm(fields['A'],fields['C']),pm(fields['A'],fields['D']),pm(fields['C'],fields['D']),ps(pm(s2,B2),-1)),2)
    residuals=[pa(ps(one,16),ps(W2,-1)),pa(ps(r2,4),ps(H2,-1)),pa(ps(r4,16),ps(T2,-1))]
    return Q,residuals


def frozen_core():
    path=ROOT/'research/expanded_family/radial_control/log-cylinder-caps-core-level-9.json'
    data=json.loads(path.read_text());cutoff=data['core_cutoff']
    verifier=ROOT/'research/expanded_family/radial_control/log_cylinder_caps.py'
    assert data['verifier_sha256']==sha(verifier) and data['interval_primitives_sha256']==sha(PRIMITIVES)
    assert cutoff=={'inner_radius_m':'10','outer_radius_m':'11','transition_coordinate':'r-10',
        'transition_degree':11,'transition_power_coefficients':['1','0','0','0','0','0','-462','1980','-3465','3080','-1386','252'],
        'inside_value':'1','outside_value':'0'}
    upper=F(data['core_energy_upper_J_exact_rational'])
    assert upper==F(data['core_integral']['core_energy_J_interval'][1])
    assert data['core_integral']['core_caps_pass']
    bounds=data['rational_proof']['core_coarse_norm_upper_bounds'];assert len(bounds)==3
    assert all(0<=F(x)<limit for x,limit in zip(bounds,(4,2,4)))
    assert 0<=F(data['rational_proof']['core_cabin_shift_upper'])<=F(1,10**6)
    return upper,path,data


def main():
    ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path)
    ap.add_argument('--tolerance',default='1/5');ap.add_argument('--limit-cells',type=int,default=0)
    ap.add_argument('--caps-only',action='store_true');ap.add_argument('--name');args=ap.parse_args()
    start=time.monotonic();path=args.candidate.resolve();data,kr,km,co=decode(path)
    radial,angular=extraction(kr),extraction(km);total=len(radial)*len(angular)
    greville=[sum(km[j+1:j+7],F(0))/6 for j in range(len(km)-7)]
    for left,right,indices,power in angular:
        reproduced=power@np.array([greville[j] for j in indices],dtype=object)
        assert list(reproduced)==[left,right-left]+[F(0)]*5
    tolerance=F(args.tolerance);assert tolerance>0 and args.limit_cells>=0
    core_upper,core_path,core=frozen_core()
    lower=F(0);upper=F(0);records=[];cap_cells=0;energy_cells=0
    for i,rspan in enumerate(radial):
        for j,mspan in enumerate(angular):
            if args.limit_cells and len(records)>=args.limit_cells:break
            Q,residuals=build_polynomials(rspan,mspan,co)
            caps=[]
            for p in residuals:
                # A zero residual is nonnegative everywhere.
                if not p:ok,info=True,{'cells':1,'deepest':0}
                else:
                    b,d=engine.integer_bernstein(p);ok,info=engine.prove_nonnegative(b,d)
                caps.append({'pass':ok,**info});cap_cells+=info['cells']
            if not all(v['pass'] for v in caps):
                failure={'complete_domain_covered':False,'all_global_caps_pass':False,'candidate_sha256':sha(path),
                    'verifier_sha256':sha(Path(__file__)),'cell':[i,j],'radial_span':list(map(str,rspan[:2])),
                    'angular_span':list(map(str,mspan[:2])),'cap_results':caps}
                (HERE/(path.stem+'-failed.json')).write_text(json.dumps(failure,indent=2)+'\n')
                print(json.dumps(failure),flush=True);raise SystemExit(2)
            record={'radial_span':list(map(str,rspan[:2])),'angular_span':list(map(str,mspan[:2])),'cap_results':caps}
            if not args.caps_only:
                area=(rspan[1]-rspan[0])*(mspan[1]-mspan[0])
                if Q:
                    b,d=engine.integer_bernstein(Q)
                    lo,hi,info=engine.integrate_absolute(b,d,area,tolerance*area/F(178))
                else:lo,hi,info=F(0),F(0),{'cells':1,'deepest':0,'requested_tolerance_met':True}
                lower+=lo;upper+=hi;energy_cells+=info['cells']
                record.update({'polynomial_integral_exact':[str(lo),str(hi)],'energy_subdivision':info})
            records.append(record)
        print(json.dumps({'radial_span':i+1,'cells_completed':len(records),'cells_total':total,
            'elapsed_seconds':time.monotonic()-start,'polynomial_integral_upper':engine.dec(upper)}),flush=True)
        if args.limit_cells and len(records)>=args.limit_cells:break
    complete=len(records)==total
    factor=F(299792458**4,8*F(66743,10**15))
    reference_path=ROOT/'research/deep_strict/validated_math/frozen-interval-level-11.json'
    ref=json.loads(reference_path.read_text());reflo=F(ref['baseline_energy_J_interval'][0])
    incumbent_path=ROOT/'research/expanded_family/angular_search/localized/compact-r100-l13-verified.json'
    incumbent=json.loads(incumbent_path.read_text())
    incumbent_lower=F(incumbent['main_energy_J_interval_outward'][0])
    do_energy=complete and not args.caps_only
    result={'status':'numerical_only','formal_certification':False,
        'evidence_kind':'exact_rational_full_sphere_tensor_spline_Bernstein_enclosure',
        'candidate_path':str(path.relative_to(ROOT)),'candidate_sha256':sha(path),'verifier_sha256':sha(Path(__file__)),
        'frozen_Bernstein_engine_sha256':sha(ENGINE),'span_primitives_sha256':sha(PRIMITIVES),
        'contract_sha256':sha(CONTRACT),'original_benchmark_sha256':sha(BENCHMARK),
        'angular_domain':['-1','1'],'reflection_symmetry_assumed':False,
        'energy_prefactor_exact':str(factor),'polynomial_integrand':'r^2 Q; beta2 is already included in the polynomial Hessian',
        'complete_domain_covered':complete,'all_global_caps_pass':complete,
        'C5_core_exterior_and_angular_matching_pass':True,'exact_original_core_preserved':True,
        'main_and_core_Hessian_supports_disjoint':True,'exterior_exactly_uniform_from_radius_m':'100',
        'core_receipt_sha256':sha(core_path),'core_verifier_sha256':core['verifier_sha256'],
        'core_energy_upper_J_exact':str(core_upper),'reference_receipt_sha256':sha(reference_path),
        'reference_lower_J_exact':str(reflo),
        'frozen_compact_incumbent_receipt_sha256':sha(incumbent_path),
        'frozen_compact_incumbent_lower_J_exact':str(incumbent_lower),
        'strict_energy_improvement_over_frozen_compact_incumbent':factor*upper+core_upper<incumbent_lower if do_energy else None,
        'main_energy_J_interval_outward':[engine.dec(factor*lower,False),engine.dec(factor*upper)] if do_energy else None,
        'total_energy_upper_J_exact':str(factor*upper+core_upper) if do_energy else None,
        'total_energy_upper_J_outward':engine.dec(factor*upper+core_upper) if do_energy else None,
        'guaranteed_reduction_fraction_lower':engine.dec(1-(factor*upper+core_upper)/reflo,False) if do_energy else None,
        'requested_polynomial_integral_tolerance':str(tolerance),'radial_spans':len(radial),'angular_spans':len(angular),
        'base_cells_completed':len(records),'cap_subdivision_cells':cap_cells,'energy_subdivision_cells':energy_cells,
        'cells':records,'elapsed_seconds':time.monotonic()-start,
        'scope':'Ordinary exact rational continuum proof for the complete polynomial main shell, with the frozen outward core enclosure. No Lean or physical-realization claim.'}
    name=args.name or path.stem+('-partial' if not complete else '-verified')
    (HERE/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='cells'},indent=2),flush=True)


if __name__=='__main__':main()
