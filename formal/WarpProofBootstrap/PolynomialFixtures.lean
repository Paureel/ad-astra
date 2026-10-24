import Std

/-!
Exact formal-polynomial endpoint checks for b(s) = [4 s (1-s)]^6.
Connecting this formal derivative to differentiability over the reals is a
separate obligation. These finite identities are useful inputs to that proof.
-/

namespace WarpProofBootstrap

/-- Integer coefficients in increasing degree order. -/
abbrev IPolynomial := List Int

def evalIPolynomial : IPolynomial → Int → Int
  | [], _ => 0
  | a :: p, x => a + x * evalIPolynomial p x

def derivativeFrom : IPolynomial → Nat → IPolynomial
  | [], _ => []
  | a :: p, n => (a * Int.ofNat n) :: derivativeFrom p (n + 1)

def derivativeIPolynomial (p : IPolynomial) : IPolynomial :=
  derivativeFrom p.tail 1

def iterDerivative : Nat → IPolynomial → IPolynomial
  | 0, p => p
  | n + 1, p => iterDerivative n (derivativeIPolynomial p)

/-- Expansion of 4096*s^6*(1-s)^6. -/
def bumpCoefficients : IPolynomial :=
  [0, 0, 0, 0, 0, 0, 4096, -24576, 61440, -81920, 61440, -24576, 4096]

def endpointJets : List (Int × Int) :=
  (List.range 6).map fun k =>
    (evalIPolynomial (iterDerivative k bumpCoefficients) 0,
     evalIPolynomial (iterDerivative k bumpCoefficients) 1)

theorem bump_endpoint_jets : endpointJets = List.replicate 6 (0, 0) := by
  decide +kernel

end WarpProofBootstrap
