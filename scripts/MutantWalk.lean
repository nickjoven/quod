/- MutantWalk.lean — Phase-3 mutant corpus: Expr-level statement mutants with
cheap gate labels, walked in one Mathlib process (the CorpusWalk pattern).

For a sampled subset of Mathlib THEOREMS, emit mutants of the statement type:
  hyp_del_k    drop the k-th explicit Prop binder (binder-level, so `variable`
               -introduced hypotheses are reachable — the Q-6 blind spot)
  swap_and_or  And <-> Or      (identical signatures: stays well-typed)
  swap_eq_ne   Eq  <-> Ne      (identical signatures)
  swap_lit_01  nat_lit 0 <-> 1 (same type: stays well-typed)
and two PROOF-side mutants whose verdict is fixed by construction:
  sorry_inject   statement unchanged, proof := sorry   -> "incomplete: sorry"
  axiom_inject   statement unchanged, proof via axiom  -> "rejected: extra axioms"

Per statement mutant we record `elaborates` (Meta.isTypeCorrect on the mutated
type, budgeted) and the mutated type in both the lock's canonical form (pp.all,
binders erased, universes u_i — byte-identical pipeline to CorpusWalk/lock.py,
hashed by the driver) and the readable form. `gate_verdict` for statement
mutants needs a proof attempt and is left null here (Phase-3b, sampled).

Env: CORPUS_OUT (required), CORPUS_LIMIT, CORPUS_RESUME_AFTER, and
CORPUS_SAMPLE_MOD=N (keep a theorem iff hash(name) % N == 0; ~230k theorems,
so N=46 -> ~5k parents). Output lines: INFO / START / MUT\t<json>. -/
import Mathlib
open Lean Meta

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

def wanted (env : Environment) (n : Name) (ci : ConstantInfo) : Bool :=
  !n.isInternal
  && (match ci with | .thmInfo _ => true | _ => false)
  && !(`Mathlib.Tactic).isPrefixOf ((env.getModuleFor? n).getD `_local)
  && (match env.getModuleFor? n with | some m => (`Mathlib).isPrefixOf m | none => false)

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

/-- Budgeted, exception-safe type-correctness of a mutated statement. -/
def elaborates (t : Expr) : MetaM Bool :=
  tryCatchRuntimeEx
    (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 20000000 }) do
      withCurrHeartbeats do
        try isTypeCorrect t catch _ => pure false)
    (fun _ => pure false)

structure Mut where
  op : String
  ty : Expr
  deriving Inhabited

/-- Statement mutants of a theorem type. -/
def mutantsOf (t : Expr) : MetaM (Array Mut) := do
  let mut out : Array Mut := #[]
  -- binder-level hypothesis deletion
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
          -- drop binder k by index (List.enum is not available at this pin)
          let keep : Array Expr :=
            ((List.range xs.size).filterMap fun i => if i == k then none else some xs[i]!).toArray
          let t' ← mkForallFVars keep body
          pure (some (Mut.mk s!"hyp_del_{k}" t'))
       catch _ => pure none)
      (fun _ => pure none)
    if let some m := m then out := out.push m
  -- signature-preserving constant / literal swaps, only where they change something
  for (op, f) in [("swap_and_or", swapConst ``And ``Or), ("swap_or_and", swapConst ``Or ``And),
                  ("swap_eq_ne", swapConst ``Eq ``Ne), ("swap_ne_eq", swapConst ``Ne ``Eq),
                  ("swap_lit_01", swapLit01)] do
    let t' := f t
    if t' != t then out := out.push (Mut.mk op t')
  return out

def emitMut (out : IO.FS.Handle) (env : Environment) (parent : Name) (ci : ConstantInfo)
    (m : Mut) : MetaM Unit := do
  let canon ← canonOf m.ty ci.levelParams
  let readable ← ppExpr m.ty
  let ok ← elaborates m.ty
  let js := Json.mkObj [
    ("parent", Json.str parent.toString),
    ("module", Json.str ((env.getModuleFor? parent).getD `_local).toString),
    ("operator", Json.str m.op),
    ("mutated_canonical", Json.str canon),
    ("mutated_readable", Json.str ((toString readable).replace "\n" " ")),
    ("elaborates", Json.bool ok),
    ("gate_verdict", Json.null)]
  out.putStr s!"MUT\t{js.compress}\n"; out.flush

set_option maxHeartbeats 0 in
run_meta do
  let env ← getEnv
  let limit := (((← IO.getEnv "CORPUS_LIMIT").getD "0").toNat?).getD 0
  let resumeAfter := (← IO.getEnv "CORPUS_RESUME_AFTER").getD ""
  let sampleMod := (((← IO.getEnv "CORPUS_SAMPLE_MOD").getD "1").toNat?).getD 1
  let outPath := (← IO.getEnv "CORPUS_OUT").getD "/dev/stdout"
  let out ← IO.FS.Handle.mk outPath IO.FS.Mode.append
  let emit (s : String) : IO Unit := do out.putStr (s ++ "\n"); out.flush
  let names : Array Name := env.constants.fold (init := #[]) fun acc n ci =>
    if wanted env n ci && (sampleMod ≤ 1 || (hash n.toString).toNat % sampleMod == 0) then acc.push n
    else acc
  let sorted := names.qsort fun a b => a.toString < b.toString
  emit s!"INFO\t{sorted.size} theorems selected (sample_mod={sampleMod}, limit={limit}, resumeAfter={resumeAfter})"
  let mut emitted := 0
  let mut skipping := resumeAfter != ""
  for n in sorted do
    if skipping then
      if n.toString == resumeAfter then skipping := false
    else
      if limit > 0 && emitted ≥ limit then break
      emit s!"START\t{n}"
      match env.find? n with
      | none => emit s!"INFO\tVANISHED {n}"
      | some ci =>
        tryCatchRuntimeEx
          (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 400000 }) do
            withCurrHeartbeats do
              try
                let muts ← mutantsOf ci.type
                for m in muts do emitMut out env n ci m
                -- proof-side mutants: verdict fixed by construction, statement unchanged
                let canon ← canonOf ci.type ci.levelParams
                let readable ← ppExpr ci.type
                for (op, v) in [("sorry_inject", "incomplete: sorry"),
                                ("axiom_inject", "rejected: extra axioms [oracle]")] do
                  let js := Json.mkObj [
                    ("parent", Json.str n.toString),
                    ("module", Json.str ((env.getModuleFor? n).getD `_local).toString),
                    ("operator", Json.str op),
                    ("mutated_canonical", Json.str canon),
                    ("mutated_readable", Json.str ((toString readable).replace "\n" " ")),
                    ("elaborates", Json.bool true),
                    ("gate_verdict", Json.str v)]
                  out.putStr s!"MUT\t{js.compress}\n"; out.flush
              catch e =>
                emit s!"INFO\tERROR {n}: {← e.toMessageData.toString}")
          (fun _ => emit s!"INFO\tBUDGET {n}")
      emitted := emitted + 1
      if emitted % 500 == 0 then emit s!"INFO\t{emitted}/{sorted.size}"
  emit s!"INFO\tdone, {emitted} parents"
