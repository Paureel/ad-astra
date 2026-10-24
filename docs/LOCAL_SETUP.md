# Local setup

Clone the repository after receiving access, then run commands from its root.
Node 18+ runs the viewer. Numerical checks use Python 3.12 and the pinned
`requirements.lock`. On Windows, use WSL for the full Makefile workflow.

## Viewer

```sh
npm run dev
```

Open <http://127.0.0.1:4173>. Bundled results work without Python, npm install,
a CDN, or an API key. `npm run build` writes a static viewer to `dist/`, including
its license and attribution files. These commands do not publish the site.

## Numerical environment

```sh
make setup
make check
```

`make setup` creates `.venv` with Python 3.12 and installs the pinned dependencies.
If Python has another executable name, use `make setup BOOTSTRAP_PYTHON=/path/to/python3.12`.
The Python module and CLI retain the name `warpproof` for compatibility.
Use `.venv/bin/python -m warpproof --help` to see the research commands.

Keep experiments in ignored `results/local/` or `research/local/`. Preserve
reference candidates and reports. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Formal checks

Install the pinned Lean toolchain using [formal/README.md](../formal/README.md),
then run `make check-formal`. The checked Lean lemmas have a limited scope;
the formal-promotion command deliberately refuses incomplete certification.

## Regenerate data

After a reviewed history update:

```sh
npm run data
make display-data
make manifest
```

The history bundler checks candidate, energy, benchmark, and evaluator identity
against the saved reports. `npm run data` refreshes the app history and README
SVG timeline. The README figure uses the viewer’s same hourly log/log projection;
`npm test` rejects a stale figure. Full Git history is needed when contributor
attribution names an exact earlier commit. `make display-data` regenerates the
calculated surfaces, density, and reference sky from the saved inputs.

For contribution-specific checks and the PR workflow, see
[CONTRIBUTING.md](../CONTRIBUTING.md). For scientific interpretation, see
[the research workflow](RESEARCH_WORKFLOW.md) and [viewer documentation](../web/README.md).
