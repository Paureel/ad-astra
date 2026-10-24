# How much exterior radius is necessary for a large energy reduction?

The compact 100 m scenario remains the active Phase 2 candidate target.
That radius was our declared comparison scenario, not a hard radius
specified by the user. The same theorem can be evaluated at other
compact-exterior radii without claiming those geometries have been
constructed or admitted.

Keep the same 10 m reference core, beta 2, SI constants, Eulerian observer
and whole-space absolute energy. Let

\[
 K=\frac{c^4(\beta-\epsilon)^2a}{3G}
   =1.6136724721105926851\ldots\times10^{45}\ {\rm J}.
\]

For every exactly uniform exterior outside a ball of radius R>a,

\[
 \boxed{E_{\rm abs}\ge
 \frac{K}{(1-a/R)\log(R/a)}.}
\]

The bound holds for arbitrary angular structure. All distances here are
radii measured from the bubble centre, not diameters.

## Radius table

The energy entries below round the proved lower bounds downward. The
improvement factors round conservative upper bounds upward and use the
frozen reference's upper energy endpoint.

| Exactly flat exterior beyond R | Universal energy lower bound, J | Maximum possible improvement factor |
| --- | --- | --- |
| 40 m | 1.5520248487 x 10^45 | less than 2.739084 |
| 80 m | 8.8687134214 x 10^44 | less than 4.793397 |
| 100 m | 7.7867672248 x 10^44 | less than 5.459424 |
| 300 m | 4.9080255073 x 10^44 | less than 8.661582 |
| 500 m | 4.2090871170 x 10^44 | less than 10.099877 |
| 1,000 m | 3.5394396476 x 10^44 | less than 12.010732 |
| 1,000,000 m, or 1,000 km | 1.4016321167 x 10^44 | less than 30.329828 |

The table supplies obstructions, not construction forecasts. For example,
the theorem stops excluding a tenfold reduction near a half-kilometre
radius, but it does not provide a candidate achieving one there.

## Necessary radius for a target factor

Let F be the requested factor relative to the reference and let E_ref,U
be the reference's frozen upper endpoint. If an actual candidate had
E_abs<=E_ref/F, it would necessarily satisfy

\[
 (1-a/R)\log(R/a)\ge\frac{KF}{E_{\rm ref,U}}=:x_F.
 \tag{1}
\]

The left side increases strictly from zero to infinity for R>a. Its
derivative is

\[
 \frac{a}{R^2}\log(R/a)+\frac{1-a/R}{R}>0.
\]

Consequently (1) has a unique threshold. Dropping the factor 1-a/R gives
the simpler but weaker necessary condition

\[
 \boxed{R>a\exp(KF/E_{\rm ref,U}).}
 \tag{2}
\]

The rational interval replay establishes:

| Desired factor | Necessary exterior radius |
| --- | --- |
| 10x | greater than 482.4155916638365989 m |
| 100x | greater than 305672731287163763 m |
| 1000x | greater than 7.1214261575988064 x 10^165 m |

For 10x, the stronger implicit root lies in
[482.4155916638365989,482.4155916638365990] m. The weaker exponential
threshold would give only about 445.17 m, so keeping the finite-radius
factor matters here.

For 100x, the stronger implicit root lies in
[305672731287163763,305672731287163764] m. This is about 32.31 light-years
when a light-year is defined as c times a 365.25-day year. Explicitly,
that distance unit is 9460730472580800 m. This conversion is explanatory;
the proof uses metres and exact rational constants throughout.

For 1000x, the already enormous value in the table uses only the weaker
condition (2). No unresolved implicit-root approximation is used to
make that claim. It follows that many orders of magnitude of saving
cannot be obtained merely by replacing the 100 m compact boundary with
a somewhat larger finite one while retaining the same core and speed.

These precise mathematical intervals use the benchmark's frozen
constants. They are not claims of equivalent experimental precision in
measured physical constants or engineered dimensions.

## Boundary and cabin assumptions, checked again

An exactly constant shift outside the ball implies
Phi-beta*x=C_ext there, because that exterior region is connected.
Subtracting this constant makes psi=0 outside and grad psi=0 at R.
The negative outer interface term of the clipped-log weight then
vanishes. Smooth matching at R is already supplied by the retained C5
condition.

The exact inner trace is

\[
 \psi(a,\Omega)=-Ba\mu-C_{\rm ext},\qquad
 B=\beta(1-g_0(a)).
\]

The divergence theorem gives

\[
 \operatorname{average}_{B_a}W_x=\beta g_0(a).
\]

Hence the retained cabin bound |W|<=epsilon yields
B>=beta-epsilon. The proof does not replace the original core by a flat
one, shrink the cabin or assert a symmetry of the shell. The arbitrary
constant contributes a nonnegative term to the trace L2 norm and no
term to its angular-gradient norm. Higher angular harmonics, if the
argument is stated using only a dipole projection, also contribute
nonnegative orthogonal terms. They cannot remove the estimate.

These statements concern exactly compact exteriors. For a noncompact
tail, the outer interface term need not vanish. A separate conditional
bound is required; substituting an arbitrary radius into this compact
table would be incorrect.

## Exact numerical enclosure method

`radius_scaling.py` evaluates logarithms by power-of-two reduction to
[1,2), followed by the positive atanh series. For z=(x-1)/(x+1),
0<=z<=1/3,

\[
 \log x=2\sum_{j=0}^{N-1}\frac{z^{2j+1}}{2j+1}+\mathcal R_N,
 \quad
 0\le\mathcal R_N\le
 \frac{2z^{2N+1}}{(2N+1)(1-z^2)}.
\]

Exponentials are reduced to an argument at most 1/8, enclosed by a
positive Taylor sum and a geometric bound on its remainder, and then
recovered by repeated outward rational squaring. All elementary
operations use exact fractions with outward quantization to denominator
10^100. Decimal arithmetic is used only to print endpoints.

The proposed implicit-root brackets are accepted only after the exact
logarithm intervals prove that the lower endpoint is below the threshold
and the upper endpoint is above it. No floating-point root is trusted.

Reproduce with:

```text
python research/radical_compact/variational_physics/radius_scaling.py
```

The output `radius-scaling.json` binds its source, the theorem and prior
bound receipt, the unchanged contract, the protected benchmark and the
reference evidence. No earlier receipt is modified. The formal
certification gate remains closed.
