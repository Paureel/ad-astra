"""Exact-rational point checks, NOT a formal GR proof.

Independent 4D Christoffel/Ricci evaluation for polynomial scalar potentials.
The samples are algebra fixtures, not admissible warp-drive candidates.
Run from the repository root with:
    python formal/diagnostics/direct_ricci_check.py
"""

from fractions import Fraction as F
from itertools import product
N=4; Z=F(0); O=F(1)
class J:
 def __init__(self,v,g=None,h=None):
  self.v=F(v);self.g=g or [Z]*N;self.h=h or [[Z]*N for _ in range(N)]
 def __add__(self,b):
  b=b if isinstance(b,J) else J(b)
  return J(self.v+b.v,[self.g[i]+b.g[i] for i in range(N)],[[self.h[i][j]+b.h[i][j] for j in range(N)] for i in range(N)])
 __radd__=__add__
 def __neg__(self): return self*(-1)
 def __sub__(self,b): return self+(-b if isinstance(b,J) else -F(b))
 def __rsub__(self,b): return -self+b
 def __mul__(self,b):
  b=b if isinstance(b,J) else J(b)
  return J(self.v*b.v,[self.g[i]*b.v+self.v*b.g[i] for i in range(N)],[[self.h[i][j]*b.v+self.g[i]*b.g[j]+self.g[j]*b.g[i]+self.v*b.h[i][j] for j in range(N)] for i in range(N)])
 __rmul__=__mul__
 def __truediv__(self,b):return self*F(1,b)
 def __pow__(self,n):
  ans=J(1)
  for _ in range(n):ans=ans*self
  return ans

def matmul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(N)) for j in range(N)] for i in range(N)]

def run(label, point, angular=False):
 b=F(2); xyz=list(map(F,point))
 coords=[J(xyz[i],[Z]+[F(i==j) for j in range(3)]) for i in range(3)]
 x,y,z=coords;r2=x*x+y*y+z*z
 g=F(1,10)+r2/17+(r2*r2)/31
 h=F(2,17)+F(4,31)*r2
 W=[b*((g if i==0 else J(0))+x*h*coords[i]) for i in range(3)]
 if angular:
  eta=F(1,101)
  W=[W[0]+b*eta*2*x*(y*y+z*z), W[1]+b*eta*2*x*x*y, W[2]+b*eta*2*x*x*z]
 g4=[[J(F(i==j)) for j in range(N)] for i in range(N)]
 g4[0][0]=-1+sum(w*w for w in W)
 for i in range(3):g4[0][i+1]=g4[i+1][0]=W[i]
 gv=[[g4[i][j].v for j in range(N)] for i in range(N)]
 inv=[[Z for j in range(N)] for i in range(N)]
 inv[0][0]=-O
 for i in range(3):
  inv[0][i+1]=inv[i+1][0]=W[i].v
  for j in range(3):inv[i+1][j+1]=F(i==j)-W[i].v*W[j].v
 assert matmul(inv,gv)==[[F(i==j) for j in range(N)] for i in range(N)]
 d=[[[g4[i][j].g[e] for j in range(N)] for i in range(N)] for e in range(N)]
 dd=[[[[g4[i][j].h[e][h] for j in range(N)] for i in range(N)] for h in range(N)] for e in range(N)]
 di=[]
 for e in range(N):
  mm=matmul(matmul(inv,d[e]),inv);di.append([[-v for v in row] for row in mm])
 Gam={};dGam={}
 for a,j,k in product(range(N),repeat=3):
  Gam[a,j,k]=sum(inv[a][h]*(d[j][h][k]+d[k][h][j]-d[h][j][k])/2 for h in range(N))
  for e in range(N):
   dGam[e,a,j,k]=sum((di[e][a][h]*(d[j][h][k]+d[k][h][j]-d[h][j][k])+inv[a][h]*(dd[e][j][h][k]+dd[e][k][h][j]-dd[e][h][j][k]))/2 for h in range(N))
 Ric=[[Z]*N for _ in range(N)]
 for a,j in product(range(N),repeat=2):
  Ric[a][j]=sum(dGam[k,k,a,j]-dGam[j,k,a,k] for k in range(N))+sum(Gam[k,k,h]*Gam[h,a,j]-Gam[k,j,h]*Gam[h,a,k] for k,h in product(range(N),repeat=2))
 assert all(Ric[i][j]==Ric[j][i] for i,j in product(range(N),repeat=2))
 scalar=sum(inv[a][j]*Ric[a][j] for a,j in product(range(N),repeat=2))
 n=[O]+[-w.v for w in W]
 gnn=sum(gv[i][j]*n[i]*n[j] for i,j in product(range(N),repeat=2));assert gnn==-1
 Gnn=sum(Ric[i][j]*n[i]*n[j] for i,j in product(range(N),repeat=2))-scalar*gnn/2
 K=[[W[i].g[j+1] for j in range(3)] for i in range(3)]
 invariant=sum(K[i][i] for i in range(3))**2-sum(K[i][j]*K[j][i] for i,j in product(range(3),repeat=2))
 from math import isqrt
 r2v=sum(v*v for v in xyz);r=F(isqrt(r2v.numerator),isqrt(r2v.denominator));assert r*r==r2v
 a=2*r/17+4*r**3/31;bg=2*r/17+12*r**3/31
 mu=xyz[0]/r
 radial=b*b*((12*a*a+4*a*bg)*mu*mu-2*a*a)
 print(label,'direct_4D_minus_Hessian=',2*Gnn-invariant)
 assert 2*Gnn==invariant
 if not angular:
  print(label,'Hessian_minus_radial=',invariant-radial)
  assert invariant==radial
run('p1',(1,2,2))
run('p2',(2,3,6))
run('p3',(F(1,3),F(2,3),F(-2,3)))
run('axisymmetric-angular',(2,3,6),True)

