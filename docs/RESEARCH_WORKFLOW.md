# Research, validation, and promotion

## One objective, a fixed comparison contract

The research objective is to reduce the benchmark's stated energy quantity
while preserving all of its admission conditions. The benchmark contract fixes
the geometry family, coordinate and observer convention, superluminal speed,
payload dimensions, energy integral, and admissibility requirements.

Keep the contract independent of the candidate. Submissions may optimize the
parameters the contract exposes. They may not change a boundary condition,
relax a bound, reinterpret a metre, or move energy outside the integration
domain. A useful extension to the geometry family is a new benchmark version
with a fresh baseline and an explicitly separate history.

The benchmark's energy is a mathematical functional of a specified spacetime.
Even a complete proof of a low value would leave questions about physically
producing its required stress-energy, preparing the spacetime, and controlling
the journey. Those claims are outside the present leaderboard contract.

## Evidence states

These are evidence categories, not interchangeable badges. The bootstrap's
machine-readable evaluator and viewer report `numerical_only`. The other rows
describe the collaboration process and the intended future promotion scheme.

| State | Evidence established | What can be claimed |
| --- | --- | --- |
| Draft | Parameters or a proposed argument exist | A candidate or conjecture |
| Numerical only | The repository evaluator has computed the documented diagnostics | Numerical results for the stated model and resolution |
| Independently reproduced | Another implementation or researcher has reproduced a defined numerical or mathematical claim | The exact claim reproduced, with its remaining limitations |
| Formally certified | A trusted checker has verified the complete admission theorem and energy bound against the approved contract | A proved bound within that benchmark and its stated assumptions |
| Rejected or superseded | A failed condition or a replacement is documented | A useful negative result or historical record |

There are no formally certified candidates in this bootstrap. Importing JSON,
building a small Lean example, or marking a task complete cannot change that.
The formal-promotion command intentionally rejects every candidate until a
complete certification path exists.

## Candidate to reproducible result

1. **Submit exact data.** Record the candidate, its provenance, the benchmark
   identifier, and the evaluator revision. Parameters should have an exact
   rational representation even if the numerical implementation uses floats.
2. **Validate the representation.** Reject missing fields, invalid types,
   non-finite numbers, unsupported families, and unauthorized contract changes.
   Validate all claimed boundary matching and shape constraints at the level
   the implementation actually supports.
3. **Compute the energy and fields.** Use the repository-owned evaluator, the
   benchmark's units, and the prescribed volume element. Calculate the entire
   energy objective, including any permitted exterior tail.
4. **Check the calculation independently.** Compare analytic or exact results
   with a different numerical formulation and refine the discretization. A
   small residual is a diagnostic unless an error theorem turns it into a bound.
5. **Record limitations.** Identify continuous conditions that were only
   sampled, unsupported stress-energy properties, unproved error bounds, and
   missing proof obligations. A passing local check does not establish an
   unimplemented global condition.
6. **Render the same candidate.** Generate viewer data from the same numerical
   evaluation and source digest. Include axes, units, field definitions, frame,
   and evidence status. The viewer may interpolate for display; interpolation
   does not redefine the score.
7. **Review an exact revision.** Preserve the input files, commands, environment,
   evidence receipts, and attribution. Changing an input invalidates dependent
   evidence and requires replay.

For a data-only candidate PR, the provided workflow checks out the base
evaluator and submitted data separately, then uses the base evaluator for a
bounded candidate replay. Another job checks the submitted software revision.
Executing a PR's modified scorer only establishes what that scorer did. The
workflow itself still needs review when it changes. These jobs are software and
reproducibility checks; they do not implement scientific promotion.

## Formal certification roadmap

Lean is useful as a small trusted checker for well-specified mathematics. It
does not supply an automatic general-relativity acceptance test merely because
a project compiles. The following chain must be connected before certification
can be enabled:

| Obligation | Required result |
| --- | --- |
| Parameter identity | The formal candidate is exactly the submitted data, with the same units and benchmark identity. |
| Profile conditions | Required smoothness, support or tail conditions, boundary values, and any shape inequalities hold over the full domain. |
| Geometry definition | The metric is well-defined with the benchmark signature and intended coordinate and observer conventions. |
| Stress-energy derivation | The chosen conventions lead from the metric to the claimed Einstein tensor and observer energy density. |
| Integral reduction | The continuum volume integral equals the one used for the candidate's score, including every domain and boundary contribution. |
| Admission conditions | Every constraint the benchmark promises is proved, rather than checked at a finite set of sample points. |
| Energy bound | The exact integral or a rigorously enclosed value yields the submitted upper bound. |
| Artifact identity | The proof result, candidate, benchmark, and published record are bound to one checked set of inputs. |

A proof may establish a uniform theorem for a family and instantiate it for
each candidate. This avoids rebuilding tensor calculus for every parameter
change. Exact polynomial arithmetic and checked interval certificates are
promising interfaces for this approach. Their use still requires a theorem
linking the checked quantities to the continuum benchmark.

The axiom dependencies of the final theorem must be inspected. Standard
foundational axioms used by the selected proof environment should be documented;
the target energy inequality or a missing physics derivation must never be
silently introduced as an axiom. Solver logs and unchecked native calculations
cannot substitute for a kernel-checked proof object.

## Future leaderboard rule

Use a certified upper bound in joules as the single ranked value once full
certification is available. Each certified candidate must also supply its
proved lower bound, so the viewer can show the enclosure and later candidates
can be compared strictly. Keep numerical previews in an explicitly named
exploratory list until then.

A smaller certified upper bound improves the stated bound, but strict-record
promotion requires `U_new < L_old` as well as admission proofs. This separates
the actual candidate energies. A bound refinement with overlapping intervals
remains useful evidence without replacing the certified record.

Every accepted row should link to the candidate digest, benchmark version,
proved bound, proof-checker version, axiom report, reproduction command,
independent replay, source papers, contributors, and predecessor record.
Historical entries should remain inspectable after a new record appears.

Use the acceptance date on a benchmark progress plot. Literature claims belong
in a separately labelled dataset because their speeds, payload sizes,
stress-energy definitions, assumptions, and proof status may differ. A
literature publication date is not an acceptance date for this benchmark.

## Parallel work for people and agents

Use `tasks/backlog.json` as the shared task catalogue. Each task names a concrete
acceptance test and its prerequisites. Useful roles include:

- **Searcher:** proposes exact candidates and records unsuccessful regions.
- **Prover:** closes a specific mathematical obligation.
- **Verifier:** checks a claim through an independent derivation or implementation.
- **Maintainer:** reviews the evidence, versions the contract, and preserves records.
- **Visualization contributor:** makes the verified fields and limitations legible.

One person or agent can fill several roles, but independence should be described
honestly. Two runs of the same implementation are repeatability evidence;
they are not independent implementations. Task claims help coordination and
should not prevent another contributor from finding a different approach.

An agent handoff should state: the task and starting commit, the exact question,
what was established, actual commands and outputs, remaining obligations, and
the smallest useful next step. Archive useful counterexamples and failed
searches with their scope. Do not count a search timeout as an impossibility
proof.

## Public GitHub operation

The supplied PR workflow uses read-only repository permissions and does not
publish records, deploy a site, open PRs, or access repository secrets. It does
not use `pull_request_target` to execute submitted code. It retains numerical
reports as CI artifacts and compiles the scoped Lean component using a pinned,
digest-checked toolchain archive. Hosted contributors' code still runs in a
disposable CI runner, and passing that job does not confer scientific authority
on a modified evaluator.

When hosting this project, maintainers should require review for changes to the
benchmark, evaluator, formal gate, and workflow. Protect the branch that defines
approved benchmark versions. Repository settings and reviewer identities are
host-specific, so this archive does not pretend to configure them.

The collaboration pattern is inspired by
[`CrocSwap/integer-mult-bounds`](https://github.com/CrocSwap/integer-mult-bounds),
especially its
[research packages](https://github.com/CrocSwap/integer-mult-bounds/blob/main/docs/research/research-package-guide.md),
[contribution policy](https://github.com/CrocSwap/integer-mult-bounds/blob/main/CONTRIBUTING.md),
and
[selected-result manifest](https://github.com/CrocSwap/integer-mult-bounds/blob/main/certificates/selected-result.json).
That repository itself distinguishes scoped certificates from a complete formal
proof. This project keeps the same distinction explicit.
