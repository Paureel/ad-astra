# Contributing

The project accepts geometry candidates, optimizers, mathematical proofs,
independent audits, counterexamples, numerical improvements, and visualization
work. A contribution need not set an energy record to be useful.

Start with `CODEX_BOOTSTRAP.md` for the executable setup and first tasks. Read
`docs/RESEARCH_WORKFLOW.md` for the meaning of each result status.

## First contribution

While the repository is private, ask the owner for access before cloning.
Invited contributors can push their own branches and open PRs against `main`;
there is no need to change visibility. If working from a permitted fork, use
the same PR process with `main` as the base branch.

```bash
git clone https://github.com/Paureel/warpproof.git
cd warpproof
make setup
make check
git switch -c codex/wp-001-reproduction-audit
```

Choose a branch name for your actual task. Use `codex/` for agent work and
`research/`, `fix/`, or `docs/` for other contributions. Check existing issues
and PRs for overlap, then read the corresponding entry in `tasks/backlog.json`.
WP-001 and WP-005 have no backlog prerequisites. A viewer or documentation
improvement can also be a narrowly scoped contribution; do not mark an
independent scientific audit complete on the strength of a UI change.

Keep scratch calculations and bulky traces in ignored `results/local/` or
`research/local/`. Keep local toolchains, API keys, `.env` files, and personal
agent state out of commits. Preserve the checked-in reference results. New
candidates and reviewed evidence belong in their documented source locations.

Before the PR, run `make check`; run `make check-formal` for proof changes and
the relevant reproduction commands for numerical changes. Run `make manifest`
after source edits, review `git diff`, and commit the intended files. Then
push the task branch and open a PR using the supplied template. PR creation
and pushing require the human's authorization for the agent's session.

GitHub Actions runs submitted-code checks, a separate base-evaluator replay of
candidate data, and the scoped Lean build and axiom audit. Passing CI is
evidence of those checks, not formal record promotion. Core trust boundaries
have maintainer ownership in `.github/CODEOWNERS`.

## Give an agent a bounded assignment

Copy this into your coding agent and replace the task identifier:

> Read AGENTS.md, README.md, CONTRIBUTING.md, and tasks/backlog.json. Work on
> WP-001, or explain a missing prerequisite before choosing another bounded
> task. Record the starting commit and acceptance test. Make a local task
> branch, implement the scoped change, and run the relevant checks. Preserve
> the fixed benchmark, source provenance, and fail-closed formal gate. Prepare
> a concrete PR-ready diff and a handoff with commands, outcomes, credits, and
> remaining obligations. Do not publish a website or contact anyone. Ask for
> authorization before pushing or opening a remote PR if this session has
> not already granted it.

`AGENTS.md` is the shared guidance; GitHub Copilot also has a short entry point
in `.github/copilot-instructions.md`. Commit author identity and AI assistance
must be accurate. Timeline metadata can bind an entry to a contributor's full
Git commit hash; see `web/README.md`.

## Before substantial work

Choose an item from `tasks/backlog.json` or propose one concrete research
question. Check open issues and PRs when working in a hosted copy. Record your
starting commit and coordinate changes to shared files. Existing work and
attribution should be preserved, including useful failed approaches.

The frozen benchmark is the comparison contract. Improvements must use the same
spacetime family, speed, payload size, observer convention, energy functional,
and constraints. A change to any of those belongs in a separate proposal for a
new benchmark version.

## Candidate contributions

Submit a parameter file in the accepted data format, together with:

1. A short claim stating exactly what is new.
2. The benchmark identifier and exact source commit used for evaluation.
3. Exact coefficients, units, and provenance for the parameter choice.
4. Reproduction commands and the generated numerical report.
5. The proof or certificate needed for any claimed certified result.
6. Any remaining obligations, failed checks, or uncertain interpretation.

An optimizer may be arbitrary research code. Its output must pass through the
repository-owned evaluator. A candidate cannot supply its own scoring function,
substitute a mesh for the continuous geometry, or set its own admission rules.

Put replayable candidate JSON files directly in `candidates/`. The current
decoder limits each file to 64 KiB. The bounded PR replay checks the baseline
and at most 32 changed candidate files; unchanged archived candidates are not
all rerun on every PR. Keep large optimizer traces outside this input directory.

## Proof contributions

State the theorem in the repository's benchmark definitions. A proof of a
related formula or a finite sampled condition is useful, but does not close a
different continuous obligation. Document the theorem's assumptions, axiom
dependencies, and relationship to the geometry and energy functional.

For certificates generated by external solvers, the solver is an untrusted
producer. The trusted proof checker must reconstruct or check the certificate.
Floating-point agreement with a proposed theorem is supporting evidence; it is
not a replacement for a proof of that theorem.

Never replace an outstanding proof obligation with an axiom, `sorry`, `admit`,
an unchecked evaluator, or a successful placeholder. The certification gate must
continue to fail until the complete promised theorem has been checked.

## Numerical and viewer contributions

Explain the numerical error being controlled, the resolution or order used,
and how results behave under refinement. An independent implementation should
avoid sharing the same derivation or computational shortcut when that would
hide a common error.

Viewer changes must preserve physical axes, scale conventions, field units,
legends, and result status. A spaceship is a visual scale marker unless a
payload model is explicitly included in the benchmark. Screenshots and
animations must identify the candidate and benchmark from which they were
generated.

## Review and acceptance

Use the PR template. List actual commands and outcomes, not a general statement
that tests passed. Mark commands not run. Review applies to an exact commit;
changing proof-relevant files invalidates affected results and requires replay.

CI checks on a submitted branch are useful evidence. They do not themselves
promote a candidate or authorize changes to the benchmark. A reviewer must
confirm that the evaluator and contract used for the scientific claim are the
approved versions, especially when a PR also modifies evaluation code.

Archiving or merging a research contribution does not mean that its scientific
claims have been certified. Only the explicit admission and promotion process
can create a certified record. The initial bootstrap deliberately has no
certified warp-drive record.

The future leaderboard ranks certified energy upper bounds. Its strict-record
promotion rule additionally requires `new_upper < old_lower`, after admission
is proved for both candidates. A tighter upper bound can be useful without
qualifying as a strict record. Overlapping intervals remain unresolved for
record replacement and must not be described as a proved energy reduction.

## Attribution and handoffs

Credit the people, agents, papers, prior candidates, and reusable proof work
that materially contributed. Describe substantial AI assistance plainly. A
handoff should identify a concrete next question, why it matters, its smallest
feasible first step, and any blocker. Keep historical claims and their evidence
intact rather than rewriting them as if later corrections were already known.
