# Ad Astra agent entry point

Read `AGENTS.md` first; it is the shared project guidance. Then read `README.md`,
`CONTRIBUTING.md`, and the task's relevant scientific documentation. The
machine-readable work queue is `tasks/backlog.json`.

This is a Python numerical evaluator, a scoped Lean proof library, and a static
HTML/JavaScript scientific viewer. Use Python 3.12.14, Node 22 (18+ supported),
and Lean 4.35.0. Run `make setup` for Python dependencies, then `make check`.
Run `make check-formal` when touching formal mathematics; it additionally needs
the pinned Lean toolchain on PATH. `npm run dev` starts a local-only viewer;
it needs no npm install. `npm run build` creates static `dist/` files.

Work on one bounded issue/backlog task per branch. Keep experiments in ignored
`results/local/` or `research/local/`. Submit exact candidate JSON and commands
that reproduce the result. The numerical evaluator and benchmark own the score;
candidate data must never replace them. Every current result is numerical only.
The explicit `verify --require-formal` refusal (exit 2) must stay in place.

Do not publish a website, change repository visibility, invite collaborators,
contact people, or push unrelated changes. Numerical tests and the small Lean
fixtures do not certify a complete warp geometry. Preserve authorship, source
citations, exact input identities, and unresolved proof obligations.
