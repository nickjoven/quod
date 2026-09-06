import CrouzeixConjecture

/-! P2: a theorem proven here from scratch through the whole pipeline.

Sharpness of the constant 2 at the 2×2 nilpotent Jordan block
`J = !![0, 1; 0, 0]`: `‖J‖ ≥ 1` (it maps `e₁` to `e₀`) and every point of the
numerical range has modulus at most `1/2` (`⟪x, J x⟫ = conj (x 0) * x 1` with
`‖x 0‖² + ‖x 1‖² = 1`). So with `p = X`, `‖p(J)‖ ≥ 2 · sup_{W(J)} |p|`.

N4 (Crouzeix with constant 1) is refuted by the same witness. -/

open CrouzeixConjecture
open scoped Matrix Matrix.Norms.L2Operator InnerProductSpace ComplexConjugate

namespace QuodP2

/-- The 2×2 nilpotent Jordan block. -/
def J : SquareMatrix (Fin 2) := !![0, 1; 0, 0]

/-- Anchor: the witness is the literal Mathlib matrix. -/
theorem anchor_J : J = !![0, 1; 0, 0] := rfl

lemma J_mulVec (x : Fin 2 → ℂ) : J *ᵥ x = ![x 1, 0] := by
  ext i
  fin_cases i <;> simp [J, Matrix.mulVec, dotProduct, Fin.sum_univ_two]

/-- The inner product `⟪x, J x⟫` on Euclidean space is `conj (x 0) * x 1`. -/
lemma inner_J (x : EuclideanSpace ℂ (Fin 2)) :
    ⟪x, (Matrix.toEuclideanCLM (𝕜 := ℂ) J) x⟫_ℂ = conj (x 0) * x 1 := by
  simp [PiLp.inner_apply, Fin.sum_univ_two, Matrix.ofLp_toEuclideanCLM, J_mulVec, mul_comm]

/-- AM-GM in the form needed: `‖a‖ * ‖b‖ ≤ (‖a‖^2 + ‖b‖^2) / 2`. -/
lemma norm_mul_le_half (a b : ℂ) : ‖a‖ * ‖b‖ ≤ (‖a‖ ^ 2 + ‖b‖ ^ 2) / 2 := by
  nlinarith [sq_nonneg (‖a‖ - ‖b‖)]

/-- Every point of the numerical range of `J` has modulus at most `1/2`. -/
lemma numericalRange_J_le (z : ℂ) (hz : z ∈ numericalRange J) : ‖z‖ ≤ 1 / 2 := by
  obtain ⟨x, hx, rfl⟩ := hz
  have hnorm : ‖x 0‖ ^ 2 + ‖x 1‖ ^ 2 = 1 := by
    have h := EuclideanSpace.norm_sq_eq x
    rw [hx, Fin.sum_univ_two, one_pow] at h
    linarith
  have hin : ⟪x, euclideanOperator J x⟫_ℂ = conj (x 0) * x 1 := inner_J x
  rw [hin, norm_mul, RCLike.norm_conj]
  linarith [norm_mul_le_half (x 0) (x 1)]

/-- The maximum modulus of `p = X` on the numerical range of `J` is at most `1/2`. -/
theorem maxmod_J_le : maxPolynomialModulusOnNumericalRange J Polynomial.X ≤ 1 / 2 := by
  unfold maxPolynomialModulusOnNumericalRange
  apply csSup_le ((numericalRange_nonempty J).image _)
  rintro _ ⟨z, hz, rfl⟩
  simpa using numericalRange_J_le z hz

/-- `‖J‖ ≥ 1`: the unit vector `e₁` is sent to the unit vector `e₀`. -/
theorem one_le_norm_J : 1 ≤ ‖J‖ := by
  rw [← Matrix.l2_opNorm_toEuclideanCLM (𝕜 := ℂ) J]
  set e1 : EuclideanSpace ℂ (Fin 2) := EuclideanSpace.single 1 1 with he1
  have h1 : ‖e1‖ = 1 := by simp [he1, EuclideanSpace.norm_single]
  have h := (Matrix.toEuclideanCLM (𝕜 := ℂ) J).unit_le_opNorm e1 h1.le
  have himg : (Matrix.toEuclideanCLM (𝕜 := ℂ) J) e1 = EuclideanSpace.single 0 1 := by
    ext i
    fin_cases i <;> simp [he1, J, Matrix.ofLp_toEuclideanCLM, EuclideanSpace.single_apply]
  rw [himg, EuclideanSpace.norm_single] at h
  simpa using h

theorem polynomialEval_X_J : polynomialEval Polynomial.X J = J := by
  simp [polynomialEval]

/-- Sharpness: at `J` and `p = X` the bound `2 · sup` is attained from below. -/
theorem sharp_two :
    2 * maxPolynomialModulusOnNumericalRange J Polynomial.X ≤ ‖polynomialEval Polynomial.X J‖ := by
  rw [polynomialEval_X_J]
  linarith [maxmod_J_le, one_le_norm_J]

/-- N4 refuted: Crouzeix with constant 1 is false already at `n = Fin 2`. -/
theorem constant_one_false :
    ¬ ∀ (A : SquareMatrix (Fin 2)) (p : Polynomial ℂ),
        ‖polynomialEval p A‖ ≤ 1 * maxPolynomialModulusOnNumericalRange A p := by
  intro h
  have := h J Polynomial.X
  rw [polynomialEval_X_J] at this
  linarith [maxmod_J_le, one_le_norm_J]

/-- N4's statement, quantified over every finite index type in `Type`, is false: the
`Fin 2` counterexample refutes it. -/
theorem N4_refuted :
    ¬ ∀ {n : Type} [Fintype n] [DecidableEq n] [Nonempty n] (A : SquareMatrix n)
        (p : Polynomial ℂ), ‖polynomialEval p A‖ ≤ 1 * maxPolynomialModulusOnNumericalRange A p :=
  fun h => constant_one_false fun A p => h A p

end QuodP2
