# Selected published reference

## Decision

Use the smooth irrotational scalar-potential family in José Rodal,
*A warp drive with predominantly positive invariant energy density and global
Hawking-Ellis Type I*, General Relativity and Gravitation **58**, article 1
(2026), published online in December 2025. The reproducible source snapshot is
[arXiv:2512.18008v1](https://arxiv.org/html/2512.18008v1); the publication DOI is
[10.1007/s10714-025-03495-x](https://doi.org/10.1007/s10714-025-03495-x).

This is a choice for this repository's mathematical requirements, not a claim
that this paper proves a physically feasible drive or the global energy minimum
over general relativity. The benchmark narrows the search to one tractable
family and keeps its metric, frame, and cabin definitions fixed.

The reference has explicit smooth functions and a known noncompact tail.
Its radial symmetry provides an analytic angular integral for an independent
reference calculation. A scalar-potential parameterization lets contributors
explore shape changes while preserving irrotationality by construction.

## Why the earlier radial optimum is not the selected entry

Bobrick and Martire's *Introducing Physical Warp Drives*,
[arXiv:2102.06824v2](https://arxiv.org/html/2102.06824v2), includes a radial
variational solution `f(r) = min(r0/r, 1)` in Appendix A.3. Its derivative jumps
at `r = r0`; accepting it unchanged would conflict with this draft's smooth
metric and bounded-derivative requirements. It also retains an infinite tail.
Their longitudinal flattening result changes the usable longitudinal geometry,
so it cannot be treated as an improvement at an unchanged cabin size without
rechecking the constraints.

Those are useful comparison and extension directions. They are not silently
mixed into this leaderboard. A broader admissible family, a distributional
metric, a different cabin, or a new lapse requires a new benchmark contract.

## Published fixture versus standardized challenge

The paper denotes its profile radius by rho. This repository uses `R` for that
radius and `L` for the numerical integration cutoff, avoiding two meanings for
the same letter.

| Quantity | Paper's energy-table fixture | Fixed challenge |
| --- | --- | --- |
| Speed ratio beta | 1 | **2** |
| Profile radius R | 5 m | 20 m |
| Profile steepness sigma | 4 / m | 1 / m |
| Dimensionless sigma R | 20 | 20 |
| Required proper cabin radius | not a benchmark constraint in the table | 10 m |
| Interior | smooth, approximately flat | same profile, approximately flat |
| Quadrature cutoff L | 12 R = 60 m | 4 R = 80 m |
| Ranked domain | table first reports finite window | entire spatial slice |

The baseline's comoving central worldline is timelike. At infinity the fixed
coordinate transformation is `x_lab = q_x + beta ct`; its asymptotic laboratory
translation is therefore `2c`. This is a prescribed superluminal geometry.
The repository does not yet certify an operational finite-trip time advance,
startup process, ability to steer, or access to the front of the bubble.

## Reproduction

Run `python3 -m warpproof reproduce --output results/paper-reproduction.json`.
The report retains the original fixture and distinguishes the finite-window
comparison from the whole-space tail correction.

| Energy at L = 60 m | Paper Table 6, rounded | Bootstrap numerical calculation |
| --- | ---: | ---: |
| Positive magnitude | 1.29e44 J | 1.293337361e44 J |
| Negative magnitude | 1.21e44 J | 1.209291836e44 J |
| Absolute total | 2.50e44 J | 2.502629197e44 J |
| Signed total | 8.37e42 J | 8.404552530e42 J |

The largest relative difference is about 0.413%. The paper also lists a direct
signed sum of `8.40e42 J` in Table 7. Its grid, sign masks and finite precision
are different from this repository's analytic angular integral and adaptive
radial quadrature. The reproduction threshold is a declared 0.5% comparison
against the published rounded figures; passing it is not a rigorous error
bound on the present calculation.

With the tail included, the original fixture evaluates to approximately
`2.656300315e44 J`, consistent with the paper's rounded tail-corrected
`2.66e44 J`. Keeping `sigma R = 20`, the integral scales as `beta^2 R`.
Multiplying R by four and beta by two multiplies the energy by sixteen:

\[
E_{\rm abs,reference}\approx 4.250080505\times10^{45}\ {\rm J}.
\]

This last number is this repository's standardized calculation. It is not
presented as a value directly quoted by the paper, a certified interval, or a
measured propulsion energy.

## Fixed tail and fixed cabin

Candidate perturbations vanish for `r <= 10 m` and `r >= 40 m`. Thus they
preserve the reference cabin and the entire distant tail. The original tail
extends to infinity even though the perturbations have compact support.
The viewer's 40 m display boundary is not an energy-integration boundary.
Approximately 17.4% of the baseline energy lies outside the 80 m quadrature
radius, so omitting the tail would materially change the score.

The zero-perturbation baseline numerically satisfies the sampled draft caps.
The approximately flat cabin is not an exactly Minkowski region. Global
derivative and cabin bounds remain formalization tasks before this draft can
become a certified competition.

