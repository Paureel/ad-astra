# A stronger lower bound for every compact 100 m geometry

## Result and scope

For every admitted potential in the compact R=100 m scenario,

\[
 \boxed{E_{\rm abs}\ge
 \frac{c^4 B^2 aR}{3G(R-a)\log(R/a)},\qquad
 B\ge\beta-\epsilon,}
\]

where a=10 m, beta=2 and epsilon=10^-6. The exact arithmetic replay gives

\[
 E_{\rm abs}>7.7867672248534370922\times10^{44}\ {\rm J}.
\]

Consequently the improvement factor against the reference is strictly
less than 5.459424. A tenfold reduction is impossible within this
specified compact class. The proof permits every angular dependence,
including broken axial, reflection and odd-parity symmetries. It does not
restrict the candidate to a spline representation.

The retained global derivative caps are not needed for the inequality.
They remain in force, so the theorem applies to a larger class than the
admitted one. No energy condition or additional material-source bound is
introduced. This is an ordinary analytic result with exact arithmetic
checks and independent mathematical review, not a formally certified
record or a statement of physical realizability.

The localized contract is unchanged. This phase selects its exactly
uniform exterior beyond 100 m scenario. No Phase 1 candidate or evidence
file is modified.

## 1. The weighted identity

Choose the exterior additive constant so that

\[
 \psi=\Phi-\beta x-C_{\rm ext}=0\quad(r\ge R).
\]

Thus v=grad psi vanishes outside the same ball. Set

\[
 H=D^2\psi,\qquad Q=(\operatorname{tr}H)^2-|H|_F^2.
\]

The affine subtraction does not change H, Q or the specified energy.
The divergence identity and a second integration by parts give

\[
 Q=\partial_i(v_i\Delta\psi-v_j\psi_{ij}),\qquad
 \int Q\,d^3q=0,
\]
\[
 \boxed{\int wQ\,d^3q
 =\int(D^2w-\Delta w\,I)[v,v]\,d^3q.}
\]

This identity also holds for a piecewise smooth Lipschitz weight, with
its second derivatives interpreted as distributions. Here v is smooth
and compact, so the interface terms are unambiguous. Equivalently, one
may smooth the two weight corners and pass to the limit.

Let L=log(R/a) and choose the clipped logarithmic weight

\[
 w(r)=\begin{cases}
 0,&0\le r\le a,\\
 \log(r/a)/L,&a<r<R,\\
 1,&r\ge R.
 \end{cases}
\]

Inside the open annulus, A=Delta w I-D^2w has radial eigenvalue
2/(Lr^2) and two zero tangential eigenvalues. The upward derivative
jump at a gives the positive tangential surface term. The downward jump
at R gives a negative tangential surface term, but its pairing with v is
zero because v=0 there. Therefore

\[
 K:=-\int wQ\,d^3q
 =\frac2L\int_a^R\int_{S^2}\psi_r^2\,d\Omega\,dr
 +\frac1{aL}\int_{S^2}
       |\nabla_{S^2}\psi(a,\Omega)|^2\,d\Omega.
 \tag{1}
\]

Both terms are nonnegative. In particular, omitting the inner surface
term would lose most of the strength of the new estimate.

## 2. The core supplies a fixed dipole

The exact core gives, on the sphere r=a,

\[
 \psi(a,\Omega)=-Ba\mu-C_{\rm ext},\qquad
 B=\beta(1-g_0(a)),\quad \mu=x/r.
\]

The cabin shift cap implies B>=beta-epsilon. More generally, the same
lower estimate follows from the degree-one projection of the trace and
the average shift over the cabin. Higher spherical harmonics and an
arbitrary additive constant only add nonnegative terms to the estimates
below.

Since integral mu^2 dOmega=4pi/3 and
integral |grad_S mu|^2 dOmega=8pi/3,

\[
 \int_{S^2}\psi(a,\Omega)^2d\Omega
 \ge\frac{4\pi}3 B^2a^2,
\]
\[
 \int_{S^2}|\nabla_{S^2}\psi(a,\Omega)|^2d\Omega
 \ge\frac{8\pi}3 B^2a^2.
\]

For every direction Omega, Cauchy-Schwarz on the finite radial interval
and the zero outer trace imply

\[
 \int_a^R\psi_r^2dr
 \ge\frac{\psi(a,\Omega)^2}{R-a}.
\]

Substitution in (1) gives

\[
 K\ge\frac{8\pi B^2}{3L}
       \left(\frac{a^2}{R-a}+a\right)
   =\frac{8\pi B^2aR}{3(R-a)L}.
 \tag{2}
\]

This argument is raywise and uses only the inner trace. It makes no
assumption about the angular structure of the intervening geometry.

## 3. The absolute energy and the factor of two

Because integral Q=0 and 0<=w<=1,

\[
 K=\left|\int(w-\tfrac12)Q\,d^3q\right|
 \le\frac12\int|Q|\,d^3q.
\]

Combining this with (2) and the fixed normalization

\[
 E_{\rm abs}=\frac{c^4}{16\pi G}\int|Q|\,d^3q
\]

proves the stated theorem. The centering factor of two is essential.
Signed cancellation is used to establish a lower bound on the absolute
objective, never to replace it as the energy being minimized.

## 4. Exact arithmetic and independent checks

The replay script uses the exact SI constants from the protected
benchmark and B=1999999/1000000. It proves

\[
 \log10<\frac{2302585092994046}{10^{15}}
\]

by verifying that the positive exponential Taylor sum through degree 50
at this rational value exceeds 10. Substituting this upper endpoint in
the denominator yields an exact rational energy lower bound.

The maximum improvement factor uses the reference's outward upper
endpoint, not a central estimate. The prior compact bound was
9.6917265592 x 10^43 J. The new bound is larger by a factor exceeding
8.0344479. The Phase 1 compact upper endpoint is within a factor
2.299664 of the new universal lower bound. This gap does not predict the
attainable optimum.

The script also constructs four different compact C5 Cartesian
polynomials, including nonaxisymmetric mixed terms. At three inner radii
for each polynomial it integrates both sides of (1) exactly after
factoring out pi. The potential logarithmic terms cancel by integral
Q=0, so all 12 checks use rational arithmetic. These checks independently
exercise both the shell and surface coefficients. They supplement the
general integration-by-parts proof; finite examples alone are not a
proof for every potential.

Reproduce with:

```text
python research/radical_compact/variational_physics/clipped_log_bound.py
```

The output receipt `clipped-log-bound.json` binds its source, task claim,
contract, protected benchmark, reference interval and Phase 1 compact
receipt. Root and the analytic-geometry agent independently checked the
interface signs, spherical normalization and energy factor.

## 5. Optimality within one radial calibration class

The log weight is optimal within the following restricted method: radial
weights whose A=Delta w I-D^2w is positive semidefinite through the ball,
apart from the harmless exterior interface, and whose range is one.
This is not an optimality statement about the physical potential.

Write p(r)=r w'(r). Positivity requires p>=0 and p nondecreasing. The
normalization gives integral_0^R p(r)/r dr=1. Relax the fixed core to its
affine dipole with the same inner trace; this can only lower its weighted
Dirichlet cost. For a dipole psi=y(r)mu, set z=y/r. Direct expansion gives

\[
 p(y')^2+\frac{p'}r y^2=(rpz^2)'+pr^2(z')^2.
\]

The weighted capacity, including the core/interface contribution, is
therefore

\[
 \mathcal C[w]=\frac{8\pi}3
 \frac{B^2}{I[p]},\qquad
 I[p]=\int_a^R\frac{dr}{p(r)r^2}.
\]

Put t=log(r/a). Then p(t) is nondecreasing and
integral_0^L p(t)dt<=1. Both exp(-t) and 1/p(t) are nonincreasing.
Chebyshev's integral inequality and Cauchy-Schwarz give

\[
 I[p]=\frac1a\int_0^L\frac{e^{-t}}{p(t)}dt
 \ge\frac{1-e^{-L}}{aL}\int_0^L\frac{dt}{p(t)}
 \ge\frac{L(1-e^{-L})}{a}
 =L\left(\frac1a-\frac1R\right).
\]

Equality is attained by p=1/L in the shell and p=0 inside the core,
precisely the clipped logarithmic weight. The zero-eigenvalue and jump
cases are understood by approximation. Thus another positive radial
weight cannot improve this particular relaxed dipole-capacity bound.
Nonradial calibrations, bounds that explicitly use the retained derivative
caps, and different identities remain possible sources of a stronger
global lower bound.

## Interpretation

The earlier weak quadratic-moment barrier left a tenfold target open.
This stronger theorem closes that possibility for the authorized compact
100 m scenario. It does not close the substantial gap below the best
candidate, and it does not apply to arbitrary noncompact exteriors.
Candidate work should continue toward improvements inside the remaining
gap rather than claim an orders-of-magnitude result in this class.
