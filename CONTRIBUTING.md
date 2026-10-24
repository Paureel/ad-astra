# Contributing

Research, candidate geometries, optimizers, proofs, independent audits, viewer
improvements, and documentation are welcome. A useful contribution need not set
an energy record. Follow our [community conduct](CODE_OF_CONDUCT.md).

## Start a contribution

The repository is private. Ask the owner for access, then clone it and create a
branch for one issue or [backlog task](tasks/backlog.json). Use `codex/` for agent
branches, or `research/`, `fix/`, and `docs/` for other work.

```sh
git clone https://github.com/Paureel/ad-astra.git
cd ad-astra
git switch -c codex/your-task
npm run dev
```

The local viewer needs Node 18+ and no npm install. Numerical work also needs
Python 3.12: run `make setup`. Proof work needs the pinned
[Lean toolchain](formal/README.md). See [local setup](docs/LOCAL_SETUP.md).

Check issues and PRs for overlap. Record your starting commit, scope, and
acceptance test. Keep experiments in ignored `results/local/` or
`research/local/`; preserve the checked-in reference results. Never commit local
environments, credentials, archives, or personal agent state.

## Validate and submit

| Change | Checks |
| --- | --- |
| Viewer | `npm test` and `npm run build` |
| Numerical code or candidate | `make check` plus the relevant reproduction commands |
| Formal code | `make check-formal` |
| Documentation or templates | Check links, commands, and formatting |

For every source change, refresh and verify the source manifest:

```sh
make manifest
python3 scripts/package_release.py --verify-manifest
git diff --check
```

Review the diff, commit the intended files, push your task branch, and open a PR
against `main`. Use the PR template to describe the result and actual validation.
Scientific fields are optional for unrelated tooling or documentation changes.
GitHub Actions checks the submitted code, separately replays candidate data with
the base evaluator, and builds and audits the scoped Lean library.

Changes to the benchmark, evaluator, formal gate, dependencies, or workflows
need independent review. [CODEOWNERS](.github/CODEOWNERS) identifies the maintainer;
the current GitHub plan does not enforce protected branches for this private
repository, so the review policy must be followed manually. Passing CI does not
certify a scientific claim or promote an energy record.

## Scientific contributions

Keep the frozen benchmark unchanged when claiming an improvement. A different
speed, cabin, geometry family, objective, or admission rule requires a separately
reviewed benchmark version. Candidate files are data, never replacement scorers.

Include exact parameters, benchmark and evaluator revision, units, provenance,
reproduction commands, and unresolved uncertainty. Put candidate JSON directly
in `candidates/` (64 KiB per file; at most 32 changed candidates per bounded PR
replay). Credit prior work and substantial AI assistance.

Proofs must state their assumptions, axiom dependencies, and connection to the
actual continuum claim. Preserve the formal gate’s refusal until the complete
required theorem chain is checked. Numerical agreement, sampled constraints,
and a compiling Lean fixture are not formal certification. The evidence states
and promotion rules are defined in [the research workflow](docs/RESEARCH_WORKFLOW.md).

Viewer work must preserve units, common scales, frame, provenance, and evidence
status. Document numerical approximations and measured performance. For new
history entries, follow [the history workflow](web/README.md), run `npm run data`
to update the app and README timeline, then `make display-data` for calculated
geometry and optics. Reviewed historical records stay intact.

## Working with an agent

Start with [AGENTS.md](AGENTS.md). A useful assignment states the task, starting
commit, concrete acceptance test, and intended files. Finish with the actual
commands, outcomes, credits, and remaining obligations so another contributor
can continue. Keep website previews local. Remote pushes, PRs, invitations, and
publication require the human’s authorization for the session.

## Contribution license

Unless explicitly stated otherwise and agreed with the maintainer, contributions
intentionally submitted for inclusion use [Apache 2.0](LICENSE). Contributors
retain their copyright. Preserve original and third-party notices, including
[the MIT bootstrap notice](licenses/WarpProof-bootstrap-MIT.txt) and the vendored
[Three.js license](web/vendor/THREE-LICENSE.txt). See [NOTICE](NOTICE).
