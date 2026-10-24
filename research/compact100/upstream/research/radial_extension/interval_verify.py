"""Outward interval replay of the radial proposal, using only Python stdlib.

This is a computer-assisted bound under the documented calculus reduction.
It is NOT a Lean certificate or approval under the frozen v1 decoder.
All spline polynomials are reconstructed exactly from rational JSON data.
Decimal elementary operations are rounded outwards at 50 digits. The usual
Decimal exp/ln/sqrt correctly rounded results are enlarged by one ulp.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D, getcontext, ROUND_FLOOR
from functools import lru_cache
from math import comb,factorial
import json,hashlib,time,sys

getcontext().prec=50
getcontext().rounding=ROUND_FLOOR


class I:
    __slots__=('lo','hi')
    def __init__(self,lo,hi=None):
        if isinstance(lo,I): self.lo,self.hi=lo.lo,lo.hi; return
        if isinstance(lo,F):
            z=D(lo.numerator)/D(lo.denominator)
            self.lo,self.hi=z,z.next_plus(); return
        self.lo=D(lo); self.hi=D(lo if hi is None else hi)
        assert self.lo<=self.hi
    def __add__(self,o):
        o=I(o); return I(self.lo+o.lo,(self.hi+o.hi).next_plus())
    __radd__=__add__
    def __neg__(self): return I(-self.hi,-self.lo)
    def __sub__(self,o): return self+-I(o)
    def __rsub__(self,o): return I(o)+-self
    def __mul__(self,o):
        o=I(o); v=[self.lo*o.lo,self.lo*o.hi,self.hi*o.lo,self.hi*o.hi]
        return I(min(v),max(v).next_plus())
    __rmul__=__mul__
    def __truediv__(self,o):
        o=I(o)
        if o.lo<=0<=o.hi: raise ZeroDivisionError('Interval crosses zero')
        return self*I(D(1)/o.hi,(D(1)/o.lo).next_plus())
    def __rtruediv__(self,o): return I(o)/self
    def square(self):
        v=[self.lo*self.lo,self.hi*self.hi]
        return I(0 if self.lo<=0<=self.hi else min(v),max(v).next_plus())
    def sqrt(self):
        assert self.lo>=0
        return I(max(D(0),self.lo.sqrt().next_minus()),self.hi.sqrt().next_plus())
    def exp(self):return I(self.lo.exp().next_minus(),self.hi.exp().next_plus())
    def ln(self):
        assert self.lo>0
        return I(self.lo.ln().next_minus(),self.hi.ln().next_plus())
    def abs(self):
        return I(0 if self.lo<=0<=self.hi else min(abs(self.lo),abs(self.hi)),max(abs(self.lo),abs(self.hi)))
    def bounds(self):return [str(self.lo),str(self.hi)]


TANH20=(1-(-I(40)).exp())/(1+(-I(40)).exp())
COSH40=(I(40).exp()+(-I(40)).exp())/2
FACTOR=I(F(299792458**4*4*10**15,4*66743))


def tanh(x):
    u=(2*x).exp(); return (u-1)/(u+1)


def sech2(x):
    y=x.abs(); u=(-2*y).exp(); return 4*u/(1+u).square()


@lru_cache(maxsize=None)
def point_profile(r):
    r=I(r)
    ch=((2*r).exp()+(-2*r).exp())/2
    f=(ch-1)/(COSH40+ch)
    def lc(z):
        z=z.abs(); return z+(1+(-2*z).exp()).ln()
    g=1-(lc(r+20)-lc(r-20))/(2*r*TANH20)
    return f,g


def baseline_ranges(left,right,third=True):
    r=I(F(left),None) if left==right else I(I(left).lo,I(right).hi)
    fl,gl=point_profile(left); fr,gr=point_profile(right)
    # f and its radial average g are monotone for r>=0.
    f=I(fl.lo,fr.hi); g=I(gl.lo,gr.hi)
    # sech2 is decreasing as |x| increases. Using its interval expression
    # remains conservative even when the interval contains the peak at zero.
    fp=(sech2(r-20)-sech2(r+20))/(2*TANH20)
    a=(f-g)/r
    b=(fp-2*a)/r
    if third:
        fpp=(sech2(r+20)*tanh(r+20)-sech2(r-20)*tanh(r-20))/TANH20
        c=fpp/r-3*fp/r.square()+6*a/r.square()
    else:c=I(0)
    return r,g,a,b,c


def poly_add(a,b):
    return [(a[i] if i<len(a) else F(0))+(b[i] if i<len(b) else F(0)) for i in range(max(len(a),len(b)))]


def poly_linear(a,u,v):
    out=[F(0)]*(len(a)+1)
    for j,c in enumerate(a):out[j]+=c*u; out[j+1]+=c*v
    return out


def exact_spans(data):
    knots=[F(x) for x in data['knots_m']]
    coeff=[F(x) for x in data['coefficients']]
    degree=data['degree']; out=[]
    for span in range(degree,len(coeff)):
        left,right=knots[span],knots[span+1]
        if left==right:continue
        width=right-left
        @lru_cache(None)
        def basis(i,d):
            if d==0:return (F(int(i==span)),)
            val=[F(0)]
            den=knots[i+d]-knots[i]
            if den:val=poly_add(val,poly_linear(basis(i,d-1),(left-knots[i])/den,width/den))
            den=knots[i+d+1]-knots[i+1]
            if den:val=poly_add(val,poly_linear(basis(i+1,d-1),(knots[i+d+1]-left)/den,-width/den))
            return tuple(val)
        power=[F(0)]*(degree+1)
        for i in range(max(0,span-degree),min(len(coeff),span+1)):
            for j,v in enumerate(basis(i,degree)):power[j]+=coeff[i]*v
        bern=[sum((power[j]*F(comb(k,j),comb(degree,j)) for j in range(k+1)),F(0)) for k in range(degree+1)]
        out.append((left,right,bern))
    return out


def split_bern(b):
    rows=[b]
    while len(rows[-1])>1:
        row=rows[-1]; rows.append([(u+v)/2 for u,v in zip(row[:-1],row[1:])])
    return [row[0] for row in rows],[row[-1] for row in rows[::-1]]


def cells(left,right,bern,level):
    if level==0:yield left,right,bern; return
    a,b=split_bern(bern); m=(left+right)/2
    yield from cells(left,m,a,level-1)
    yield from cells(m,right,b,level-1)


def spline_ranges(bern,width):
    out=[]; b=bern
    for j in range(4):
        out.append(I(I(min(b)).lo,I(max(b)).hi))
        n=len(b)-1
        if n:b=[F(n)*(v-u)/width for u,v in zip(b[:-1],b[1:])]
    return out


def angular_interval(p,q):
    # H is globally 1/3-Lipschitz in p and 1-Lipschitz in q because
    # H(p,q)=integral_0^1 |p mu^2-q| dmu.
    pm=(p.lo+p.hi)/2; qm=(q.lo+q.hi)/2
    pc,qc=I(pm),I(qm)
    if pm<=qm:hc=qc-pc/3
    else:hc=pc/3-qc+F(4,3)*qc*(qc/pc).sqrt()
    ep=max(pm-p.lo,p.hi-pm).next_plus()
    eq=max(qm-q.lo,q.hi-qm).next_plus()
    er=(I(ep)/3+I(eq)).hi
    return I(max(D(0),(hc.lo-er).next_minus()),(hc.hi+er).next_plus())


def density_integral(r,a,b):
    aa=a.square()
    p=12*aa+4*r*a*b; q=2*aa
    return r.square()*angular_interval(p,q)


def tail_interval():
    C=20/TANH20; k=1/TANH20; L=I(40)
    lead=FACTOR*F(2,3)*C.square()/L*(2*I(2).sqrt()-1)
    rem=FACTOR*C*k*(-I(40)).exp()*(F(4,3)+F(20,3)/(2*L)+F(20,3)/(4*L.square()))
    return I((lead.lo-rem.hi).next_minus(),(lead.hi+rem.hi).next_plus())


def replay(level):
    start=time.time(); path=Path(__file__).with_name('candidate-radial-extension.json')
    data=json.loads(path.read_text()); spans=exact_spans(data)
    base_integral=I(0); new_integral=I(0); maxima=[D(0)]*3
    count=0
    for left,right,bern in spans:
        for a,b,bs in cells(left,right,bern,level):
            r,g,gp,gpp,gppp=baseline_ranges(a,b)
            dg,da,db,dc=spline_ranges(bs,b-a)
            ng,na,nb,nc=g+dg,gp+da,gpp+db,gppp+dc
            base_integral=base_integral+(b-a)*density_integral(r,gp,gpp)
            new_integral=new_integral+(b-a)*density_integral(r,na,nb)
            w=2*max(ng.abs().hi,(ng+r*na).abs().hi)
            jac=2*(2*na.square()+(2*na+r*nb).square()).sqrt().hi
            axis=(3*nb+r*nc).square()+6*nb.square()
            eq=3*nb.square()+12*(na/r).square()
            third=2*max(axis.sqrt().hi,eq.sqrt().hi)
            maxima=[max(x,y.next_plus()) for x,y in zip(maxima,[w,jac,third])]
            count+=1
    # On [0,10], f' <3e-8 and g' <=(max f')/2 give
    # H<=6(g')^2+4g'f'. Integral r^2 dr=1000/3.
    # exp(20)>1e8 is checked by exact finite Taylor arithmetic below.
    assert sum((F(20)**j/F(factorial(j)) for j in range(31)),F(0))>10**8
    core=I(0,(FACTOR*F(105,10**14)).hi)
    tail=tail_interval()
    old=FACTOR*base_integral+core+tail
    new=FACTOR*new_integral+core+tail
    reduction=1-new/old
    results={'status':'numerical_only','evidence_kind':'computer_assisted_interval_enclosure','formal_certification':False,'v1_admissible':False,
        'precision_decimal_digits':getcontext().prec,'subdivision_level':level,'radial_cells':count,
        'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'baseline_energy_J_interval':old.bounds(),'candidate_energy_J_interval':new.bounds(),
        'reduction_fraction_interval':reduction.bounds(),'whole_space_tail_J_interval':tail.bounds(),
        'shell_global_norm_upper_bounds':[str(x) for x in maxima],
        'global_caps_pass':all(v<=D(cap) for v,cap in zip(maxima,[4,2,4])),
        'analytic_core_energy_upper_J':str(core.hi),
        'analytic_core_norm_upper_bounds':['0.00000002','0.0000001','0.000001'],
        'analytic_exterior_norm_upper_bounds':['2','0.04','0.004'],
        'scope':'Exact rational spline reconstruction; outward Decimal ranges; analytic angular integral with Lipschitz enclosure; fixed exterior tail remainder. Conditional on documented continuum identities and Decimal arithmetic implementation. Not a Lean certificate, a formal GR bridge, or material realizability.',
        'elapsed_seconds':time.time()-start}
    out=Path(__file__).with_name(f'interval-level-{level}.json');out.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2),flush=True)
    return results


if __name__=='__main__':replay(int(sys.argv[1]) if len(sys.argv)>1 else 5)
