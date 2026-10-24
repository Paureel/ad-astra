"""Exact rational two-variable Bernstein admission and energy replay.

Every main radial profile is a rational polynomial on each spline span.
The functions r²Q, |W|², r²|H|² and r4|D3Phi|² are exact polynomials
in local radial coordinate and mu. Integer Bernstein subdivision proves
the global caps and brackets the absolute energy without a sampled mesh.
The independently enclosed disjoint core correction is added separately.
"""
from pathlib import Path
from fractions import Fraction as F
from math import comb,factorial,lcm
from decimal import Decimal,localcontext,ROUND_FLOOR,ROUND_CEILING
import argparse,hashlib,heapq,importlib.util,json,time
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
PRIMITIVES=ROOT/'research/radial_extension/interval_verify.py'
spec=importlib.util.spec_from_file_location('span_iv',PRIMITIVES)
iv=importlib.util.module_from_spec(spec);spec.loader.exec_module(iv)


def ua(*ps):
    out=[F(0)]*max(map(len,ps))
    for p in ps:
        for i,v in enumerate(p):out[i]+=v
    while len(out)>1 and out[-1]==0:out.pop()
    return out


def us(p,c):return [v*c for v in p]


def um(p,q):
    out=[F(0)]*(len(p)+len(q)-1)
    for i,a in enumerate(p):
        for j,b in enumerate(q):out[i+j]+=a*b
    return out


def ud(p,scale=F(1)):return [F(i)*v/scale for i,v in enumerate(p) if i] or [F(0)]


def pa(*ps):
    out={}
    for p in ps:
        for k,v in p.items():out[k]=out.get(k,F(0))+v
    return {k:v for k,v in out.items() if v}


def ps(p,c):return {k:v*c for k,v in p.items() if v*c}


def pm(p,q):
    out={}
    for (i,j),a in p.items():
        for (k,l),b in q.items():
            key=i+k,j+l;out[key]=out.get(key,F(0))+a*b
    return {k:v for k,v in out.items() if v}


def outer(r,p,c=F(1)):
    return {(i,j):a*b*c for i,a in enumerate(r) for j,b in enumerate(p) if a*b*c}


def legendre(ell):
    p=[F(0)]*(ell+1)
    for k in range(ell//2+1):
        p[ell-2*k]=F((-1)**k*factorial(2*ell-2*k),2**ell*factorial(k)*factorial(ell-k)*factorial(ell-2*k))
    return p


def span_power(bern):
    n=len(bern)-1
    return [F(comb(n,j))*sum((F((-1)**(j-i)*comb(j,i))*bern[i] for i in range(j+1)),F(0)) for j in range(n+1)]


def build_polynomials(left,right,mode_bern):
    r=[left,right-left];r2=um(r,r);r4=um(r2,r2);width=right-left
    fields={name:{} for name in ['Wr','Wt','A','B','C','D','Ar','Br','Cr','Dr','Tt','Tp']}
    for ell,bern in mode_bern.items():
        h=span_power(bern);hp=ud(h,width);hpp=ud(hp,width);hppp=ud(hpp,width)
        P=legendre(ell);P1=ud(P);P2=ud(P1);P3=ud(P2)
        T=ua(P,um([F(1),F(0),F(-1)],P2),us(um([F(0),F(1)],P1),-1))
        U=ua(P,us(um([F(0),F(1)],P1),-1))
        T1=ua(um([F(1),F(0),F(-1)],P3),us(um([F(0),F(1)],P2),-3))
        rhp=um(r,hp);r2hpp=um(r2,hpp);rhp_h=ua(rhp,us(h,-1))
        contributions={
            'Wr':outer(ua(h,rhp),P,2),'Wt':outer(h,P1,-2),
            'A':outer(um(r,ua(us(hp,2),um(r,hpp))),P,2),
            'B':outer(rhp,P1,-2),
            'C':pa(outer(rhp,P,2),outer(h,T,2)),
            'D':pa(outer(rhp,P,2),outer(h,U,2)),
            'Ar':outer(um(r2,ua(us(hpp,3),um(r,hppp))),P,2),
            'Br':outer(r2hpp,P1,-2),
            'Cr':pa(outer(r2hpp,P,2),outer(rhp_h,T,2)),
            'Dr':pa(outer(r2hpp,P,2),outer(rhp_h,U,2)),
            'Tt':pa(outer(rhp,P1,-6),outer(h,T1,-2)),
            'Tp':pa(outer(rhp,P1,-2),outer(h,um([F(0),F(1)],P2),2))}
        for name,p in contributions.items():fields[name]=pa(fields[name],p)
    sq=lambda name:pm(fields[name],fields[name])
    s2={(0,0):F(1),(0,2):F(-1)}
    W2=pa(sq('Wr'),pm(s2,sq('Wt')))
    H2=pa(sq('A'),ps(pm(s2,sq('B')),2),sq('C'),sq('D'))
    T2=pa(sq('Ar'),ps(pm(s2,sq('Br')),3),ps(sq('Cr'),3),ps(sq('Dr'),3),pm(s2,sq('Tt')),ps(pm(s2,sq('Tp')),3))
    Q=ps(pa(pm(fields['A'],fields['C']),pm(fields['A'],fields['D']),pm(fields['C'],fields['D']),ps(pm(s2,sq('B')),-1)),2)
    residuals=[pa({(0,0):F(16)},ps(W2,-1)),pa(outer(r2,[F(1)],4),ps(H2,-1)),pa(outer(r4,[F(1)],16),ps(T2,-1))]
    assert all(j%2==0 for i,j in Q), 'Only odd potential modes are accepted by this half-sphere replay.'
    assert all(j%2==0 for p in residuals for i,j in p), 'Each cap residual must also be reflection-even.'
    return Q,residuals


def integer_bernstein(poly):
    n=max(i for i,j in poly);m=max(j for i,j in poly)
    power=np.empty((n+1,m+1),dtype=object);power.fill(F(0))
    for (i,j),v in poly.items():power[i,j]=v
    U=np.array([[F(comb(i,k),comb(n,k)) if k<=i else F(0) for k in range(n+1)] for i in range(n+1)],dtype=object)
    V=np.array([[F(comb(j,k),comb(m,k)) if k<=j else F(0) for k in range(m+1)] for j in range(m+1)],dtype=object)
    bern=U@power@V.T
    den=lcm(*(v.denominator for v in bern.ravel()))
    integers=np.array([[v.numerator*(den//v.denominator) for v in row] for row in bern],dtype=object)
    return integers,den


def split_integer(bern,den,axis):
    a=bern if axis==0 else bern.T
    n=a.shape[0]-1;left=np.empty_like(a);right=np.empty_like(a);row=a.copy()
    for k in range(n+1):
        factor=2**(n-k)
        left[k]=row[0]*factor;right[n-k]=row[-1]*factor
        if k<n:row=row[:-1]+row[1:]
    if axis: left,right=left.T,right.T
    return (left,den*2**n),(right,den*2**n)


def select_axis(bern,depth):
    if bern.shape[0]==1:return 1
    if bern.shape[1]==1:return 0
    # Compare coefficient changes per direction; interval sizes are already
    # incorporated by subdivision. This selection affects speed, not validity.
    dr=max(abs(v) for v in (bern[1:]-bern[:-1]).ravel())*(bern.shape[0]-1)
    dm=max(abs(v) for v in (bern[:,1:]-bern[:,:-1]).ravel())*(bern.shape[1]-1)
    return int(dm>dr)


def prove_nonnegative(bern,den,max_depth=24):
    stack=[(bern,den,0)];cells=0;deepest=0
    while stack:
        b,d,depth=stack.pop();cells+=1;deepest=max(deepest,depth)
        if min(b.ravel())>=0:continue
        if min(b[0,0],b[-1,0],b[0,-1],b[-1,-1])<0:
            return False,{'cells':cells,'deepest':deepest,'reason':'Exact negative corner of cap residual.'}
        if depth>=max_depth:return False,{'cells':cells,'deepest':deepest,'reason':'Subdivision depth exhausted.'}
        for bb,dd in split_integer(b,d,select_axis(b,depth)):stack.append((bb,dd,depth+1))
    return True,{'cells':cells,'deepest':deepest}


def integrate_absolute(bern,den,width,tolerance,max_depth=28):
    # Sign-definite cells integrate exactly. Split the largest remaining
    # absolute-integral uncertainty; the stopping comparison is exact rational.
    heap=[];lower=F(0);upper=F(0);cells=0;deepest=0;serial=0;unsplittable=0
    def add_cell(b,d,area,depth):
        nonlocal lower,upper,cells,deepest,serial,unsplittable
        cells+=1;deepest=max(deepest,depth)
        lo=min(b.ravel());hi=max(b.ravel())
        integral=F(sum(b.ravel()),d*b.size)*area
        if lo>=0 or hi<=0:
            lower+=abs(integral);upper+=abs(integral);return
        lb=abs(integral);ub=F(max(abs(lo),abs(hi)),d)*area
        lower+=lb;upper+=ub
        if depth<max_depth:
            serial+=1;heapq.heappush(heap,(-float(ub-lb),serial,b,d,area,lb,ub,depth))
        else:unsplittable+=1
    add_cell(bern,den,F(width),0)
    while upper-lower>tolerance and heap:
        _,_,b,d,area,lb,ub,depth=heapq.heappop(heap)
        lower-=lb;upper-=ub
        for bb,dd in split_integer(b,d,select_axis(b,depth)):add_cell(bb,dd,area/2,depth+1)
    return lower,upper,{'cells':cells,'uncertain_leaves':len(heap)+unsplittable,'deepest':deepest,'requested_tolerance_met':upper-lower<=tolerance}


def dec(value,upper=True):
    with localcontext() as ctx:
        ctx.prec=60;ctx.rounding=ROUND_CEILING if upper else ROUND_FLOOR
        return str(Decimal(value.numerator)/Decimal(value.denominator))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('candidate');ap.add_argument('--tolerance',default='1/10')
    ap.add_argument('--caps-only',action='store_true');ap.add_argument('--name');args=ap.parse_args()
    started=time.monotonic();path=Path(args.candidate);data=json.loads(path.read_text())
    assert data['contract_id']=='rodal-2c-localized-exterior-research'
    contract=ROOT/'research/expanded_family/localized-exterior-contract.json'
    assert data['contract_sha256']==hashlib.sha256(contract.read_bytes()).hexdigest()
    assert data['scenario']=='compact_spherical_exterior'
    assert F(data['outer_radius_m']) in [40,80,100]
    ells=[item['ell'] for item in data['modes']]
    assert ells==sorted(set(ells)) and 1 in ells and all(type(ell) is int and ell>0 and ell%2==1 for ell in ells)
    assert data['core_correction']=='eta(r)*Phi0, eta=1 onr<=10, eta=1-S(r-10) on10<r<11, eta0beyond11; degree11 smootherstepS'
    for item in data['modes']:
        knots=[F(v) for v in item['knots_m']];coef=[F(v) for v in item['coefficients']]
        assert item['degree']==6 and len(knots)==len(coef)+7
        assert knots==sorted(knots) and knots[:7]==[F(11)]*7
        assert knots[-7:]==[F(data['outer_radius_m'])]*7
        assert all(11<v<F(data['outer_radius_m']) for v in knots[7:-7])
        assert all(a<b for a,b in zip(knots[7:-7],knots[8:-7]))
        assert coef[:6]==[F(0)]*6
        assert coef[-6:]==[F(item['ell']==1)]*6
    spans={item['ell']:iv.exact_spans(item) for item in data['modes']}
    first=spans[1];count=len(first);records=[];lower=F(0);upper=F(0)
    full_width=F(data['outer_radius_m'])-11
    for j,(a,b,_) in enumerate(first):
        mode_bern={ell:items[j][2] for ell,items in spans.items()}
        assert all(items[j][:2]==(a,b) for items in spans.values())
        Q,residuals=build_polynomials(a,b,mode_bern)
        caps=[]
        for p in residuals:
            bb,dd=integer_bernstein(p);ok,info=prove_nonnegative(bb,dd);caps.append({'pass':ok,**info})
        if not all(v['pass'] for v in caps):
            print(json.dumps({'failed_span':[str(a),str(b)],'caps':caps}),flush=True)
            raise RuntimeError('A global cap could not be certified.')
        record={'span':[str(a),str(b)],'cap_proofs':caps}
        if not args.caps_only:
            bb,dd=integer_bernstein(Q);lo,hi,info=integrate_absolute(bb,dd,b-a,F(args.tolerance)*(b-a)/full_width)
            lower+=lo;upper+=hi;record.update({'energy_polynomial_integral_exact':[str(lo),str(hi)],'energy_subdivision':info})
        records.append(record)
        print(json.dumps({'span':j+1,'of':count,'elapsed_seconds':time.monotonic()-started,
            'integral_bounds':[dec(lower,False),dec(upper)]}),flush=True)
    factor=F(299792458**4,4*F(66743,10**15))
    core_path=ROOT/'research/expanded_family/radial_control/log-cylinder-caps-core-level-9.json'
    core=json.loads(core_path.read_text());core_upper=F(core['core_energy_upper_J_exact_rational'])
    core_verifier=ROOT/'research/expanded_family/radial_control/log_cylinder_caps.py'
    assert core['verifier_sha256']==hashlib.sha256(core_verifier.read_bytes()).hexdigest()
    assert core['interval_primitives_sha256']==hashlib.sha256(PRIMITIVES.read_bytes()).hexdigest()
    cutoff=core['core_cutoff']
    assert cutoff['inner_radius_m']=='10' and cutoff['outer_radius_m']=='11'
    assert cutoff['transition_coordinate']=='r-10' and cutoff['transition_degree']==11
    assert cutoff['transition_power_coefficients']==['1','0','0','0','0','0','-462','1980','-3465','3080','-1386','252']
    assert cutoff['inside_value']=='1' and cutoff['outside_value']=='0'
    assert core_upper==F(core['core_integral']['core_energy_J_interval'][1])
    assert core['core_integral']['core_caps_pass']
    assert len(core['rational_proof']['core_coarse_norm_upper_bounds'])==3
    assert all(0<=F(v)<lim for v,lim in zip(core['rational_proof']['core_coarse_norm_upper_bounds'],[4,2,4]))
    assert 0<=F(core['rational_proof']['core_cabin_shift_upper'])<F(1,10**6)
    reference_path=ROOT/'research/deep_strict/validated_math/frozen-interval-level-11.json'
    reference=json.loads(reference_path.read_text());reflo=F(reference['baseline_energy_J_interval'][0])
    result={'status':'numerical_only','formal_certification':False,'evidence_kind':'exact_rational_two_variable_Bernstein_continuum_enclosure',
        'candidate_path':str(path),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'span_source_sha256':hashlib.sha256(PRIMITIVES.read_bytes()).hexdigest(),
        'contract_sha256':hashlib.sha256(contract.read_bytes()).hexdigest(),'all_main_global_caps_pass':True,
        'endpoint_C5_matching_verified':True,'exact_core_and_disjoint_support_verified':True,
        'core_cutoff_decoded_as':cutoff,'core_verifier_sha256':core['verifier_sha256'],
        'core_receipt_sha256':hashlib.sha256(core_path.read_bytes()).hexdigest(),'core_energy_upper_J_exact':str(core_upper),
        'main_energy_J_interval_outward':[dec(factor*lower,False),dec(factor*upper)] if not args.caps_only else None,
        'total_energy_upper_J_exact':str(factor*upper+core_upper) if not args.caps_only else None,
        'total_energy_upper_J_outward':dec(factor*upper+core_upper) if not args.caps_only else None,
        'reference_lower_J_exact':str(reflo),'reference_receipt_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        'guaranteed_reduction_fraction_lower':dec(1-(factor*upper+core_upper)/reflo,False) if not args.caps_only else None,
        'requested_total_polynomial_integral_width':args.tolerance,'spans':records,'elapsed_seconds':time.monotonic()-started,
        'scope':'Exact ordinary rational mathematics for polynomial main shell. Entire disjoint core correction separately enclosed; exterior exactly uniform. No formal Lean or physical feasibility claim.'}
    name=args.name or path.stem+'-bernstein'
    (OUT/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='spans'},indent=2),flush=True)


if __name__=='__main__':main()
