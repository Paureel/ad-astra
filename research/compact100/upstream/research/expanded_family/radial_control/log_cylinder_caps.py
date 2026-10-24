"""Exact global-cap bounds and an outward core energy integral.

Main potential: Phi=2[x-f(x)G(rho)], with the frozen 12/24/36/48 axial
profile and G=1-S(log(rho/12)/T), T>=10. S'=2772 t^5(1-t)^5.
Core correction: eta(r)*Phi0, eta=1 for r<=10, eta=1-S(r-10) on
10<r<11, eta=0 for r>=11. The main potential vanishes throughout
the support of this correction. All proof bounds below are exact rational
arithmetic or outward Decimal intervals. No formal certification is claimed.
"""
from pathlib import Path
from fractions import Fraction as F
from math import factorial
from decimal import Decimal as D
import importlib.util
import json,hashlib,time,sys

OUT=Path(__file__).parent
ROOT=OUT.parents[2]
PRIMITIVES=ROOT/'research/radial_extension/interval_verify.py'
spec=importlib.util.spec_from_file_location('core_iv',PRIMITIVES)
iv=importlib.util.module_from_spec(spec);spec.loader.exec_module(iv)
I=iv.I
CONTRACT=ROOT/'research/expanded_family/free-exterior-contract.json'
CANDIDATE=ROOT/'research/expanded_family/angular_search/log-cylinder-candidate.json'
CONTRACT_HASH='c5ceac307000cb0f332a737347dec8bd2f3af5c3872e2f120ca97e57b78cdbb3'
CANDIDATE_HASH='91a48a8337b6b4139119b959995b47ee4a706df999614b28f94cb797c18509c8'


def verify_data_binding():
    assert hashlib.sha256(CONTRACT.read_bytes()).hexdigest()==CONTRACT_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()==CANDIDATE_HASH
    data=json.loads(CANDIDATE.read_text())
    assert data['contract']=='rodal-2c-free-exterior-research'
    assert data['contract_sha256']==CONTRACT_HASH
    assert data['speed_c']=='2' and data['inner_cylinder_radius_m']=='12'
    assert data['axial_positive_breaks_m']==['0','12','24','36','48']
    assert data['axial_parity']=='odd' and F(data['logarithmic_extent_T'])>=10
    S=[F(v) for v in data['smootherstep_power_coefficients']]
    assert S==[F(0)]*6+list(map(F,[462,-1980,3465,-3080,1386,-252]))
    primitive=[F(0)]+[v/F(j+1) for j,v in enumerate(S)]
    first=[F(12),F(12)]+[F(0)]*11
    last=[F(9,2),F(-9)]+[F(0)]*11
    for j,v in enumerate(primitive):first[j]-=21*v;last[j]+=9*v
    expected=[[F(0),F(12)],first,[F(27,2),F(-9)],last]
    assert [[F(v) for v in row] for row in data['axial_piece_coefficients_in_local_t']]==expected
    assert data['core_correction']=='Phi_core=eta(r)*Phi0(r,x); eta=1 for r<=10; eta=1-S(r-10) for 10<r<11; eta=0 for r>=11'
    return {'inner_radius_m':'10','outer_radius_m':'11',
        'transition_coordinate':'r-10','transition_degree':11,
        'transition_power_coefficients':[str(F(int(j==0))-v) for j,v in enumerate(S)],
        'inside_value':'1','outside_value':'0'}


def rational_bounds():
    # u=t(1-t)<=1/4. S'''=55440*u^3*(1-(9/2)*u), whose final
    # factor lies in [-1/8,1], so absolute value is at most one.
    S1=F(2772,4**5)
    S2=F(13860,4**4)
    S3=F(55440,4**3)
    f0=F(24);f1=F(1);f2=F(7,48)*S1;f3=F(7,576)*S2
    a=F(12);T=F(10)
    g1=S1/(T*a)
    g1_rho=S1/(T*a*a)
    g2=(S1/T+S2/T**2)/a**2
    g3=(2*S1/T+3*S2/T**2+S3/T**3)/a**3
    gm=(2*S1/T+S2/T**2)/a**3
    shift2=4*(F(7,4)**2+f0*f0*g1*g1)
    jac2=4*(f2*f2+2*f1*f1*g1*g1+f0*f0*(g2*g2+g1_rho*g1_rho))
    third2=4*(f3*f3+3*f2*f2*g1*g1+3*f1*f1*(g2*g2+g1_rho*g1_rho)
               +f0*f0*(g3*g3+3*gm*gm))
    assert shift2<16 and jac2<4 and third2<16
    # Exponential inequalities used for the exact-core fallback bound.
    thresholds=[(18,50_000_000),(20,100_000_000),(38,10**16),(40,10**17)]
    taylor=[]
    for x,bound in thresholds:
        partial=sum((F(x)**n/F(factorial(n)) for n in range(101)),F(0))
        assert partial>bound
        taylor.append({'argument':x,'lower_threshold':str(bound),'degree':100,
                       'exact_partial_sum':str(partial)})
    tanh_lower=F(999,1000)
    assert F(10**17-1,10**17+1)>tanh_lower
    # Independent uniform baseline bounds on the closed cabin, including r=0.
    # g^(n)(r)=integral_0^1 t^n f^(n)(rt)dt; also f'(0)=0.
    M1=F(3,10**8);M2=F(1,10**7);M3=F(2,10**7)
    assert 2*F(1,10**8)/tanh_lower<M1
    assert 8*F(1,10**8)/tanh_lower<M2
    assert 16*F(1,10**8)/tanh_lower<M3
    assert 4*(2*(M1/2)**2+M1**2)<F(1,10**7)**2
    cabin_t3_axis=4*((M2+10*M3/4)**2+6*(M2/3)**2)
    cabin_t3_equator=4*(15*(M2/3)**2)
    assert max(cabin_t3_axis,cabin_t3_equator)<F(2,10**6)**2
    tiny_M1=F(3,10**16);tiny_M2=F(1,10**15);tiny_M3=F(2,10**15)
    assert 2*F(1,10**16)/tanh_lower<tiny_M1
    assert 8*F(1,10**16)/tanh_lower<tiny_M2
    assert 16*F(1,10**16)/tanh_lower<tiny_M3
    assert 4*(2*(tiny_M1/2)**2+tiny_M1**2)<F(1,10**15)**2
    assert 4*((tiny_M2+tiny_M3/4)**2+6*(tiny_M2/3)**2)<F(2,10**14)**2
    assert 4*15*(tiny_M2/3)**2<F(2,10**14)**2
    # On 10<=r<=11: f0<=e^-18, g0<=f0 and a=(f0-g0)/r.
    f=F(1,50_000_000);gp=f/10
    fp=F(5,10**8);fpp=F(1,10**7)
    assert 2*f/tanh_lower<fp
    assert 4*(f+F(1,10**17))/tanh_lower<fpp
    gpp=(fp+2*gp)/10
    gppp=fpp/10+3*fp/100+6*gp/100
    phi=22*f;grad=2*(f+11*gp)
    hess2=4*(2*gp**2+(2*gp+11*gpp)**2)
    hess=F(13,10**8);assert hess2<hess*hess
    t3axis=4*((3*gpp+11*gppp)**2+6*gpp*gpp)
    t3eq=4*(3*gpp*gpp+12*(gp/10)**2)
    third=F(3,10**7);assert max(t3axis,t3eq)<third*third
    eta1=F(2708,1000);eta2=F(55);eta3=F(867)
    assert S1<eta1
    assert S2*S2+2*(S1/10)**2<eta2*eta2
    assert S3*S3+6*(S2/10+S1/100)**2<eta3*eta3
    cw=grad+phi*eta1
    ck=hess+2*eta1*grad+phi*eta2
    ct=third+3*eta1*hess+3*eta2*grad+phi*eta3
    assert cw<F(13,10**7) and ck<F(25,10**6) and ct<F(4,10**4)
    # On r<=10, the unchanged baseline has shift<2e-8, Hessian<1e-7,
    # and third tensor<2e-6 from its integral representation g=integral f(rt)dt.
    # These are smaller than the correction-shell bounds above.
    coarse_energy=F(299792458**4*10**15,66743)*F(11**3,3)*F(25,10**6)**2
    return {'smoothstep_derivative_bounds':[str(v) for v in (S1,S2,S3)],
        'axial_absolute_bounds':[str(v) for v in (f0,f1,f2,f3)],
        'main_squared_norm_upper_bounds':[str(v) for v in (shift2,jac2,third2)],
        'main_norm_upper_bounds':[I(v).sqrt().bounds()[1] for v in (shift2,jac2,third2)],
        'main_global_caps_pass':True,
        'uniform_parameter_range':'Every finite real T>=10',
        'core_coarse_norm_upper_bounds':[str(v) for v in (F(13,10**7),F(25,10**6),F(4,10**4))],
        'core_coarse_energy_upper_J_exact_rational':str(coarse_energy),
        'exponential_taylor_checks':taylor,
        'core_cabin_shift_upper':'1/50000000'}


def core_integral(level):
    value=I(0);maxima=[D(0)]*3;count=0
    def accumulate(lo,hi,eta):
        nonlocal value,count,maxima
        r,g,a,b,c=iv.baseline_ranges(lo,hi)
        if eta is not None:
            e,e1,e2,e3=iv.spline_ranges(eta,hi-lo)
            g,a,b,c=(e*g,e*a+e1*g,e*b+2*e1*a+e2*g,
                     e*c+3*e1*b+3*e2*a+e3*g)
        value=value+(hi-lo)*iv.density_integral(r,a,b)
        w=2*max(g.abs().hi,(g+r*a).abs().hi)
        h=2*(2*a.square()+(2*a+r*b).square()).sqrt().hi
        t=2*max(((3*b+r*c).square()+6*b.square()).sqrt().hi,
                (3*b.square()+12*(a/r).square()).sqrt().hi)
        maxima=[max(old,new.next_plus()) for old,new in zip(maxima,(w,h,t))]
        count+=1
    sub=2**level
    for integer in range(1,10):
        for j in range(sub):
            lo=F(integer)+F(j,sub);hi=lo+F(1,sub)
            accumulate(lo,hi,None)
    # Degree11 eta Bernstein coefficients on the exact interval [10,11].
    eta=[F(1)]*6+[F(0)]*6
    for lo,hi,bern in iv.cells(F(10),F(11),eta,level):
        accumulate(lo,hi,bern)
    # For 0<=r<=1, exp(38)>10^16 gives f'<3e-16 and g'<1.5e-16.
    # H<=6(g')^2+4g'f' and integral r^2 dr=1/3.
    small_ball=I(0,(iv.FACTOR*F(105,10**33)).hi)
    energy=iv.FACTOR*value+small_ball
    # The excluded tiny ball also has explicit norm bounds, much smaller than
    # the interval maxima on [1,11]. They close the global-cap coverage.
    tiny_norms=list(map(D,('2e-16','1e-15','2e-14')))
    maxima=[max(a,b) for a,b in zip(maxima,tiny_norms)]
    return {'radial_level':level,'radial_cells':count,
        'core_energy_J_interval':energy.bounds(),
        'tiny_ball_r_le_1_energy_upper_J':str(small_ball.hi),
        'tiny_ball_r_le_1_norm_upper_bounds':[str(v) for v in tiny_norms],
        'core_interval_norm_upper_bounds':[str(v) for v in maxima],
        'core_caps_pass':all(v<D(cap) for v,cap in zip(maxima,(4,2,4))),
        'whole_space_core_correction':'eta(r)*Phi0, eta=1 on r<=10, eta=1-S(r-10) on10<r<11, eta=0 on r>=11'}


def main(level=9):
    started=time.monotonic()
    cutoff=verify_data_binding()
    result={'status':'numerical_only','formal_certification':False,
        'evidence_kind':'exact_rational_global_caps_and_outward_core_energy_enclosure',
        'contract_id':'rodal-2c-free-exterior-research',
        'contract_sha256':CONTRACT_HASH,
        'candidate_sha256':CANDIDATE_HASH,
        'candidate_binding_scope':'Frozen axial, transverse and core profiles, with main caps proved uniformly for every finite real T>=10; base data instance T=1000. Other exact T instances are bound separately by the energy receipt.',
        'core_cutoff':cutoff,
        'main_profile':'f=x on|x|<=12; positive-side transitions12..24 and36..48 with degree11 smootherstep, slope-3/4 on24..36; f odd, zero outside48',
        'transverse_profile':'G=1 belowrho12; G=1-S(log(rho/12)/T) untilrho12exp(T); zero beyond; every finiteT>=10',
        'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'interval_primitives_sha256':hashlib.sha256(PRIMITIVES.read_bytes()).hexdigest(),
        'rational_proof':rational_bounds(),
        'core_integral':core_integral(level),
        'disjoint_support_argument':'The main potential is identically zero on the open cylinder |x|<12,rho<12. The core correction is supported in the closed ball r<=11, strictly inside that cylinder. Thus the two Hessians have disjoint supports and their absolute source energies add exactly.',
        'regularity':'S and its first five derivatives match the constant endpoint values; the axial f is C6 and transverse G is C5. The core cutoff is C5 and equals the original baseline onr<=10. Therefore the total potential is C5 and metric C4.',
        'finite_energy':'For each finiteT, the main Hessian has compact support in |x|<=48,rho<=12exp(T). The correction has compact support inr<=11. The metric is exactly asymptotically Minkowski in laboratory coordinates.',
        'scope':'Ordinary computer-assisted mathematics under the benchmark GR identity and reviewed Decimal implementation. No formal Lean certification or physical realization claim.',
        'elapsed_seconds':time.monotonic()-started}
    # Capture elapsed time after the computation, rather than before evaluation.
    result['elapsed_seconds']=time.monotonic()-started
    result['core_energy_upper_J_exact_rational']=str(F(D(result['core_integral']['core_energy_J_interval'][1])))
    path=OUT/f'log-cylinder-caps-core-level-{level}.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('evidence_kind','rational_proof','core_integral','elapsed_seconds')},indent=2),flush=True)


if __name__=='__main__':main(int(sys.argv[1]) if len(sys.argv)>1 else 9)
