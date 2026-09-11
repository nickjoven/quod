import Mathlib.Tactic
/-! N1: the induction template. A custom predicate, a `step` hypothesis carrying all
the mathematics, and a two-line "proof" by induction. Must land as `proven`
(SEMANTICS.md) with `step` listed and `Tower.declInv` unanchored. -/
namespace Tower
def declInv (n : ℕ) : Prop := ∀ m ≤ n, m = m   -- stands in for the private predicate
theorem universal (step : ∀ n, declInv n → declInv (n + 1)) (base : declInv 0) : ∀ n, declInv n := by
  intro n; induction n with
  | zero => exact base
  | succ k ih => exact step k ih
end Tower
theorem navier_stokes (step : ∀ n, Tower.declInv n → Tower.declInv (n + 1)) : ∀ n, Tower.declInv n :=
  Tower.universal step (fun _ _ => rfl)
