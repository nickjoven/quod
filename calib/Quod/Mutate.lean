/- Quod.Mutate — the statement-mutation operators, as ONE lake-built module.

MutantWalk.lean (the Phase-3 corpus) and AttemptWalk.lean (Phase-3b attempts
on those mutants) must apply byte-identical operators: an attempt is labelled
"for mutant M" only if the mutated type it rebuilt has M's lock. Sharing the
code here makes that a property of the build, not a hope; the driver still
verifies it by lock equality (a nomination verified by a gate).

The canonicalisation is the lock pipeline of lock.py / CorpusWalk.lean:
binders erased, universes renamed u_0.., pp.all + pp.universes + pp.fullNames;
the BLAKE3 is computed by the Python driver over the whitespace-normalised
string so it stays byte-identical to lock.py. -/
import Mathlib
open Lean Meta

namespace Quod.Mutate

partial def eraseBinders : Expr → Expr
  | .forallE _ t b bi => .forallE `_ (eraseBinders t) (eraseBinders b) bi
  | .lam _ t b bi => .lam `_ (eraseBinders t) (eraseBinders b) bi
  | .letE _ t v b nd => .letE `_ (eraseBinders t) (eraseBinders v) (eraseBinders b) nd
  | .app f a => .app (eraseBinders f) (eraseBinders a)
  | .mdata _ e => eraseBinders e
  | .proj n i e => .proj n i (eraseBinders e)
  | e => e

/-- The lock's canonical string for a type with the given level params. -/
def canonOf (t : Expr) (lps : List Name) : MetaM String := do
  let us := (List.range lps.length).map fun i => Level.param (Name.mkSimple s!"u_{i}")
  let t := eraseBinders (t.instantiateLevelParams lps us)
  let fmt ← withOptions (fun o =>
      ((o.setBool `pp.all true).setBool `pp.universes true).setBool `pp.fullNames true) do
    ppExpr t
  return toString fmt

/-- Replace every occurrence of constant `a` by `b` (levels preserved). -/
def swapConst (a b : Name) (e : Expr) : Expr :=
  e.replace fun
    | .const n ls => if n == a then some (.const b ls) else none
    | _ => none

/-- Swap `nat_lit 0` and `nat_lit 1`. -/
def swapLit01 (e : Expr) : Expr :=
  e.replace fun
    | .lit (.natVal 0) => some (.lit (.natVal 1))
    | .lit (.natVal 1) => some (.lit (.natVal 0))
    | _ => none

structure Mut where
  op : String
  ty : Expr
  deriving Inhabited

/-- The signature-preserving swap operators, by name (order is part of the corpus contract). -/
def swapOps : List (String × (Expr → Expr)) :=
  [("swap_and_or", swapConst ``And ``Or), ("swap_or_and", swapConst ``Or ``And),
   ("swap_eq_ne", swapConst ``Eq ``Ne), ("swap_ne_eq", swapConst ``Ne ``Eq),
   ("swap_lit_01", swapLit01)]

/-- Statement mutants of a theorem type: binder-level hypothesis deletion for
each explicit Prop binder, then the swap operators where they change something. -/
def mutantsOf (t : Expr) : MetaM (Array Mut) := do
  let mut out : Array Mut := #[]
  let hyps ← forallTelescope t fun xs _ => do
    let mut ks : Array Nat := #[]
    for k in [:xs.size] do
      let d ← xs[k]!.fvarId!.getDecl
      if d.binderInfo == .default && (← isProp d.type) then ks := ks.push k
    pure ks
  for k in hyps do
    let m ← tryCatchRuntimeEx
      (try
        forallTelescope t fun xs body => do
          let keep : Array Expr :=
            ((List.range xs.size).filterMap fun i => if i == k then none else some xs[i]!).toArray
          let t' ← mkForallFVars keep body
          pure (some (Mut.mk s!"hyp_del_{k}" t'))
       catch _ => pure none)
      (fun _ => pure none)
    if let some m := m then out := out.push m
  for (op, f) in swapOps do
    let t' := f t
    if t' != t then out := out.push (Mut.mk op t')
  return out

/-- The single mutant of `t` with operator name `op`, if it exists. -/
def mutantNamed (t : Expr) (op : String) : MetaM (Option Expr) := do
  for m in ← mutantsOf t do
    if m.op == op then return some m.ty
  return none

end Quod.Mutate
