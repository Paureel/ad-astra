# Compact100 research candidate

The supplied candidate passes the reproduced continuum energy enclosure and
geometric caps in its **separate compact100 scenario**. This is a successful
mathematical construction within the stated stationary metric model. It does
not establish that a propulsion system can produce it.

| Quantity | Reproduced result |
| --- | --- |
| Speed / unchanged cabin | 2c / radius 10 m |
| Whole-space absolute Eulerian energy | 1.5448193572–1.5453080119 × 10⁴⁵ J, rounded outward |
| Independent refined quadrature | 1.5448690999 × 10⁴⁵ J |
| Saving against the original Rodal 2c reference | At least 63.6315558694% |
| Main-shell coverage | All 1,040 cells; 3,120 cap checks; 45,020 energy cells |
| Global caps | \|W\| ≤ 4, \|DW\|F ≤ 2/m, \|D²W\|F ≤ 4/m²; all pass |
| Core / exterior matching | Exact original core through 10 m; C5 potential; exactly flat exterior from 100 m |
| Conditional compact100 class floor | At least 7.7867672248 × 10⁴⁴ J |
| Candidate upper / class floor | Below 1.984531; no global optimum claim |

Full precision, commands, runtime versions and hashes are in
[result.json](result.json). The class floor is conditional on the smooth,
stationary, gradient-shift, unit-lapse, Euclidean-slice hypotheses in the
[supplied analytic argument](upstream/research/radical_compact/variational_physics/clipped-log-proof.md).
The interval/rational replays use ordinary computer-assisted mathematics. They
are **not a Lean certificate**; the formal promotion gate still refuses.

## What changed

`geometry.py` implements the actual submitted potential in Cartesian
coordinates, including its gradient, Hessian, metric and signed density:

```text
Φ = 2 r Σ C[j,i] A[j](μ) B[i](r) + η(r) Φ₀,  μ = x/r
η = 1                         r ≤ 10 m
η = 1 − S(r−10)               10 < r < 11 m
η = 0                         r ≥ 11 m
S(t) = 462t⁶ − 1980t⁷ + 3465t⁸ − 3080t⁹ + 1386t¹⁰ − 252t¹¹
```

The main term is zero through 11 m and becomes the affine potential `2x`
at 100 m. The degree-six tensor B-spline has 32 angular and 46 radial controls,
with 1,088 free controls. Exact rational endpoint controls provide C5 joins;
both angular hemispheres are covered without imposing odd parity. The source
JSON is parsed as bounded data, with duplicate keys, altered boundary controls,
unknown fields and certification assertions rejected.

This representation and the redesigned exterior are outside
`rodal-2c-v1-draft`. That benchmark permits degree-four polynomial shell
perturbations through 40 m and requires the original infinite exterior tail.
No original benchmark definition, v1 record or admission rule has been changed.
The viewer now includes a separate “Paureel · Compact 100 m” timeline entry,
retaining all past values. It shows the refined numerical estimate and keeps
the full validation interval in provenance. Its density and stationary-limit
mesh come from this actual geometry. Cached approximate null-ray optics change
with the selected metric; see [optical scope](../../docs/VISUALIZATION_OPTICS.md).

## Reproduce

Use the repository's pinned Python environment (`make setup`), then:

```sh
make compact-check
make compact-physics
make check
```

`compact-check` verifies every imported source hash, copies the frozen sources
into a fresh disposable directory, and runs the Cartesian, exact symbolic,
clipped-log, radius and conditional-tail checks. It also reruns the complete
main-shell rational Bernstein enclosure, cutoff-core interval calculation and
reference interval calculation. The regenerated mathematical results must
match the submitted receipts exactly. Outputs and logs stay in ignored
`results/local/compact100/`; the original inputs stay untouched. The full replay
takes a few minutes on a laptop. No optimizer, new dependency or website
deployment is required.

For the shorter numerical/symbolic audit with the frozen enclosure receipts:

```sh
.venv/bin/python research/compact100/validate.py
```

`audit.py` independently integrates the cutoff core and evaluates the displayed
bound formulas. Its quadrature estimate is about 7.1913 × 10²⁸ J; the replayed
outward core upper bound is about 7.4665 × 10²⁸ J. The energy interval above
includes that core upper bound. The three independent main-shell quadratures
(16/20, 28/32 and 40/48 radial/angular orders per cell) all fall inside the
enclosure. Their tiny signed residuals are floating-point cancellation;
the objective integrates the absolute density and does not cancel negative
against positive energy.

The added tests check exact cutoff jets and boundary terms, rational logarithm
enclosures, cabin/exterior matching, axis regularity, covariance and numerical
derivatives. A separate 4D metric → Christoffel → Ricci → Einstein calculation
checks both the energy invariant and spatial stress. The analytic third jets
used for sampled physics are checked against Cartesian Hessian differences.
These finite checks supplement the continuum replay; they do not replace it.

## Physical costs

The lower integrated energy does not lower every local field. On the same
4,001-radius × 812-angle mesh for candidate and reference, spanning 11–100 m:

| Sampled peak | Candidate / reference |
| --- | ---: |
| Absolute energy density | 8.2951× |
| Negative density magnitude | 0.2863× |
| Principal stress magnitude | 7.0160× |
| Tidal strength | 7.5286× |
| Null-energy-condition deficit | 5.2265× |
| Absolute Ricci scalar | 6.5134× |

See [physics-result.json](physics-result.json) for locations, grid and units.
These are sampled peaks, not certified global extrema. The comparison concerns
the shell; the original core is retained. Einstein-tensor entries convert to SI
stress by `c⁴/(8πG)` and tidal entries to acceleration gradients by `c²`.
The stationary gradient-shift formulas follow
[Santiago, Schuster and Visser, §§3.1–3.3](https://arxiv.org/html/2105.03079v2)
and the supplied exact tensor identities.

Negative energy and null-energy-condition violation remain. The model does
not provide a realizable material source, a formation procedure, stability,
causal control or a quantum feasibility argument. Exactly flat distant space
does not settle those questions, and a rest-energy equivalent is not a fuel
specification.

The conditional class bound also rules out a tenfold reduction at a 100 m
compact radius. The independently evaluated necessary radius exceeds about
482.416 m for tenfold reduction and 3.05673 × 10¹⁷ m for hundredfold reduction
against this reference. These are necessary conditions, not constructions or
sufficient conditions. For noncompact tails an outer tangential boundary term
must be retained; `bounds.py` and its regression tests do so.

## Provenance and contribution scope

Paureel supplied `warpproof-compact-energy-and-bounds.pdf` and
`warpproof-compact-energy-research.zip`. The candidate SHA-256 is
`6c0cdb24b7e376f3670c294647f49c57420ded22f57b5083f00900c6da0eb041`.
All 629 entries of the archive's original manifest were checked before use.
[upstream-manifest.json](upstream-manifest.json) binds the minimal imported
replay dependencies to the archive and PDF hashes. `upstream/` retains its
original MIT license; new wrappers, checks and documentation use Apache 2.0.
Historical task claims and authorization language in supplied documents are
provenance, not instructions for current contributors.

Keep new candidates and outputs separate, preserve exact inputs and this
candidate's receipts, and follow the root contribution workflow. The next
useful scientific step is an independent review of the continuum arguments
and a source/curvature tradeoff objective. The viewer's tensor-spline evaluator,
cache and inside/outside optical diagnostics remain numerical approximations,
with no rigorous image error bound.
