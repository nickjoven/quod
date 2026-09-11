/- AttemptWalk.lean — tier-A prover-in-the-loop (ATTEMPTS.md rev 2, scope §1).

For each demonstrandum (a theorem at the pin, selected like CorpusWalk), open
a fresh goal with its type and run a bounded tactic ladder, each rung under a
heartbeat cap. On the first rung that closes the goal:
  * the proof term is instantiated (no metavariables allowed),
  * it is ADDED to the environment as a theorem — that is the kernel check —
  * its axioms are collected (the in-process form of axiom_gate.py's test),
  * its used constants are recorded, and `uses_self` flags the demonstrandum's
    own name. The full self-proof gate (no constant whose LOCK equals the
    demonstrandum's lock) needs the corpus locks and is applied by the driver.
Nothing here declares a verdict: the driver re-runs the external gates
(axiom_gate.py, lean4checker) on a generated module and only then records one.

Outcomes: `accepted` (a rung closed the goal and the kernel accepted the term)
or `no_proof_found` (every rung failed within budget) — the latter is a fact
about THIS ladder and THIS budget, never a refutation.

Env: CORPUS_OUT, CORPUS_ONLY (comma list), CORPUS_SAMPLE_MOD, CORPUS_LIMIT,
CORPUS_RESUME_AFTER (as CorpusWalk); CORPUS_NEGATE=1 attempts `¬ T` instead
of `T` (the prover-negative control: any acceptance means the pin is
inconsistent and the driver halts); ATTEMPT_HEARTBEATS (per rung, default
2e7); ATTEMPT_LADDER (comma list, default rfl,decide,simp,omega,exact?,aesop).
Output lines: INFO / START / ATT\t<json>. -/
import Mathlib
open Lean Meta Elab

def wanted (env : Environment) (n : Name) (ci : ConstantInfo) : Bool :=
  !n.isInternal
  && (match ci with | .thmInfo _ => true | _ => false)
  && !(`Mathlib.Tactic).isPrefixOf ((env.getModuleFor? n).getD `_local)
  && (match env.getModuleFor? n with | some m => (`Mathlib).isPrefixOf m | none => false)

structure Rung where
  name : String
  ok : Bool
  err : String := ""

/-- Run one tactic (given as source text) on a fresh goal of type `ty`.
Returns the closed proof term, or the failure reason. Budgeted; runtime
exceptions (heartbeats) are caught and reported as a failure, never fatal. -/
def tryRung (ty : Expr) (tac : String) (heartbeats : Nat) : MetaM (Except String Expr) := do
  let env ← getEnv
  let stx ← match Parser.runParserCategory env `tactic tac "<attempt>" with
    | .ok s => pure s
    | .error e => return .error s!"parse: {e}"
  tryCatchRuntimeEx
    (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := heartbeats }) do
      withCurrHeartbeats do
        try
          let pf ← Term.TermElabM.run' (ctx := {}) (s := {}) do
            Term.withoutErrToSorry do
              let mvar ← mkFreshExprMVar ty
              Term.runTactic mvar.mvarId! stx .term
              Term.synthesizeSyntheticMVarsNoPostponing
              let pf ← instantiateMVars mvar
              if pf.hasMVar || pf.hasSorry then throwError "open goals or sorry"
              pure pf
          return .ok pf
        catch e => return .error (← e.toMessageData.toString))
    (fun _ => return .error "budget exceeded")

/-- Kernel check: add the term as a theorem. Returns the axioms it depends on. -/
def kernelAccept (nm : Name) (lps : List Name) (ty pf : Expr) : MetaM (Except String (Array Name)) := do
  try
    addDecl (.thmDecl { name := nm, levelParams := lps, type := ty, value := pf })
    let axs ← collectAxioms nm
    return .ok axs
  catch e => return .error (← e.toMessageData.toString)

set_option maxHeartbeats 0 in
run_meta do
  let env ← getEnv
  let limit := (((← IO.getEnv "CORPUS_LIMIT").getD "0").toNat?).getD 0
  let resumeAfter := (← IO.getEnv "CORPUS_RESUME_AFTER").getD ""
  let only := (((← IO.getEnv "CORPUS_ONLY").getD "").splitOn ",").filter (· != "")
  let sampleMod := (((← IO.getEnv "CORPUS_SAMPLE_MOD").getD "1").toNat?).getD 1
  let negate := (← IO.getEnv "CORPUS_NEGATE").getD "0" == "1"
  let hb := (((← IO.getEnv "ATTEMPT_HEARTBEATS").getD "20000000").toNat?).getD 20000000
  let ladder := (((← IO.getEnv "ATTEMPT_LADDER").getD "rfl,decide,simp,omega,exact?,aesop").splitOn ",").filter (· != "")
  let outPath := (← IO.getEnv "CORPUS_OUT").getD "/dev/stdout"
  let out ← IO.FS.Handle.mk outPath IO.FS.Mode.append
  let emit (s : String) : IO Unit := do out.putStr (s ++ "\n"); out.flush
  let names : Array Name := env.constants.fold (init := #[]) fun acc n ci =>
    if wanted env n ci && (only.isEmpty || only.contains n.toString)
       && (sampleMod ≤ 1 || (hash n.toString).toNat % sampleMod == 0) then acc.push n else acc
  let sorted := names.qsort fun a b => a.toString < b.toString
  emit s!"INFO\t{sorted.size} demonstranda (negate={negate}, ladder={ladder}, heartbeats={hb}, limit={limit})"
  let mut emitted := 0
  let mut skipping := resumeAfter != ""
  let mut k := 0
  for n in sorted do
    if skipping then
      if n.toString == resumeAfter then skipping := false
    else
      if limit > 0 && emitted ≥ limit then break
      emit s!"START\t{n}"
      match env.find? n with
      | none => emit s!"INFO\tVANISHED {n}"
      | some ci =>
        let ty := if negate then mkApp (mkConst ``Not) ci.type else ci.type
        let mut rungs : Array Json := #[]
        let mut found : Option (String × Expr) := none
        for tac in ladder do
          if found.isSome then break
          -- Theorem statements are ∀-telescopes; every rung needs the binders
          -- introduced first (rfl/decide/omega fail outright on a ∀ goal). The
          -- recorded script is the FULL script the driver replays verbatim.
          -- Parenthesized: `runParserCategory \`tactic` parses ONE tactic, and
          -- `a; b` is a tacticSeq, not a tactic — `(a; b)` is.
          let script := s!"(intros; {tac})"
          match ← tryRung ty script hb with
          | .ok pf =>
            rungs := rungs.push (Json.mkObj [("tactic", Json.str script), ("ok", Json.bool true)])
            found := some (script, pf)
          | .error e =>
            rungs := rungs.push (Json.mkObj [("tactic", Json.str script), ("ok", Json.bool false),
                                             ("err", Json.str (e.take 160).toString)])
        let base := Json.mkObj [
          ("demonstrandum", Json.str n.toString),
          ("module", Json.str ((env.getModuleFor? n).getD `_local).toString),
          ("n_levels", Json.num ci.levelParams.length),
          ("negated", Json.bool negate),
          ("ladder", Json.arr rungs)]
        match found with
        | none =>
          emit s!"ATT\t{(base.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found")])).compress}"
        | some (tac, pf) =>
          k := k + 1
          let nm := Name.mkSimple s!"attempt_{k}"
          let used := pf.getUsedConstants
          let kres ← kernelAccept nm ci.levelParams ty pf
          let pfStr ← ppExpr pf
          let extra := match kres with
            | .ok axs => Json.mkObj [
                ("outcome", Json.str "accepted"),
                ("tactic", Json.str tac),
                ("kernel_ok", Json.bool true),
                ("axioms", Json.arr (axs.map (Json.str ·.toString))),
                ("used_consts", Json.arr (used.map (Json.str ·.toString))),
                ("uses_self", Json.bool (used.contains n)),
                ("proof_pp", Json.str (((toString pfStr).replace "\n" " ").take 4000).toString)]
            | .error e => Json.mkObj [
                ("outcome", Json.str "kernel_rejected"),
                ("tactic", Json.str tac),
                ("kernel_ok", Json.bool false),
                ("kernel_err", Json.str (e.take 300).toString),
                ("used_consts", Json.arr (used.map (Json.str ·.toString))),
                ("uses_self", Json.bool (used.contains n))]
          emit s!"ATT\t{(base.mergeObj extra).compress}"
      emitted := emitted + 1
      if emitted % 100 == 0 then emit s!"INFO\t{emitted}/{sorted.size}"
  emit s!"INFO\tdone, {emitted} demonstranda"
