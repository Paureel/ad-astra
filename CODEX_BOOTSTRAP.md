# Start here: a collaborative warp-geometry research project

This repository is a working numerical bootstrap for a future proof-checked
energy challenge. Its initial model is the smooth irrotational warp family in
[Rodal's paper, arXiv:2512.18008](https://arxiv.org/abs/2512.18008), with the
published version identified by
[DOI 10.1007/s10714-025-03495-x](https://doi.org/10.1007/s10714-025-03495-x).

The benchmark is `rodal-2c-v1-draft`, defined in
`benchmarks/rodal-2c-v1.json`. The baseline candidate is
`candidates/rodal-baseline.json`. Every included evaluated result is
`numerical_only`, with formal certification unavailable. The certified registry
in `records/registry.json` starts empty.

## The one quantity to optimize

The project uses the absolute Eulerian energy integral in the fixed benchmark
frame:

\[
E_{\mathrm{abs}}=\int_{\mathbb R^3}|\rho_E|\,d^3q,
\qquad
\rho_E=\frac{c^4}{16\pi G}
\left[(\operatorname{tr}\operatorname{Hess}\Phi)^2
-\operatorname{tr}\bigl((\operatorname{Hess}\Phi)^2\bigr)\right].
\]

The proposed future ranked value is a **proved upper bound on this energy in
joules**. The current code supplies a numerical estimate and documented
diagnostics. Its finite-domain quadrature error is not yet a formally proved
enclosure. The exterior tail is part of the objective and cannot be discarded.

This energy functional is tied to the chosen slicing and observers. It is a
specified mathematical optimization target; it is not a demonstrated fuel or
power requirement for an engineered propulsion system.

The challenge fixes nominal speed at `beta = 2`, radial scale at `R = 20 m`,
profile steepness at `sigma = 1 m^-1`, and a `10 m` cabin radius. The smooth
published profile has an infinite tail and an approximately flat cabin. Do not
replace those descriptions with exact compact support or an exactly flat
interior. The paper reproduction uses its separate fiducial parameters and is
not an alternate setting for scoring candidates.

Candidate changes are exact rational polynomial perturbations of the scalar
potential within the prescribed shell. The trusted decoder fixes the basis,
support function, coefficient limits, and degree limit. Details and implemented
checks are in the benchmark contract and the scientific documentation linked
from `README.md`.

## 1. Reproduce the bootstrap

Run these commands from the repository root. Python `3.12.14` is the reference
interpreter; use an isolated environment with the pinned runtime dependencies.
These are local computations and do not publish anything.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.lock
python3 -m pip install --no-deps -e .
python3 -m unittest discover -s tests -v
python3 -m warpproof reproduce --output results/paper-reproduction.json
python3 -m warpproof evaluate candidates/rodal-baseline.json --output results/baseline.json
python3 -m warpproof render-data candidates/rodal-baseline.json --output web/default-result.js
```

The reproduction command checks the published family at its documented
fiducial parameters. The evaluation command computes the draft challenge's
baseline. Inspect the generated reports for numerical uncertainty, input
identity, and explicitly unproved conditions.

`src/warpproof/independent.py` provides a second calculation from metric samples
through the four-dimensional Christoffel symbols, Ricci tensor, and Einstein
tensor. Its refinement check compares `2*G(n,n)` with the reduced invariant.
It shares the metric's profile implementation, and its finite-difference
agreement remains a numerical diagnostic.

Run `npm run dev` and open http://127.0.0.1:4173 to inspect the scientific viewer.
Reviewed results are added through `records/history.json`; the viewer has no
import button. See `web/README.md` for generation and author attribution.
The vendored ES modules require this local HTTP server; no runtime network
dependencies or publication are involved. The interface always identifies this bootstrap as a numerical
preview with formal promotion unavailable.

If Node.js is available, the viewer's independent interface checks are:

```bash
node --check web/app.js
node web/validate-viewer.cjs
```

See `web/README.md` for the meaning of the displayed fields, reference contours,
coordinate frames, and supplied rays.

## 2. Confirm that certification is blocked

```bash
python3 -m warpproof verify --require-formal
```

**Expected outcome: exit status 2 and an explanation that formal promotion is
unavailable.** This is intentional. Do not change the command to return success
merely to make a workflow green. The CI test checks that the refusal remains in
place.

Read `docs/FORMALIZATION.md` for the exact scope of the included Lean code.
With the toolchain specified in `formal/lean-toolchain` installed, its separate
commands are:

```bash
cd formal
lake build
lake env lean Audit.lean
cd ..
```

These commands check the scoped formal component and its audit. They do not
certify the spacetime, the complete energy integral, or any candidate's global
admissibility. The promotion gate must remain closed until the full theorem
chain is connected.

## 3. Run a small exploratory search

```bash
python3 -m warpproof search --iterations 8 --output candidates/search-example.json
python3 -m warpproof evaluate candidates/search-example.json --output results/search-example.json
python3 -m warpproof render-data candidates/search-example.json --output results/search-example-viewer.json
```

Add the reviewed viewer JSON through `records/history.json`, then run
`python3 scripts/build_viewer_history.py`.
Compare it with the baseline using the same scale, field definitions, and
benchmark settings. A search may fail to find an improvement. Report the
actual result; never guarantee improvement or describe a numerical estimate as
a certified record.

If a candidate appears better, refine and independently check the numerical
calculation before spending substantial proof effort. If the uncertainty is
larger than the apparent improvement, the comparison is unresolved. Record
useful negative results and numerical instabilities with their input files.

## 4. Give Codex a concrete first assignment

Paste the following prompt into a coding agent with this repository open:

> Read AGENTS.md, README.md, CODEX_BOOTSTRAP.md, CONTRIBUTING.md,
> docs/RESEARCH_WORKFLOW.md, docs/FORMALIZATION.md, and tasks/backlog.json. Run
> the documented local checks and report the actual outputs. Choose the highest
> priority open task whose prerequisites you can satisfy. State the task ID,
> starting revision, exact acceptance criterion, and planned files. Work
> autonomously on that bounded task. Preserve the frozen draft benchmark and
> the fail-closed formal-promotion gate. Do not publish or contact anyone.
> Finish with a concrete artifact or a precise handoff, listing what is proved,
> what is only numerical, actual commands run, and remaining obligations.

For a team, assign different task IDs and avoid concurrent edits to shared
files. A useful first split is an independent GR derivation, continuous
admissibility specification, rigorous energy enclosure, and numerical
cross-checking. Search and visualization work can proceed while proofs mature,
provided that every result retains its numerical status.

## 5. Build the missing proof infrastructure in order

The highest-value work is not automatically more optimizer iterations. The
initial priorities are:

1. **Audit the published-model reproduction.** Verify the scalar potential,
   derivatives, units, observer convention, and fiducial comparison against the
   paper. Identify any transcription discrepancy before optimizing it.
2. **Establish the GR bridge.** Derive and formalize the connection between the
   specified metric and the Eulerian energy expression used by the evaluator.
   A proof of an unrelated algebraic expression is insufficient.
3. **Finish the continuous admission contract.** Specify and justify any cabin,
   stress, curvature, causal, or regularity constraints the challenge will
   promise. Current sampled diagnostics do not establish those properties over
   a continuum. A new or changed constraint requires an explicit benchmark
   version decision.
4. **Certify the whole-space energy bound.** Connect finite-region integration,
   absolute values, zero crossings, and the infinite tail to a rigorous global
   enclosure. Put external solvers behind a small checked certificate interface.
5. **Bind proofs to exact candidates.** Prove that decoded rational parameters,
   formal definitions, benchmark identity, and the published certificate all
   describe the same object.
6. **Enable promotion only after independent review.** The complete theorem
   must establish every promised admission condition and the energy bound.
   Make invalid or incomplete certificates fail before accepting a first record.

`tasks/backlog.json` breaks these phases into independently assignable tasks.
The detailed evidence states and promotion requirements are in
`docs/RESEARCH_WORKFLOW.md`.

## 6. Collaborate through GitHub

The private `Paureel/warpproof` repository includes issue templates, a PR
template, code ownership, agent guidance, and read-only GitHub Actions checks.
Invited contributors can follow `CONTRIBUTING.md` to work locally and submit a
reviewable change. Repository access does not publish or deploy the viewer.
Configure repository permissions and required reviewers in GitHub; a text file
cannot enforce those settings. Keep the benchmark, evaluator, formal gate, and
workflow changes under independent review.

Use the accepted benchmark version and exact source revision for scientific
review. Preserve past candidates and receipts. A merged exploratory PR can be
valuable without changing the selected scientific record or the certified
registry.
