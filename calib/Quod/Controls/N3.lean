import Mathlib.Tactic
/-! N3: a proof resting on an uninterpreted axiom. The axiom gate must FAIL. -/
axiom oracle : ∀ n : ℕ, Nat.Prime n → n < 10 ^ 100
theorem all_primes_small : ∀ n, Nat.Prime n → n < 10 ^ 100 := oracle
