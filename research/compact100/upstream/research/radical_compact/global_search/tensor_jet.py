"""Data-only decoder and full spherical 3-jet for the tensor spline family.

Rows of C index degree6 angular B-splines A_j(mu), columns index degree6
radial B-splines B_i(r), and Phi_main=2*r*sum(C[j,i]*A_j(mu)*B_i(r)).
The numerical API covers r>=11. The separate eta*Phi0 core correction applies
below11 and restores the original potential exactly below10.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib,itertools,json
import numpy as np
from scipy.interpolate import BSpline

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]


def decode(path):
    data=json.loads(Path(path).read_text())
    assert data['representation']=='tensor_product_radial_angular_bspline'
    assert data['contract_id']=='rodal-2c-localized-exterior-research'
    contract=ROOT/'research/expanded_family/localized-exterior-contract.json'
    assert data['contract_sha256']==hashlib.sha256(contract.read_bytes()).hexdigest()
    assert data['scenario']=='compact_spherical_exterior' and F(data['outer_radius_m'])==100
    assert type(data['radial_degree']) is int and data['radial_degree']==6
    assert type(data['angular_degree']) is int and data['angular_degree']==6
    rk=[F(v) for v in data['radial_knots_m']];ak=[F(v) for v in data['angular_knots']]
    for knots,lower,upper in [(rk,F(11),F(100)),(ak,F(-1),F(1))]:
        assert knots[:7]==[lower]*7 and knots[-7:]==[upper]*7
        assert all(lower<v<upper for v in knots[7:-7])
        assert all(a<b for a,b in zip(knots[7:-7],knots[8:-7]))
    nr=len(rk)-7;na=len(ak)-7;C=[[F(v) for v in row] for row in data['coefficients']]
    assert len(C)==na and all(len(row)==nr for row in C)
    greville=[sum(ak[j+1:j+7],F(0))/6 for j in range(na)]
    assert all(row[:6]==[F(0)]*6 and row[-6:]==[greville[j]]*6 for j,row in enumerate(C))
    assert data['core_correction']=='eta(r)*Phi0, eta=1 onr<=10, eta=1-S(r-10) on10<r<11, eta0beyond11; degree11 smootherstepS'
    return data,rk,ak,C


class TensorPotential:
    def __init__(self,path):
        self.path=Path(path);self.data,rk,ak,C=decode(path)
        self.C=np.array(C,dtype=float)
        self.radial=BSpline(np.array(rk,dtype=float),np.eye(len(rk)-7),6,extrapolate=False)
        self.angular=BSpline(np.array(ak,dtype=float),np.eye(len(ak)-7),6,extrapolate=False)
        self.radial_edges=sorted(set(rk));self.angular_edges=sorted(set(ak))

    def spherical_jet(self,r,mu):
        r=np.asarray(r,dtype=float);mu=np.asarray(mu,dtype=float)
        assert r.ndim==mu.ndim==1 and np.all(r>=11) and np.all(np.abs(mu)<=1)
        shape=(len(r),len(mu));body=r<100
        angular=[self.angular(mu,k) for k in range(4)]
        radial=[self.radial(r[body],k)@self.C.T for k in range(4)]
        h={}
        for i in range(4):
            for j in range(4-i):
                value=np.zeros(shape);value[body]=radial[i]@angular[j].T
                if i==0 and j==0:value[~body]=mu
                if i==0 and j==1:value[~body]=1
                h[i,j]=value
        rr=r[:,None];u=mu[None,:];s=np.sqrt(1-u*u);s2=1-u*u
        f=h[0,0];fr=h[1,0];fm=h[0,1];frr=h[2,0];frm=h[1,1];fmm=h[0,2]
        Wr=2*(f+rr*fr);Wt=-2*s*fm
        A=2*(2*fr+rr*frr);B=-2*s*frm
        C=2*(fr+(f+s2*fmm-u*fm)/rr);D=2*(fr+(f-u*fm)/rr)
        Ar=2*(3*frr+rr*h[3,0]);Br=-2*s*h[2,1]
        Cr=2*(frr+fr/rr-f/rr**2+s2*(h[1,2]/rr-fmm/rr**2)-u*(frm/rr-fm/rr**2))
        Dr=2*(frr+fr/rr-f/rr**2-u*(frm/rr-fm/rr**2))
        Tt=-2*s/rr*(3*frm+(s2*h[0,3]-3*u*fmm)/rr)
        Tp=-2*s/rr*(frm-u*fmm/rr)
        W=np.zeros(shape+(3,));H=np.zeros(shape+(3,3));T=np.zeros(shape+(3,3,3))
        W[...,0]=Wr;W[...,1]=Wt
        H[...,0,0]=A;H[...,0,1]=H[...,1,0]=B;H[...,1,1]=C;H[...,2,2]=D
        for indices,value in [((0,0,0),Ar),((0,0,1),Br),((0,1,1),Cr),((0,2,2),Dr),((1,1,1),Tt),((1,2,2),Tp)]:
            for perm in set(itertools.permutations(indices)):T[(...,)+perm]=value
        H[~body]=0;T[~body]=0
        return {'W':W,'H':H,'T':T,'r':r,'mu':mu,'frame':'Orthonormal(e_r,e_theta,e_phi), polar axis+x',
                'scope':'Main shell and exact uniform exterior, r>=11; separate compact core correction below11.'}

    def cartesian_jet(self,r,mu):
        jet=self.spherical_jet(r,mu);mu=jet['mu'];s=np.sqrt(1-mu*mu)
        rotation=np.zeros((len(mu),3,3));rotation[:,0,0]=mu;rotation[:,1,0]=s
        rotation[:,0,1]=-s;rotation[:,1,1]=mu;rotation[:,2,2]=1
        return {'W':np.einsum('mia,rma->rmi',rotation,jet['W']),
                'H':np.einsum('mia,mjb,rmab->rmij',rotation,rotation,jet['H']),
                'T':np.einsum('mia,mjb,mkc,rmabc->rmijk',rotation,rotation,rotation,jet['T']),
                'r':jet['r'],'mu':mu,'points':'(x,y,z)=(r*mu,r*sqrt(1-mu²),0)','scope':jet['scope']}
