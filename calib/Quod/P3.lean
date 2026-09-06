import Mathlib.NumberTheory.PrimeCounting

/-! P3: a Mathlib theorem restated under another name. The lock must equal
Mathlib's own, so the corpus holds one node, and status arrives by dependency
(the proof is the Mathlib term itself). -/

namespace QuodP3

theorem infinitely_many_primes_again (n : ℕ) : ∃ p, n ≤ p ∧ Nat.Prime p :=
  Nat.exists_infinite_primes n

end QuodP3
