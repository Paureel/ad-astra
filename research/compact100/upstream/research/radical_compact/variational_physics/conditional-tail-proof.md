# Conditional bounds when the exterior is not exactly flat

The compact-exterior theorem cannot be applied at an arbitrary radius
inside a noncompact tail. The missing term is an outer spherical
tangential-gradient contribution. Keeping it gives a useful conditional
statement and a separate corollary for the existing reference-comparable
tail scenario.

## Assumptions and exact identity

Let psi=Phi-beta*x, with any additive constant, and retain the same core,
metric and Eulerian energy. Assume integral|Q| is finite and the infinity
flux of

\[
 J=\nabla\psi\,\Delta\psi-D^2\psi\,\nabla\psi
\]

vanishes. These hypotheses imply integral Q=0. One sufficient uniform
decay condition is grad psi=O(r^-p), Hess psi=O(r^-p-1), with p>1/2.
They are hypotheses of this statement, not assumptions about every
unspecified exterior that might be called realistic.

Use the same clipped logarithmic weight with L=log(R/a). Its outer
corner now contributes:

\[
 K_w:=-\int wQ\,dq
 =\frac2L\int_a^R\|\psi_r\|_{L^2(S^2)}^2dr
 +\frac{\|\nabla_S\psi(a)\|_2^2}{aL}
 -\frac{\|\nabla_S\psi(R)\|_2^2}{RL}.
 \tag{1}
\]

The last term has a negative sign. Omitting it would incorrectly turn
the compact theorem into a theorem about arbitrary tails.

Centering the weight still gives integral|Q|>=2|K_w|. Define

\[
 S_R=\frac1{4\pi}\|\nabla_S\psi(R)\|_2^2
 =R^2\operatorname{mean}_{S^2}|v_T(R)|^2,
\]

where v_T is the component of grad psi tangent to the sphere. Dropping
the nonnegative radial term yields

\[
 \boxed{E_{\rm abs}\ge\frac{c^4}{G\log(R/a)}
 \left[\frac{B^2a}{3}-\frac{S_R}{2R}\right]_+,}
 \tag{2}
\]

with B>=beta-epsilon. Brackets with subscript plus mean the nonnegative
part. A pointwise bound |v_T|<=delta implies S_R<=R^2 delta^2, giving
the equivalent conservative term -R delta^2/2 in the bracket.

## Radial trace information can improve the bound

Define the outer x-dipole coefficient by

\[
 b_R=\frac3{4\pi}\int_{S^2}\psi(R,\Omega)\mu\,d\Omega.
\]

For the actual inner coefficient B, radial Cauchy-Schwarz adds
(Ba+b_R)^2/[3(R-a)] inside the bracket of (2). The precise statement is

\[
 E_{\rm abs}\ge\frac{c^4}{GL}
 \left[\frac{B^2a}{3}
 +\frac{(Ba+b_R)^2}{3(R-a)}-\frac{S_R}{2R}\right]_+.
 \tag{3}
\]

The signed-square expression is not always monotone in B. If only a
lower bound on B is available, the correct procedure is to minimize (3)
over a known B interval, or use the following monotone alternative.

Angular orthogonality gives |b_R|<=sqrt(3S_R/2). Therefore

\[
 \boxed{E_{\rm abs}\ge\frac{c^4}{GL}
 \left[\frac{B^2a}{3}
 +\frac{(Ba-\sqrt{3S_R/2})_+^2}{3(R-a)}
 -\frac{S_R}{2R}\right]_+.}
 \tag{4}
\]

This expression is nondecreasing in B>=0 and nonincreasing in S_R. It
thus safely accepts a lower bound on B and an upper bound on S_R.
Setting S_R=0 recovers the compact bound. No symmetry assumption has
been introduced.

## A distinct corollary for the original norm envelope

Consider the existing reference-comparable scenario: at every point
with r>=40 m, the candidate shift deviation and Hessian norms are no
larger than the corresponding reference norms. This differs from the
compact 100 m candidate scenario; a compact candidate need not satisfy
the reference envelope within its transition region.

The envelope gives v=O(r^-1) and Hess psi=O(r^-2), so the assumed
integrability and vanishing infinity flux follow. At a single sphere
R=150 m, write D0=1-g0(R), epsilon0=1-(g0+R g0'). The reference obeys

\[
 \frac{|v_{\rm ref}|^2}{\beta^2}
 =D_0^2(1-\mu^2)+\epsilon_0^2\mu^2.
\]

The candidate's tangential norm is at most its full norm. Integrating
the actual angular envelope therefore gives

\[
 S_R\le\beta^2\left[\frac23(RD_0)^2+
                          \frac13(R\epsilon_0)^2\right].
 \tag{5}
\]

This angular integral matters: replacing the reference by its maximum
norm would give a weaker estimate.

Let q=exp(-40). A positive Taylor sum proves q<10^-17. Then

\[
 RD_0<\frac{20}{\tanh20}
 <20\frac{1+10^{-17}}{1-10^{-17}},\qquad
 \epsilon_0<2e^{-260}<2(10^{-17})^6.
\]

Substitution into (5), with beta=2, proves the convenient rational bound
S_R<1067 square metres. Equation (2) now gives

\[
 \boxed{E_{\rm abs}>
 4.3692872061457726350\times10^{44}\ {\rm J}.}
\]

The maximum improvement factor against the reference is consequently
less than 9.729565. A tenfold reduction is excluded within this specific
reference-comparable noncompact-tail scenario too. This conclusion uses
the declared norm envelope; it is not a bound on every conceivable
noncompact exterior or a statement of engineering safety.

## Verification and limits

The script `conditional_tail_bound.py` tests (1) on four Cartesian C5
potentials with three pairs of inner and outer radii each. Their support
extends beyond the test sphere, and nine checks have a nonzero outer
tangential term. Every identity is evaluated exactly as a rational
multiple of pi. The checks also assert that deleting the outer term
fails in those nine cases.

The corollary uses exact rational bounds on the reference profile and
the previously reviewed outward logarithm enclosure. The script binds
both helper sources, the unchanged contract, the benchmark and the
reference receipt. Reproduce with:

```text
python research/radical_compact/variational_physics/conditional_tail_bound.py
```

Its receipt is `conditional-tail-bound.json`. No earlier evidence file
is modified, and formal certification remains unavailable.
