# Formalization contract and mathematical derivation

## Current status

The numerical benchmark is `rodal-2c-v1-draft`. The Lean project proves exact
rational arithmetic and polynomial identities only. The bootstrap has no
end-to-end formal certificate of an admissible spacetime or its source energy.
The required status remains:

```json
{
  "formal_certification": false,
  "certified_bounds": null
}
```

Successful numerical refinement, agreement between two implementations, and a
successful Lean arithmetic build do not change that status. No omitted proof
is hidden behind an admitted theorem or a new axiom.

## Published family and normalized reference

The reference is José Rodal, *A warp drive with predominantly positive invariant
energy density and global Hawking–Ellis Type I*, published 17 December 2025 in
*General Relativity and Gravitation*, volume 58, article 1 (2026).

- DOI: <https://doi.org/10.1007/s10714-025-03495-x>
- Versioned manuscript: <https://arxiv.org/html/2512.18008v1>
- Relevant equations: (14), (36), (38)–(43), and Appendix 9, (9.1)–(9.3).

The benchmark instantiates that smooth published family at speed parameter
`beta = 2`, bubble profile radius `R = 20 m`, and `sigma = 1/m`. These are
benchmark parameters, not a claim to reproduce every parameter or numerical
table in the paper. The dimensionless smoothing product is `sigma R = 20`.
The chosen payload region has proper spatial radius 10 m because the spatial
slices are Euclidean. Its baseline metric is approximately flat, not exactly
flat. Its allowed deviations require a separate explicit global certificate.

Define

\[
F(r)=\frac{\tanh[\sigma(r+R)]-\tanh[\sigma(r-R)]}
 {2\tanh(\sigma R)},\qquad f(r)=1-F(r),
\]

\[
g_0(r)=\frac1r\int_0^r f(s)\,ds,
\qquad g_0(0)=0.
\]

The relation `f = g_0 + r g_0'` determines the radial shift component.
The apparent division by zero in this integral representation is removable:
`f` is an even analytic function with `f(0)=0`, so `g_0` has an even Taylor
expansion starting at order `r^2`.

In comoving Cartesian coordinates `q=(x,y,z)`, use length-valued time
`tau=ct`, and define

\[
\Phi_0(\mathbf q)=\beta x g_0(r),\qquad
\mathbf W=\nabla\Phi,\qquad
ds^2=-d\tau^2+|d\mathbf q+\mathbf W\,d\tau|^2.
\]

This uses a sign convention in which `W = grad Phi`; the paper's shift
notation has the opposite sign. At the center `W=0`. At infinity
`W -> beta e_x`. The exterior inertial coordinate is asymptotically
`X=x+beta tau`, so the center is timelike while having asymptotic speed `beta`.
A full operational transit theorem, including the chosen exterior clocks,
is still required before formal certification.

## Permitted compact perturbations

The optimization changes the scalar potential:

\[
\Phi=\beta\left[xg_0(r)+R\,b(s)P(u,w)\right],
\quad u=x/R,\quad w=(y^2+z^2)/R^2,
\]

\[
s=\frac{r^2-10^2}{40^2-10^2},\qquad
b(s)=[4s(1-s)]^6\quad(0<s<1),
\]

with `b=0` elsewhere. The radii in this formula are in meters.
The nine monomials are `1,u,u^2,u^3,u^4,w,uw,u^2w,w^2`; equivalently
`u^i w^j` with `i+2j <= 4`. Each exact rational coefficient has absolute
value at most `1/10` in the draft design space. The canonical numerical schema
and Lean encoding must be bound to the same order before any candidate
certificate can be promoted.

The sixth-order zeros at `s=0,1` allow the piecewise potential perturbation to
be `C^5`. Therefore its shift is `C^4`, sufficient for the classical curvature
calculations used here. This reasoning must still be connected to a formal
real-calculus theorem. The existing Lean file checks the endpoint identities
of the *formal polynomial*, not the differentiability of the physical field.

The perturbation is exactly zero inside 10 m and outside 40 m. It preserves the
published baseline cabin and far field. This is an axisymmetric scalar-potential
search space. It does not exhaust all irrotational potentials or all warp
metrics, and no global optimality claim is attached to a numerical record.

## Source-energy reduction

The lapse is 1 and the induced spatial metric is Euclidean. The future unit
normal is `n = partial_tau - W^i partial_i`. Let

\[
H_{ij}=\partial_i\partial_j\Phi.
\]

The flat-slice Hamiltonian constraint gives the proposed reduced density

\[
\rho_E=\frac{c^4}{16\pi G}
\left[(\operatorname{tr}H)^2-\operatorname{tr}(H^2)\right],
\qquad
E_{\rm abs}=\int_{\mathbb R^3}|\rho_E|\,d^3q.
\]

For a symmetric Hessian the bracket also equals

\[
2(H_{xx}H_{yy}+H_{xx}H_{zz}+H_{yy}H_{zz}
 -H_{xy}^2-H_{xz}^2-H_{yz}^2).
\]

Lean currently proves this last polynomial identity over exact rationals.
It does not yet prove that the variables are derivatives of the candidate,
or that the expression equals the Einstein contraction of the metric.
Those two semantic connections are essential outstanding obligations.

This energy is a source-energy magnitude on the specified slice. It does not
include a model for creating the geometry or manufacturing its source.
For an irrotational shift the momentum density vanishes under the stated
smoothness assumptions, giving a timelike rest-frame energy density. The
full stress and curvature constraints still matter: a low density score
does not by itself control pressures, fluxes, or tidal effects.

## Exact angular reduction for the unperturbed radial reference

This section supplies an independent scalar reference calculation.
It does not apply unchanged to the angularly perturbed candidates.

Let `a=g_0'(r)`, `b=r g_0''(r)`, and `mu=x/r`. In a radial orthonormal basis,
up to the sign of the off-diagonal element induced by the angular orientation,

\[
H=\beta\begin{pmatrix}
\mu(2a+b)&a\sqrt{1-\mu^2}&0\\
a\sqrt{1-\mu^2}&a\mu&0\\
0&0&a\mu
\end{pmatrix}.
\]

Consequently, with `f'=2a+b`,

\[
(\operatorname{tr}H)^2-\operatorname{tr}(H^2)
=\beta^2(p\mu^2-q),
\quad p=4a(a+f'),\quad q=2a^2\ge0.
\]

Define the nonnegative angular integral

\[
\mathcal A(p,q)=\int_0^1|p\mu^2-q|\,d\mu
=\begin{cases}
q-p/3,&p\le q,\\
p/3-q+(4q/3)\sqrt{q/p},&p>q.
\end{cases}
\]

The second branch only divides by positive `p`. Both branches agree at
`p=q`. The energy is

\[
E_{\rm abs}=\frac{c^4\beta^2}{4G}
\int_0^\infty r^2\mathcal A(p(r),q(r))\,dr.
\]

This removes angular quadrature for the reference. The algebraic invariant
identities are in the Lean core; the angular integral and the real calculus
behind it are not yet formalized.

As an additional check,

\[
r^2(p/3-q)=\frac23\frac{d}{dr}\left[r^3(g_0')^2\right].
\]

Both boundary terms vanish for this profile. Thus the signed whole-slice
energy vanishes, whereas `E_abs` remains positive. Compact smooth potential
perturbations preserve the far-field boundary terms. A signed-energy score
would therefore be unsuitable for this challenge.

## Analytic tail and a conservative error enclosure

The baseline is not compactly supported. Its infinite tail must be included.
Define

\[
k=\coth(\sigma R),\quad \lambda=2\sigma,\quad
C=\int_0^\infty F(r)\,dr=Rk,\quad J(r)=\int_r^\infty F(s)\,ds.
\]

Then exactly

\[
g_0(r)=1-C/r+J(r)/r,\qquad
g_0'(r)=C/r^2-[J(r)+rF(r)]/r^2.
\]

For `r >= L > R`, elementary exponential bounds give

\[
0\le F(r)\le k e^{-\lambda(r-R)},\quad
0\le f'(r)\le\lambda k e^{-\lambda(r-R)},\quad
0\le J(r)\le(k/\lambda)e^{-\lambda(r-R)}.
\]

The pure algebraic asymptote `g=1-C/r` has tail energy

\[
T_0(L)=\frac{c^4\beta^2 C^2}{6GL}(2\sqrt2-1).
\]

This is **not** the exact tail of the hyperbolic profile. A conservative
error bound for the actual baseline is

\[
|E_{\rm tail}(L)-T_0(L)|\le
\frac{c^4\beta^2}{4G}\,Ck e^{-\lambda(L-R)}
\left[\frac43+\frac{20}{3\lambda L}
+\frac{20}{3\lambda^2L^2}\right].
\]

This bound also applies unchanged to every admissible compact perturbation
when `L >= 40 m`, since the candidate equals the baseline outside that radius.

Derivation: set `a0=C/r^2` and
`delta_a=k exp(-lambda(r-R))(1/r+1/(lambda r^2))`. Monotonicity of `F` gives
`0 <= a <= a0` and `a0-a <= delta_a`. Let
`delta_f=lambda k exp(-lambda(r-R))`. Comparing the angular integrands and
using `||x|-|y|| <= |x-y|` yields

\[
|\mathcal A(p,q)-\mathcal A(4a_0^2,2a_0^2)|
\le \frac{20}{3}a_0\delta_a+\frac43 a_0\delta_f.
\]

Multiply by `r^2`, integrate, and use `1/r <= 1/L` and
`1/r^2 <= 1/L^2` to obtain the stated remainder. All side conditions,
transcendental enclosures, improper-integral steps, and SI constant choices
must be checked in the future real-analysis certificate. The bootstrap's
floating-point evaluation of this formula is not itself a formal enclosure.

## What the Lean build establishes today

| Component | Checked statement | Still missing |
|---|---|---|
| Coefficients | Nine exact rationals pass the fixed coefficient bound | Binding to parsed candidate bytes and field semantics |
| Polynomial endpoint jets | Formal derivatives of `[4s(1-s)]^6` through order 5 vanish at 0 and 1 | Real derivatives and piecewise `C^5` theorem |
| Hessian algebra | Rational polynomial identities | Differentiation and Einstein-tensor bridge |
| Interval composition | Addition, scaling, and remainder widening for rational enclosures | Enclosures of actual real-valued quantities |
| Record rule | An interval gap implies strict ordering of contained rational values | Certified real energy intervals and candidate binding |
| Tail | Conditional arithmetic composition only | The analytic inequalities and improper integration above |

Closed computations use kernel reduction. The theorem audit accepts only
Lean's standard `propext`, `Classical.choice`, and `Quot.sound` foundations.
It rejects unexpected transitive axiom dependencies in the audited targets.
This does not replace sandboxing: elaboration and tactics can execute code.

## Required implementation order for a full certificate

1. Add a pinned real-analysis library and define the exact benchmark semantics,
   including units, slicing, observers, profile, and operational speed claim.
2. Prove the profile's regular origin, tail, and derivative formulas; connect
   the compact polynomial extension to real `C^5` regularity.
3. Prove the metric has Lorentzian signature and derive the Hessian energy
   functional from the full Einstein tensor under explicit assumptions.
4. Bind exact candidate bytes and canonical rational coefficients to the
   formal potential. Keep the trusted checker outside candidate-controlled
   source files and verify a fixed statement identity.
5. Specify and prove all everywhere cabin, curvature, and stress constraints.
   Coefficient bounds are not a substitute for these conditions.
6. Implement exact enclosure certificates for finite-domain integration and
   the analytic tail. Cover the axis, origin, joins, and whole exterior.
7. Produce a theorem `Admissible candidate AND L <= E_abs candidate <= U`.
   Require independent replay and update the promotion gate only after this
   theorem exists, is bound to the candidate, and passes an axiom audit.

An inability to find a certificate is inconclusive. It must not be reported
as a proof that the geometry is impossible or that the claimed inequality is
false. Numerical simulations remain independent verification and visualization
inputs throughout this process.

