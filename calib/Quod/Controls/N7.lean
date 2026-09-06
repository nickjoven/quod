import Mathlib.Tactic
/-! N7: anchor laundering. The AIX template again, but this time the private
predicate carries an anchor of the admissible shape whose right-hand side is
another private constant. The anchor chain does not end in the pinned
libraries, so the claim must still land as `stated`. -/
namespace Tower7
def declInv (n : ℕ) : Prop := ∀ m ≤ n, m = m
def declInv' (n : ℕ) : Prop := declInv n
theorem anchor_declInv (n : ℕ) : declInv n ↔ declInv' n := Iff.rfl
theorem universal (step : ∀ n, declInv n → declInv (n + 1)) (base : declInv 0) : ∀ n, declInv n := by
  intro n; induction n with
  | zero => exact base
  | succ k ih => exact step k ih
end Tower7
theorem navier_stokes_laundered (step : ∀ n, Tower7.declInv n → Tower7.declInv (n + 1)) :
    ∀ n, Tower7.declInv n :=
  Tower7.universal step (fun _ _ => rfl)
