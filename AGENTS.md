# Instructions for collaborating agents

Read `README.md`, `CODEX_BOOTSTRAP.md`, `CONTRIBUTING.md`, and
`docs/RESEARCH_WORKFLOW.md` before starting substantive work. The machine-readable
task backlog is `tasks/backlog.json`. These instructions apply throughout this
repository.

## Local entry points

- Read `CONTRIBUTING.md` for the short community/agent workflow.
- `make setup` installs the pinned Python dependencies in `.venv`; Python 3.12
  is needed to create a new environment. `make check` runs Python and viewer
  checks, builds the static viewer, and checks the intentional refusal gate.
- `make check-formal` additionally builds and audits Lean 4.35.0. The Lean
  installation is separate; instructions are in `formal/README.md`.
- `npm run dev` is a local preview; no npm install or website deployment is
  needed. Keep website hosting disabled unless the human explicitly requests
  it for that task. Repository publication does not authorize website hosting.
- Use one task branch per contribution (`codex/<task>` for agent work). Keep
  scratch output in ignored `results/local/` or `research/local/`.
- Refresh source hashes with `make manifest` after intentional edits. Never
  include local environments, credentials, archives, or personal agent state.

## Scientific objective

Improve the energy objective for the frozen benchmark while satisfying every
benchmark constraint. The chosen spacetime family, observer, spatial slice,
units, speed, payload region, regularity requirements, and integration domain
are part of the problem. Changing them creates a different benchmark; it does
not improve an existing record.

This bootstrap contains mathematical models and numerical checks. Report the
scope of each result accurately. A low numerical energy estimate, a smooth
animation, an Einstein tensor calculated from a proposed metric, or a passing
CI run is not a proof that a physical propulsion system can produce that metric.

## Begin a task

1. Read the current task backlog and candidate records. Choose one concrete
   question with a clear acceptance test. Prefer an existing open task.
2. Record the task identifier, the starting commit, and the files you intend to
   change. Coordinate overlapping edits with other agents. A task claim is
   advisory and does not establish priority or validate a result.
3. Use an isolated branch or worktree when another contributor is editing the
   same files. Preserve their work and the current benchmark records.
4. Set a reasonable time and computation budget. A counterexample, a smaller
   proof obligation, or a documented obstruction is a useful contribution.

## Preserve the trust boundary

- Candidate parameters are data. Do not let a candidate replace the evaluator,
  import executable code, redefine units, or override the benchmark contract.
- Keep the numerical search, independent numerical validation, formal proof,
  and physical interpretation distinct. Use only the statuses defined in
  `docs/RESEARCH_WORKFLOW.md`.
- Do not edit the objective, constraints, tolerances, sampling rules, reference
  constants, or admission rules to make a candidate pass. Propose a separately
  reviewed benchmark version if a definition needs correction.
- Do not manufacture proofs, error bounds, citations, execution receipts,
  timestamps, or certificates. Explicitly report commands that were not run.
- A formal build is necessary but not sufficient for certified promotion. The
  theorem must cover the candidate, the energy bound, every admission condition,
  and the derivation connecting the benchmark to its stated geometry.
- Do not use `sorry`, `admit`, unchecked evaluation, or a new axiom to discharge a
  required certification obligation. Record the axiom dependencies of the final
  theorem and review them against the project's documented trust policy.
- Preserve a failing promotion gate until every required proof obligation is
  closed. Do not turn an unimplemented proof check into a successful stub.

## Make results reproducible

- Keep submitted parameters exact, normally as rational numbers. Convert to
  floating point only inside explicitly numerical computations.
- Bind generated output to the exact candidate bytes, benchmark identity, and
  evaluator version. Regenerate output after changing any input.
- Treat rendered images and viewer data as derived artifacts. Never adjust a
  reported score or simulation field manually to improve presentation.
- Keep citations to the original papers and official mathematical/software
  sources. Distinguish reproduced results from new derivations and conjectures.
- Run the relevant existing checks. Add a test only for a real mathematical
  identity, boundary condition, parser failure, or regression risk.
- State remaining limitations and proof obligations in the handoff, including
  discretization error that has not been rigorously bounded.

## Work autonomously within the assignment

Local, reversible research and implementation work can proceed without repeated
confirmation. Do not publish a repository, open a remote PR, post a message,
change remote settings, or deploy a viewer unless the user has authorized that
external action. Do not put credentials or private data in this shared research
project. Dependency installation and remote access remain subject to the
execution environment's permissions.

At the end of a task, summarize what changed, what the evidence establishes,
which commands ran, which checks did not run, and the next smallest useful task.
