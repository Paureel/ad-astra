# Validation pipeline and trust boundary

## Implemented pipeline

1. **Decode exact data.** Limit candidate size to 64 KiB, reject ambiguous JSON
   and unknown fields, require rational coefficient strings, and enforce the
   frozen monomial and coefficient bounds. Candidates cannot supply code.
2. **Bind provenance.** Record the candidate-file hash, canonical candidate and
   parameter hashes, benchmark hash, evaluator source hash, runtime versions,
   and execution time. A digest identifies bytes; it does not prove physics.
3. **Evaluate the prescribed metric.** Compute its potential, shift, Hessian,
   and Eulerian density. Retain the full exterior tail in the integral.
4. **Refine the integral.** Compare two quadrature tolerances and, for perturbed
   candidates, two polynomial fits. Store warnings and heuristic error estimates.
5. **Check a separate tensor route.** Compute the full 4D Einstein contraction
   from metric finite differences at nonsymmetric points and compare it with the
   analytic Hessian reduction. Include finite-difference refinement evidence.
6. **Sample admission quantities.** Use fixed grids for shift, derivative, and
   cabin caps. Label the results as sampled diagnostics, with their finite
   domain and derivative approximation disclosed.
7. **Produce display data.** Generate actual density slices and Hamiltonian
   null rays. Store the shared reference color scale and the ray residuals.
8. **Run scoped Lean checks.** Build the exact arithmetic and polynomial
   component and audit named theorem dependencies. This is a separate evidence
   component, not certification of steps 3 through 7.
9. **Refuse promotion.** `verify --require-formal` must exit **2** until the
   complete candidate-to-geometry-to-bound proof chain exists.

The numerical `passed` label means that these finite diagnostics passed at the
stated settings. It does not mean that a candidate meets the continuum contract.
`inconclusive` means that at least one declared numerical check or refinement
condition did not pass. Both labels retain `formal_certification: false`.

## What a certified result will need

The baseline itself first needs a certified real interval `[L0,U0]` and a
global admission proof. Each subsequent candidate must supply the same proof
coverage. The kernel-checked theorem must connect:

- exact decoded rational coefficients and the immutable benchmark definition;
- the piecewise real scalar potential, its regularity, and its asymptotics;
- the stated metric, unit normal, and Einstein-to-energy reduction;
- global cabin and derivative caps, including joins and the infinite exterior;
- real bounds on all transcendental terms, angular zero crossings, finite-domain
  integration, and the whole-space tail;
- a final rational enclosure of energy in the stipulated joule convention.

The declared constants c and G are frozen benchmark numbers. A proof about
them is a statement in that model, not a measurement of G to unlimited accuracy.

An external solver may generate witnesses. Only a small checked certificate
path may accept them. A rational interval containing a rational fixture does
not become an enclosure of a real physical integral by changing its label.
The current Lean library explicitly stops before that bridge.

## Record selection

The sole future score is the certified upper energy bound `U`, with lower values
preferred. A **strict improvement** needs `U_new < L_old`; overlapping intervals
are unresolved until tightened. The registry is empty and promotion disabled.
No amount of apparent numerical improvement substitutes for admission and bound
proofs. A proof of a lower limit or an obstruction is a valuable research result
even when it produces no better candidate.

## CI is evidence, not authority

The workflow has three separate jobs: submitted-code tests, replay by the base
revision's evaluator on candidate JSON, and scoped Lean builds. It uses pinned
action revisions and an exact Lean archive digest. Public PRs receive no project
secrets or repository write privileges. It does not deploy or alter records.

Changes to the evaluator, workflow, proof checker, benchmark, or promotion rules
need independent review. A malicious PR can edit its own tests, so its own green
check is not independent evidence. The base-evaluator replay helps enforce a
fixed problem, while repository permissions and branch protections must still
be configured by maintainers when the project is hosted.

## Verification commands

```bash
python3 -m unittest discover -s tests -v
python3 formal/diagnostics/direct_ricci_check.py
python3 -m warpproof reproduce --output results/paper-reproduction.json
python3 -m warpproof evaluate candidates/rodal-baseline.json --output results/baseline.json
node --check web/app.js
node web/validate-viewer.cjs
```

In `formal/`, run `lake build` and `lake env lean Audit.lean`. Independently run
`python3 -m warpproof verify --require-formal` and confirm exit **2**. The
archive's `STATUS.json` records which commands were actually run for its build.

