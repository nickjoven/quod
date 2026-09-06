import CrouzeixConjecture
/-! N4: Crouzeix with constant 1. Must be `refuted`: the negation is proven
by the 2x2 nilpotent witness from P2. Stated here; the refutation lives in
P2's file. -/
open CrouzeixConjecture
open scoped Matrix Matrix.Norms.L2Operator
theorem crouzeix_constant_one {n : Type*} [Fintype n] [DecidableEq n] [Nonempty n]
    (A : SquareMatrix n) (p : Polynomial ℂ) :
    ‖polynomialEval p A‖ ≤ 1 * maxPolynomialModulusOnNumericalRange A p := by
  sorry
