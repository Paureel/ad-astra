# Mathematical model and evaluator

The full derivation and proposed proof decomposition are in
[FORMALIZATION.md](FORMALIZATION.md). This document maps those definitions to
the implementation. All real-analysis formulas here require their stated
regularity and decay assumptions; prose derivations are not Lean certificates.

## Geometry and reference profile

Write `u = ct`, `q = (x_lab - beta ct, y, z)`, `r = |q|`, and

\[
F(r)=\frac{\tanh[\sigma(r+R)]-\tanh[\sigma(r-R)]}{2\tanh(\sigma R)},
\qquad f=1-F,
\qquad g_0(r)=\frac1r\int_0^r f(a)\,da.
\]

Set `g0(0) = 0` by the smooth extension. The reference potential is
`Phi0 = beta x g0(r)` and `W = grad(Phi)`. The repository uses
`ds^2 = -du^2 + |dq + W du|^2`; this explicitly fixes the shift sign convention.
The spatial metric is Euclidean and the lapse is one, so `dV = d^3q` and the
future unit normal has components `n = (1, -W)`.

At the center `W = 0`; at infinity `W -> beta e_x`. The metric has Lorentzian
signature everywhere for any finite smooth W. This property alone does not
prove the physical availability of its required stress-energy source.

`geometry.py` implements the baseline derivatives analytically. Hyperbolic
functions use cancellation-resistant forms. A Taylor expansion through order
`r^6` is used when `sigma r < 10^-3`. Its truncation and floating-point rounding
are numerical approximations, not certified transcendental enclosures.

## Admissible candidate syntax

\[
\Phi=\beta\left[xg_0(r)+R b(s) P(x/R,(y^2+z^2)/R^2)\right],
\qquad s=\frac{r^2-100}{1500}.
\]

`b(s) = [4s(1-s)]^6` for `0 < s < 1`, and zero otherwise. Its first five
derivatives vanish at both endpoints, giving a C5 potential and C4 shift metric
across the compact perturbation's joins. The formal polynomial endpoint
identities are checked in Lean; connecting them to the piecewise real function
is an open proof obligation.

The nine allowed monomials are `1, u, u^2, u^3, u^4, w, uw, u^2w, w^2`, with
`u = x/R` and `w = (y^2+z^2)/R^2`. Each coefficient is an exact rational in
`[-1/10, 1/10]`. `model.py` enforces these syntax constraints and rejects
unknown keys, duplicate keys, duplicate monomials, and parameter overrides.
Zero terms are canonicalized for the parameter hash. The source-file byte
hash is retained separately from the canonical parameter identity.

## Energy reduction

With `K = Hess(Phi)`, the Hamiltonian constraint for the fixed flat spatial
slices gives

\[
\rho_E=\frac{c^4}{16\pi G}
\left[(\operatorname{tr}K)^2-\operatorname{tr}(K^2)\right].
\]

This is `T(n,n)` in energy-density units. The score is its absolute integral.
The independent tensor path in `independent.py` constructs the 4D Ricci and
Einstein tensors from finite differences of the metric and compares `2G(n,n)`
with the reduced Hessian expression. It catches sign, normalization, and
derivative mistakes on tested points; it is not a proof of the identity.

For the unperturbed radial potential, let `a = g0'`, `mu = x/r`,
`p = 4a(a+f')`, and `q = 2a^2`. The reduced invariant is
`beta^2 (p mu^2 - q)`. The half-angle integral is

\[
H(p,q)=\int_0^1|p\mu^2-q|\,d\mu
=\begin{cases}
q-p/3,&p\le q,\\
p/3-q+(4q/3)\sqrt{q/p},&p>q\ge0.
\end{cases}
\]

Thus `E_abs = c^4 beta^2/(4G) integral_0^infinity r^2 H(p,q) dr`.
This analytic angular reduction is independent of the candidate's numerical
polynomial-root integration route.

For candidates, axial symmetry removes the azimuthal integral. At fixed r the
remaining invariant is an angular polynomial of degree at most eight for this
restricted potential basis. The numerical implementation fits degree ten
(degree twelve on refinement), checks additional angles, locates its real
roots, and integrates the absolute polynomial between roots. Polynomial
fitting, coefficient trimming, root selection, and quadrature errors are not
rigorously enclosed in the bootstrap.

## Infinite tail

Let `C = R coth(sigma R)`, `k = coth(sigma R)`, `lambda = 2 sigma`. Outside
the compact perturbation,
`g0(r) = 1 - C/r + J(r)/r`, where `J(r) = integral_r^infinity F(a) da`.
For `L > R` and beyond all perturbations, the leading absolute tail is

\[
T_0(L)=\frac{c^4\beta^2 C^2}{6GL}(2\sqrt2-1).
\]

The derivation in FORMALIZATION.md gives the exponential remainder estimate

\[
|E_{\rm tail}-T_0|\le
\frac{c^4\beta^2}{4G}Ck e^{-\lambda(L-R)}
\left(\frac43+\frac{20}{3\lambda L}
+\frac{20}{3\lambda^2 L^2}\right).
\]

This bound's analytic derivation is supplied, but its hypotheses and
floating-point evaluation are not yet formally verified. The very small
exponential remainder is not an error bound on the large leading term's
floating-point evaluation or on the interior quadrature. Reports explicitly
label their total error estimate as heuristic.

The signed radial identity
`r^2(p/3-q) = (2/3) d[r^3(g0')^2]/dr` provides another consistency check.
More generally, integration by parts under the smoothness and decay assumptions
gives cancellation of the signed energy for these irrotational fields. A zero
signed sum must never be described as zero required source-energy magnitude.

## Null rays for the viewer

The stationary geodesic Hamiltonian is

\[
\mathcal H=\frac12[-(p_0-\mathbf W\cdot\mathbf p)^2+|\mathbf p|^2].
\]

For a unit Eulerian launch direction d, set `p = d` and `p0 = W(q0).d - 1`.
The constant p0 is the stationary covariant time momentum. With
`omega = -p0 + W.p`, integration using `u = ct` follows

\[
\frac{d\mathbf q}{du}=\frac{\mathbf p}{\omega}-\mathbf W,
\qquad
\frac{d\mathbf p}{du}=(D\mathbf W)^T\mathbf p.
\]

`geodesics.py` supplies the actual numerical paths, termination reasons and
null residuals. The ship is a scale marker. The spherical reference F contours
are not event horizons and need not be contours of a perturbed metric. An
outgoing trajectory that leaves the plotted domain does not establish escape
to infinity. This viewer does not solve the Einstein-matter evolution problem.

