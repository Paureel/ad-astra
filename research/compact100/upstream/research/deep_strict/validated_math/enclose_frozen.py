"""Whole-space outward interval enclosure for the unchanged exact v1 candidate.

The selected candidate has only x, x*w, x^3 terms. Its invariant is an even
angular polynomial of degree six. This is a scoped computer-assisted bound,
conditional on the documented continuum reduction, not a Lean certificate.
No benchmark or evaluator files are modified.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,getcontext
from math import comb
import importlib.util,json,hashlib,time,sys
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('radial_interval_primitives',ROOT/'research/radial_extension/interval_verify.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
I=m.I
EXPECTED_CANDIDATE='1aa50dd2e5dd4b9f44fe8e93d3558df0cd6b9c93d990749bed52f687e7cc176d'
EXPECTED_BENCHMARK='52445e98a20de0f2768c6c385ed1fdea80e39351b00eb685690ea358cd44bee9'
CANDIDATE=ROOT/'research/frozen_search/research-optimal.json'
BENCHMARK=ROOT/'benchmarks/rodal-2c-v1.json'
assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()==EXPECTED_CANDIDATE
# The benchmark hash in project receipts is canonical JSON, not file bytes.
benchmark=json.loads(BENCHMARK.read_text())
canonical=json.dumps(benchmark,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
assert hashlib.sha256(canonical).hexdigest()==EXPECTED_BENCHMARK
candidate=json.loads(CANDIDATE.read_text())
co={(x['x_power'],x['transverse_power']):F(x['coefficient']) for x in candidate['coefficients']}
assert set(co)=={(1,0),(1,1),(3,0)}
assert all(abs(x)<=F(1,10) for x in co.values())
a10=I(co[1,0]);a11=I(co[1,1]);a30=I(co[3,0])
CONV=[[F(comb(k,2*j),comb(6,2*j)) if 2*j<=k else F(0) for j in range(4)] for k in range(7)]


def ipow(x,n):
    out=I(1)
    while n:
        if n&1:out=out*x
        x=x*x;n>>=1
    return out


def angular_coefficients(r,gp,gpp):
    s=(r.square()-100)/1500
    t=4*s*(1-s);ts=4-8*s
    b=ipow(t,6)
    bs=6*ipow(t,5)*ts
    bss=30*ipow(t,4)*ts.square()-48*ipow(t,5)
    sr=r/750
    br=bs*sr
    brr=bss*sr.square()+bs/F(750)
    U1=gp+a10*br+a11/F(400)*(2*r*b+r.square()*br)
    U2=gpp+a10*brr+a11/F(400)*(2*b+4*r*br+r.square()*brr)
    vco=(a30-a11)/400
    V=vco*b;V1=vco*br;V2=vco*brr
    a=U1;e=r.square()*V1;c=r*U2-U1;f=ipow(r,3)*V2-r.square()*V1;d=6*r*V
    q0=-2*a.square()
    q1=16*a.square()-12*a*e+4*a*(c+d)+2*d*c
    q2=56*a*e-18*e.square()+4*a*f+4*e*(c+d)+2*d*(f-c)
    q3=48*e.square()+4*e*f-2*d*f
    return [q0,q1,q2,q3]


def split(b):
    rows=[b]
    while len(rows[-1])>1:
        row=rows[-1];rows.append([(u+v)/2 for u,v in zip(row[:-1],row[1:])])
    return [row[0] for row in rows],[row[-1] for row in rows[::-1]]


def integrate_abs_bernstein(b,depth,width=I(1)):
    signed=width*sum(b,I(0))/7
    if all(x.lo>=0 for x in b):return signed
    if all(x.hi<=0 for x in b):return -signed
    if depth==0:
        upper=width*sum((I(x.abs().hi) for x in b),I(0))/7
        return I(signed.abs().lo,upper.hi)
    left,right=split(b)
    return integrate_abs_bernstein(left,depth-1,width/2)+integrate_abs_bernstein(right,depth-1,width/2)


def angular_enclosure(coeff,angular_depth):
    centers=[];error=I(0)
    for j,x in enumerate(coeff):
        c=(x.lo+x.hi)/2
        radius=max(c-x.lo,x.hi-c).next_plus()
        centers.append(I(c));error=error+I(radius)/F(2*j+1)
    bern=[sum((centers[j]*CONV[k][j] for j in range(4)),I(0)) for k in range(7)]
    h=integrate_abs_bernstein(bern,angular_depth)
    return I(max(D(0),(h.lo-error.hi).next_minus()),(h.hi+error.hi).next_plus())


def replay(level=5,angular_depth=10):
    start=time.time();oldbody=I(0);newbody=I(0)
    N=60*(2**level);step=F(30,N)
    for j in range(N):
        left=F(10)+j*step;right=left+step
        r,g,gp,gpp,_=m.baseline_ranges(left,right,third=False)
        old=m.density_integral(r,gp,gpp)
        cc=angular_coefficients(r,gp,gpp)
        new=r.square()*angular_enclosure(cc,angular_depth)
        oldbody=oldbody+step*old;newbody=newbody+step*new
    core=I(0,(m.FACTOR*F(105,10**14)).hi);tail=m.tail_interval()
    old=m.FACTOR*oldbody+core+tail;new=m.FACTOR*newbody+core+tail
    delta=m.FACTOR*(oldbody-newbody)
    reduction=1-new/old
    out={'status':'numerical_only','evidence_kind':'computer_assisted_interval_enclosure','formal_certification':False,
         'benchmark_id':benchmark['id'],'benchmark_canonical_sha256':EXPECTED_BENCHMARK,
         'candidate_sha256':EXPECTED_CANDIDATE,'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'imported_interval_primitives_sha256':hashlib.sha256((ROOT/'research/radial_extension/interval_verify.py').read_bytes()).hexdigest(),
         'radial_cells':N,'radial_level':level,'angular_depth':angular_depth,'precision_decimal_digits':getcontext().prec,
         'baseline_energy_J_interval':old.bounds(),'candidate_energy_J_interval':new.bounds(),
         'improvement_J_interval':delta.bounds(),'reduction_fraction_interval':reduction.bounds(),
         'strict_energy_improvement_established':delta.lo>0,
         'scope':'Frozen candidate and benchmark unchanged. Outward intervals under analytic continuum identities. Global cap proof remains in the existing separate note. No formal GR or Lean certification.',
         'elapsed_seconds':time.time()-start}
    path=Path(__file__).with_name(f'frozen-interval-level-{level}.json');path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2),flush=True)
    return out


if __name__=='__main__':replay(int(sys.argv[1]) if len(sys.argv)>1 else 5,int(sys.argv[2]) if len(sys.argv)>2 else 10)
