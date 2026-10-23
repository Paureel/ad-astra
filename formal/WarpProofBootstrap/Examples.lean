import WarpProofBootstrap.CertificateArithmetic
import WarpProofBootstrap.PolynomialFixtures

namespace WarpProofBootstrap

def baselineCoefficients : List Rat := List.replicate 9 0

theorem baseline_coefficient_check : checkCoefficients baselineCoefficients = true := by
  decide +kernel

theorem baseline_coefficient_bounds :
    baselineCoefficients.length = 9 ∧
      ∀ x ∈ baselineCoefficients, CoefficientBound x :=
  checkCoefficients_sound baselineCoefficients baseline_coefficient_check

theorem oversized_coefficient_rejected : checkCoefficient (11 / 100) = false := by
  decide +kernel

theorem missing_coefficient_rejected : checkCoefficients (List.replicate 8 0) = false := by
  decide +kernel

/-- Synthetic arithmetic fixture, not an energy result in joules. -/
theorem synthetic_tail_composition :
    ((⟨100, 101⟩ : QInterval).add (⟨2, 3⟩ : QInterval)).Contains (104 / 1) := by
  decide +kernel

theorem synthetic_record_gap :
    (⟨100, 101⟩ : QInterval).upper < (⟨102, 103⟩ : QInterval).lower := by
  decide +kernel

end WarpProofBootstrap
