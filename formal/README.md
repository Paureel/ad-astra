# Lean bootstrap: exact arithmetic only

This directory builds with **Lean 4.35.0**, with no external Lake packages.
It has been compiled locally, including the axiom audit. It does **not** certify
the Einstein-tensor derivation, the numerical energy integral, or an admissible
warp-drive candidate. A successful build must not change
`formal_certification: false` or turn numerical scores into certified bounds.

From this directory, with the pinned toolchain available:

```sh
lake build
lake env lean Audit.lean
```

The first command kernel-checks the theorem files. The second audits the
transitive axiom dependencies of the 18 listed theorems and fails on anything
outside `propext`, `Classical.choice`, and `Quot.sound`. Those are standard Lean
foundations. Custom axioms, `sorryAx`, and native-evaluation trust extensions
are not allowed. Closed examples use `decide +kernel`; algebraic identities
use proof-producing `grind`.

## Toolchain provenance

- Release: <https://github.com/leanprover/lean4/releases/tag/v4.35.0>
- Linux x86-64 archive:
  <https://github.com/leanprover/lean4/releases/download/v4.35.0/lean-4.35.0-linux.tar.zst>
- Archive SHA-256:
  `7289597a44543246c9227b8cae501767e095ce17f6d448b95fc4a8dc97268f6d`
- Compiler commit reported by `lean --version`:
  `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`

Use a fresh official archive or an existing trusted toolchain installation.
Do not execute a toolchain supplied by a contestant. The ZIP intentionally
does not contain the compiler or generated `.lake` build files. On Linux,
extract the archive with `tar --no-same-owner --zstd -xf ARCHIVE` and make its
`bin` directory available to the build. The `lean-toolchain` file also works
with an existing Elan installation.

## What is proved

- The canonical monomial list contains nine terms of weighted degree at most 4.
- The exact rational coefficient checker implies every coefficient lies in
  `[-1/10, 1/10]`.
- Conditional addition, nonnegative scaling, and remainder widening of rational
  intervals preserve containment of rational values.
- Disjoint ordered intervals imply strict ordering of their contained values.
- The symmetric-Hessian and radial-reduction algebraic identities hold over
  the rationals.
- The formal polynomial `[4s(1-s)]^6` and its first five formal derivatives
  vanish at both endpoints.

These statements are useful building blocks. They do not assert that the
program's floating-point output encloses a real integral. The synthetic
interval examples are arithmetic fixtures, not joule measurements.

## What still needs proof

Read [the formalization contract](../docs/FORMALIZATION.md) before adding a
certificate path. In particular, a full record needs a real-analysis library,
the metric-to-energy theorem, exact candidate binding, global admissibility
certificates, certified quadrature, and a proved analytic tail enclosure.
No unimplemented obligation is represented by a `sorry` or an added axiom.

## Independent diagnostic

From the repository root:

```sh
python formal/diagnostics/direct_ricci_check.py
```

This standard-library-only diagnostic computes the full 4D Einstein contraction
at exact rational polynomial sample points and compares it with the Hessian
invariant. It also checks the radial reduction and an angular perturbation.
It uses a different calculation path from the scorer. Point checks help catch
signs and factors, but do not prove a continuum identity.

