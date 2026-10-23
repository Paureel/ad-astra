import WarpProofBootstrap
import Lean
import Lean.Util.CollectAxioms

/-! Fail if a listed theorem transitively uses a nonstandard axiom. -/

open Lean Elab Command

run_elab do
  let allowed : Array Name := #[``propext, ``Classical.choice, ``Quot.sound]
  let checked : Array Name := #[
    ``WarpProofBootstrap.monomial_count,
    ``WarpProofBootstrap.monomial_degrees,
    ``WarpProofBootstrap.checkCoefficient_sound,
    ``WarpProofBootstrap.checkCoefficients_sound,
    ``WarpProofBootstrap.enclosure_add,
    ``WarpProofBootstrap.enclosure_scale,
    ``WarpProofBootstrap.enclosure_with_remainder,
    ``WarpProofBootstrap.strict_record_sound,
    ``WarpProofBootstrap.hessian_invariant_identity,
    ``WarpProofBootstrap.radial_invariant_identity,
    ``WarpProofBootstrap.radial_profile_identity,
    ``WarpProofBootstrap.bump_endpoint_jets,
    ``WarpProofBootstrap.baseline_coefficient_check,
    ``WarpProofBootstrap.baseline_coefficient_bounds,
    ``WarpProofBootstrap.oversized_coefficient_rejected,
    ``WarpProofBootstrap.missing_coefficient_rejected,
    ``WarpProofBootstrap.synthetic_tail_composition,
    ``WarpProofBootstrap.synthetic_record_gap]
  for theoremName in checked do
    let axioms ← Lean.collectAxioms theoremName
    let unexpected := axioms.filter fun name => !allowed.contains name
    unless unexpected.isEmpty do
      throwError "Unexpected axiom dependencies for {theoremName}: {unexpected}"
    logInfo m!"AXIOM_AUDIT_PASS {theoremName}: {axioms}"

