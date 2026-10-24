import Std
import Init.Data.Rat.Lemmas

/-!
# Exact certificate arithmetic, not a certificate of a spacetime

These theorems concern rational numbers and exact algebraic expressions.
There is deliberately no theorem claiming that a numerical quadrature result
encloses a real integral, or that a candidate satisfies the Einstein equations.
See `docs/FORMALIZATION.md` for the missing semantic bridge.
-/

namespace WarpProofBootstrap

/-- The nine monomials used by the draft axisymmetric potential perturbation. -/
def monomialPowers : List (Nat × Nat) :=
  [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (0, 1), (1, 1), (2, 1), (0, 2)]

theorem monomial_count : monomialPowers.length = 9 := by decide +kernel

theorem monomial_degrees :
    monomialPowers.all (fun ij => decide (ij.1 + 2 * ij.2 ≤ 4)) = true := by
  decide +kernel

/-- Exact coefficient limit; a finite design-space rule, not a curvature bound. -/
def CoefficientBound (x : Rat) : Prop := -(1 / 10 : Rat) ≤ x ∧ x ≤ (1 / 10 : Rat)

instance (x : Rat) : Decidable (CoefficientBound x) :=
  inferInstanceAs (Decidable (-(1 / 10 : Rat) ≤ x ∧ x ≤ (1 / 10 : Rat)))

def checkCoefficient (x : Rat) : Bool := decide (CoefficientBound x)

theorem checkCoefficient_sound (x : Rat) (h : checkCoefficient x = true) :
    CoefficientBound x := of_decide_eq_true h

def checkCoefficients (xs : List Rat) : Bool :=
  decide (xs.length = 9) && xs.all checkCoefficient

theorem checkCoefficients_sound (xs : List Rat) (h : checkCoefficients xs = true) :
    xs.length = 9 ∧ ∀ x ∈ xs, CoefficientBound x := by
  have hs := Bool.and_eq_true_iff.mp h
  constructor
  · exact of_decide_eq_true hs.1
  · intro x hx
    exact checkCoefficient_sound x ((List.all_eq_true.mp hs.2) x hx)

/-- Rational endpoints. Their physical meaning must be established separately. -/
structure QInterval where
  lower : Rat
  upper : Rat
  deriving Repr, DecidableEq

def QInterval.Contains (i : QInterval) (x : Rat) : Prop :=
  i.lower ≤ x ∧ x ≤ i.upper

instance (i : QInterval) (x : Rat) : Decidable (i.Contains x) :=
  inferInstanceAs (Decidable (i.lower ≤ x ∧ x ≤ i.upper))

def QInterval.add (i j : QInterval) : QInterval :=
  ⟨i.lower + j.lower, i.upper + j.upper⟩

def QInterval.scale (a : Rat) (i : QInterval) : QInterval :=
  ⟨a * i.lower, a * i.upper⟩

def QInterval.widen (i : QInterval) (epsilon : Rat) : QInterval :=
  ⟨i.lower - epsilon, i.upper + epsilon⟩

theorem enclosure_add (i j : QInterval) (x y : Rat)
    (hx : i.Contains x) (hy : j.Contains y) :
    (i.add j).Contains (x + y) := by
  constructor
  · exact Rat.le_trans (Rat.add_le_add_right.mpr hx.1)
      (Rat.add_le_add_left.mpr hy.1)
  · exact Rat.le_trans (Rat.add_le_add_right.mpr hx.2)
      (Rat.add_le_add_left.mpr hy.2)

theorem enclosure_scale (i : QInterval) (a x : Rat) (ha : 0 ≤ a)
    (hx : i.Contains x) : (i.scale a).Contains (a * x) := by
  exact ⟨Rat.mul_le_mul_of_nonneg_left hx.1 ha,
    Rat.mul_le_mul_of_nonneg_left hx.2 ha⟩

/-- Conditional composition: the remainder bound is an explicit hypothesis. -/
theorem enclosure_with_remainder (i : QInterval) (x delta epsilon : Rat)
    (hx : i.Contains x) (hd : -epsilon ≤ delta ∧ delta ≤ epsilon) :
    (i.widen epsilon).Contains (x + delta) := by
  have h := enclosure_add i ⟨-epsilon, epsilon⟩ x delta hx hd
  simpa only [QInterval.Contains, QInterval.add, QInterval.widen,
    Rat.sub_eq_add_neg] using h

theorem strict_record_sound (new old : QInterval) (x y : Rat)
    (hx : new.Contains x) (hy : old.Contains y) (hgap : new.upper < old.lower) :
    x < y := by
  apply Rat.not_le.mp
  intro hyx
  exact Rat.not_le.mpr hgap (Rat.le_trans hy.1 (Rat.le_trans hyx hx.2))

/-- Polynomial identity for a symmetric 3 by 3 Hessian, over exact rationals. -/
theorem hessian_invariant_identity (a b c d e f : Rat) :
    (a + b + c) ^ 2 - (a ^ 2 + b ^ 2 + c ^ 2 + 2 * (d ^ 2 + e ^ 2 + f ^ 2)) =
      2 * (a * b + a * c + b * c - d ^ 2 - e ^ 2 - f ^ 2) := by
  grind

/-- Algebraic part of the radial baseline reduction; no derivative semantics. -/
theorem radial_invariant_identity (a b mu : Rat) :
    (mu * (4 * a + b)) ^ 2 - ((mu * (2 * a + b)) ^ 2 + 2 * a ^ 2) =
      (12 * a ^ 2 + 4 * a * b) * mu ^ 2 - 2 * a ^ 2 := by
  grind

theorem radial_profile_identity (a b mu : Rat) :
    (12 * a ^ 2 + 4 * a * b) * mu ^ 2 - 2 * a ^ 2 =
      (4 * a * (a + (2 * a + b))) * mu ^ 2 - 2 * a ^ 2 := by
  grind

end WarpProofBootstrap
