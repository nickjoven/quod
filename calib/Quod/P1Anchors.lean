import CrouzeixConjecture

/-! P1 anchors: every custom constant in the type of
`CrouzeixConjecture.crouzeixConjecture` unfolds to a Mathlib notion by `rfl`.
These are the definitional bridges the lock requires before the claim can
be `proven`. Plus the satisfiability witness: the hypothesis context is
inhabited at `n := Fin 1`. -/

open scoped Matrix Matrix.Norms.L2Operator InnerProductSpace
open CrouzeixConjecture

variable {n : Type*} [Fintype n] [DecidableEq n]

theorem anchor_SquareMatrix : SquareMatrix n = Matrix n n ℂ := rfl

theorem anchor_EuclideanVector : EuclideanVector n = EuclideanSpace ℂ n := rfl

theorem anchor_polynomialEval (p : Polynomial ℂ) (A : SquareMatrix n) :
    polynomialEval p A = Polynomial.aeval A p := rfl

theorem anchor_norm (A : SquareMatrix n) :
    ‖A‖ = ‖(Matrix.toEuclideanCLM (𝕜 := ℂ) (n := n) A : EuclideanSpace ℂ n →L[ℂ] EuclideanSpace ℂ n)‖ := rfl

theorem anchor_numericalRange (A : SquareMatrix n) :
    numericalRange A =
      {z | ∃ x : EuclideanSpace ℂ n, ‖x‖ = 1 ∧ ⟪x, Matrix.toEuclideanCLM (𝕜 := ℂ) A x⟫_ℂ = z} := rfl

theorem anchor_maxPolynomialModulusOnNumericalRange (A : SquareMatrix n) (p : Polynomial ℂ) :
    maxPolynomialModulusOnNumericalRange A p =
      sSup ((fun z : ℂ ↦ ‖Polynomial.eval z p‖) '' numericalRange A) := rfl

/-- Satisfiability witness: the endpoint's hypothesis context is inhabited. -/
example (A : SquareMatrix (Fin 1)) (p : Polynomial ℂ) :
    ‖polynomialEval p A‖ ≤ 2 * maxPolynomialModulusOnNumericalRange A p :=
  crouzeixConjecture A p

#print axioms anchor_norm
#print axioms anchor_numericalRange
