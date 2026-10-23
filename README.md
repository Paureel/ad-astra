# Ad Astra: a fixed 2c source-energy challenge

A collaborative mathematical research repository for reducing one quantity:
**the whole-space absolute Eulerian source energy, in joules, of a fixed
superluminal warp-geometry benchmark**.

The selected published reference is José Rodal's smooth irrotational geometry,
[arXiv:2512.18008v1](https://arxiv.org/abs/2512.18008v1), published as
[DOI 10.1007/s10714-025-03495-x](https://doi.org/10.1007/s10714-025-03495-x).
The challenge instantiates that family at **2c**, with a **10 m proper cabin
radius**, a **20 m profile radius**, and `sigma = 1 / m`.

## Join the work

The repository is private during bootstrap. Invited contributors can work on
branches and open pull requests; access does not require making the project
public. Human and agent contributions follow the same reproducibility rules.

```bash
git clone https://github.com/Paureel/ad-astra.git
cd ad-astra
make setup          # Python 3.12 installed; creates an isolated .venv
make check          # Python + viewer checks, static build, certification refusal
npm run dev         # local viewer; no npm dependencies to install
```

Node 18+ and Python 3.12 are needed for the full checks; Node alone runs the
viewer. Lean 4.35.0 is separate: see [formal/README.md](formal/README.md), then
run `make check-formal` for proof changes. On Windows, use WSL or run the Python
and npm commands directly. No command in this quickstart deploys a website.

Start with [CONTRIBUTING.md](CONTRIBUTING.md),
[AGENTS.md](AGENTS.md), and the machine-readable [task backlog](tasks/backlog.json).
Pick one bounded task, preserve exact inputs, and include a concrete handoff.
The existing issue and PR templates capture scientific evidence and authorship.

Ad Astra continues the supplied WarpProof bootstrap. The `warpproof` Python
module and command, Lean namespaces, and browser history keys stay compatible
with existing scripts and scientific receipts.

## Current result and exact scope

| Item | Bootstrap state |
| --- | --- |
| Benchmark | `rodal-2c-v1-draft` |
| Numerical reference energy | approximately **4.250080505 × 10^45 J** |
| Exterior domain | all of space, including the analytic asymptotic tail |
| Search space | nine bounded rational coefficients in a compact scalar-potential perturbation |
| Numerical evaluator | working Python implementation with refinement and an independent 4D tensor check |
| Scientific viewer | local 3D geometry, computed density slices, sampled null-ray replay, ideal annihilation mass comparison |
| Formal component | compiled Lean 4.35.0 arithmetic and polynomial lemmas with an axiom audit |
| Certified energy records | **none** |
| Promotion gate | **disabled**, `verify --require-formal` exits 2 |

The energy is a specified stress-energy integral in a fixed frame. It is not a
demonstrated fuel budget, construction cost, or proof that a material system can
produce this spacetime. The model is an eternal, prescribed moving geometry.
Bubble formation, acceleration, shutdown, matter dynamics, quantum restrictions,
and operational control are outside this draft's claims.

The project is ready to bootstrap research in Codex. It is not yet a complete
proof-checked physics benchmark. The missing proof obligations are explicit,
and no successful numerical or Lean fixture test can promote a record.

## Start in Codex

Open this directory and read [CODEX_BOOTSTRAP.md](CODEX_BOOTSTRAP.md). It contains
a ready-to-paste agent assignment and parallel research tasks. All agents should
also follow [AGENTS.md](AGENTS.md).

From the repository root, using Python 3.12:

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

Run `npm run dev` and open http://127.0.0.1:4173. The viewer includes generated
baseline and search data, so it works before Python is installed. It needs only
Node 18+; no npm install, account, API key, CDN, or deployment is required.
`npm run build` prepares static files in `dist/` for future hosting.
See [local setup](docs/LOCAL_SETUP.md).

The reference environment uses Python **3.12.14**, NumPy **2.3.5**, and SciPy
**1.17.0**. Runtime dependencies are pinned. The pinned Lean toolchain is
separate; see [formal/README.md](formal/README.md).

## The objective

For comoving spatial coordinates `q` and `u = ct`, the metric is

\[
ds^2=-du^2+|d\mathbf q+\nabla\Phi(\mathbf q)du|^2.
\]

Let `K = Hess(Phi)` and let `n` be the unit future normal to the fixed spatial
slices. The challenge minimizes

\[
\boxed{E_{\rm abs}=\int_{\mathbb R^3}|\rho_E|\,d^3q},
\qquad
\rho_E=\frac{c^4}{16\pi G}
\left[(\operatorname{tr}K)^2-\operatorname{tr}(K^2)\right].
\]

The signed integral is unsuitable as a score: positive and negative terms
cancel in this family even when their individual magnitudes are enormous.
Absolute energy counts both. `positive_J`, `negative_J`, and other diagnostics
are explanatory outputs, not additional objectives.

A future official entry must prove `L <= E_abs <= U` and all admission
conditions. Its score will be `U` in joules. A strict replacement requires
`U_new < L_old`. There is no certified reference interval in this bootstrap.

## Try the working search

```bash
python3 -m warpproof search --iterations 8 --output candidates/search-example.json
python3 -m warpproof evaluate candidates/search-example.json --output results/search-example.json
python3 -m warpproof render-data candidates/search-example.json --output results/search-example-viewer.json
```

For an exploratory run, write outputs under ignored `results/local/` instead of
overwriting the included examples. To add a reviewed result to the viewer,
follow the history manifest workflow in [web/README.md](web/README.md).
This is a small reproducible coordinate search. It can seed
better optimizers, but it does not certify global admissibility or a record.
An included example perturbation is a schema demonstration, not an improvement
claim.

Only the coefficient JSON is a search submission. The decoder fixes the
geometry, constants, support window, speed, cabin, asymptotics, objective,
degree bound, and coefficient limits. Altering those definitions needs a new,
separately reviewed benchmark version.

## Why this published baseline?

The Rodal family has a smooth origin, explicit potential and derivatives, a
tractable energy reduction, published energy tables for reproduction, and a
retained exterior tail. Those properties make it suitable for a proof-oriented
starter. Selecting it does not assert a universal lowest-energy result among
all warp metrics. The benchmark's larger, faster instance is clearly separated
from the paper's original parameter choice. Read [BASELINE.md](docs/BASELINE.md)
for the selection and numerical comparison.

## Validation and collaboration

| Area | Entry point |
| --- | --- |
| Frozen draft problem | [benchmarks/rodal-2c-v1.json](benchmarks/rodal-2c-v1.json) |
| Published baseline and reproduction | [docs/BASELINE.md](docs/BASELINE.md) |
| Mathematical definitions and numerical methods | [docs/MATHEMATICS.md](docs/MATHEMATICS.md) |
| Implemented gates and limitations | [docs/VALIDATION.md](docs/VALIDATION.md) |
| Lean scope and missing proof bridges | [docs/FORMALIZATION.md](docs/FORMALIZATION.md) |
| Task selection and evidence states | [docs/RESEARCH_WORKFLOW.md](docs/RESEARCH_WORKFLOW.md) |
| Contribution process | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Machine-readable task queue | [tasks/backlog.json](tasks/backlog.json) |
| Scientific display semantics | [web/README.md](web/README.md) |
| Included execution receipt | [STATUS.json](STATUS.json) |
| Source bibliography | [SOURCES.json](SOURCES.json) |

GitHub Actions includes ordinary submitted-code checks, a separate base-evaluator
replay of data-only submissions, and scoped Lean builds. These jobs have read-only
permissions and do not publish results or promote records. Maintainers must
configure their own review and branch-protection policies when hosting the repo.

The collaboration pattern takes inspiration from
[CrocSwap/integer-mult-bounds](https://github.com/CrocSwap/integer-mult-bounds):
concrete tasks, exact inputs, reproducible evidence, scoped proof claims, and
preserved records. No upstream code or endorsement is included.

## Archive integrity

`MANIFEST.sha256` identifies the included source files. After intentional edits,
run `make manifest`, then verify with
`python3 scripts/package_release.py --verify-manifest`. Run
`python3 scripts/package_release.py` to create `build/ad-astra-source.zip`.
Packaging honors `.gitignore` in a checkout and excludes local environments,
credentials, caches, and scratch research. No Git history or remote
configuration is bundled.

