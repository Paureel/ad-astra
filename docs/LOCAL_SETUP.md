# Local viewer setup

Task: local setup and scientific viewer redesign (WP-008-related display work;
the independent audit prerequisite and research task remain open).
Starting revision: empty `main` branch, with no commits. The supplied archive's
65 content hashes matched its original manifest before edits.

Acceptance: interactive 3D reference geometry and computed fields, an inspectable
history of actual supplied energy evaluations, common physical scales, local
JSON imports, responsive layout, and unchanged benchmark and promotion gate.
Primary changes: `web/`, local development/build scripts, documentation, and
release exclusions. Evaluator, benchmark, candidates, and formal proofs stay
bound to their original artifacts. Budget: local setup, bounded reproduction,
and browser QA; no research optimization or formal theorem development.

Run `npm run dev` and open http://127.0.0.1:4173. Node 18+ suffices. No npm
install is required. `npm run build` creates a static `dist/` directory for
possible future hosting; neither command publishes or contacts a host.

The numerical environment is in `.venv` with Python 3.12.14 and the supplied
`requirements.lock`. Activate it with `source .venv/bin/activate`.
The official Lean 4.35.0 macOS arm64 toolchain is installed under `.tools/`;
`make proof` selects it automatically. Its archive SHA-256 was verified against
the official release: `c0c6f34f35ba1dcc5c4a5fd106fefab9eb5e8469712624dd2c868d51b63177c2`.
`make test` also selects the local Python environment automatically.

Useful checks:

```sh
npm test
make test proof
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python formal/diagnostics/direct_ricci_check.py
.venv/bin/python -m warpproof verify --require-formal  # expected exit 2
```

Regenerate the bundled history after intentional updates to generated reports:
`python3 scripts/build_viewer_history.py`. The script checks that candidate,
energy, benchmark, and evaluator identity agree with their viewer artifacts.
The original receipts in `STATUS.json` describe the archive author's run.
This setup's actual checks are recorded separately in `results/local/`.

The requested interface uses a single full-screen scene, a floating selected
energy, and the saved evaluation timeline. Scientific details and exact
parameters are available through the provenance control. There is no dashboard
section layout, automatic hosting, or remote source synchronization.

Timeline follow-up: add the publication's original energy and author, attribute
the current repository entry to Paureel, resolve future contributor names from
Git metadata, and use logarithmic axes with hourly bins and date labels.
Starting revision is still uncommitted `main`. Scope: `records/history.json`,
the history bundler, `web/`, and attribution/mapping regressions. Publication
values and dates were checked against the pinned paper and publisher. The
numerical evaluator, frozen benchmark, candidate bytes, and formal gate were
not changed. Literature and benchmark results retain their separate meanings.
