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
CORPUS_MUTATE=1: instead of the theorem itself, attempt each ELABORATED
statement mutant of it (Quod.Mutate — the same operators that built the
mutant corpus), emitting `mutant_operator` and `mutant_canonical` so the
driver can verify by lock equality that the attempt is for the corpus
mutant.

TRANSITIONS (the world-model corpus): every tactic step of every attempt is
recorded, whatever its outcome. A rung `(intros; tac)` is run as two steps —
`intros` on the initial goal, then `tac` on what it produced — so a rung that
makes progress without closing yields its remaining goals, and a failing rung
yields an error CLASS (`budget` = the heartbeat cap was hit: a CENSORED
observation, not a failure at infinite cost). Every goal is closed over its
local context (∀ over the hypotheses) and canonicalised exactly like a
statement (Quod.Mutate.canonOf: binders erased, universes renamed, pp.all), so
the driver hashes it with lock_of and a goal state has an identity; the
readable form (ppGoal) is recorded alongside, once per distinct goal.

Output lines: INFO / START / ATT\t<json> / GOAL\t<json> / TRANS\t<json>.
ATT and TRANS share `aid` (attempt counter); TRANS and GOAL share `gid`. -/
import Quod.Mutate
open Lean Meta Elab

def wanted (env : Environment) (n : Name) (ci : ConstantInfo) : Bool :=
  !n.isInternal
  && (match ci with | .thmInfo _ => true | _ => false)
  && !(`Mathlib.Tactic).isPrefixOf ((env.getModuleFor? n).getD `_local)
  && (match env.getModuleFor? n with | some m => (`Mathlib).isPrefixOf m | none => false)

/-- Goal identities. `canon → gid`, shared by the whole walk; a GOAL line is
emitted the first time a canonical form is seen. -/
structure GoalTable where
  ids : Std.HashMap String Nat := {}
  next : Nat := 0
  emit : String → IO Unit := fun _ => pure ()

/-- Walk-wide mutable state (a script has no `initialize`; the ref is created
in `run_meta` and passed down). -/
abbrev Walk := IO.Ref GoalTable

/-- Close the goal over its local context and canonicalise it as a statement. -/
def goalCanon (g : MVarId) (lps : List Name) : MetaM (String × String) := g.withContext do
  let ty ← instantiateMVars (← g.getType)
  let lctx ← getLCtx
  let fvars := lctx.foldl (init := #[]) fun acc d => if d.isImplementationDetail then acc else acc.push d.toExpr
  let closed ← mkForallFVars fvars ty
  let canon ← Quod.Mutate.canonOf closed lps
  let readable ← ppGoal g
  return (canon, toString readable)

def goalId (w : Walk) (g : MVarId) (lps : List Name) : MetaM Nat := do
  let (canon, readable) ← goalCanon g lps
  let tbl ← w.get
  match tbl.ids[canon]? with
  | some i => return i
  | none =>
    let i := tbl.next
    w.set { tbl with ids := tbl.ids.insert canon i, next := i + 1 }
    let r := readable.take 6000
    let j := Json.mkObj [("gid", Json.num i), ("readable", Json.str r.toString),
                         ("readable_truncated", Json.bool (readable.length > 6000)),
                         ("canonical", Json.str canon)]
    tbl.emit s!"GOAL\t{j.compress}"
    return i

/-- One recorded tactic step. `after` is `"closed"`, `"error"`, or the list of
remaining goal ids; `errClass` ∈ {"", budget, no_progress, failed, parse, error}. -/
structure Step where
  pos : Nat
  kind : String
  tactic : String
  before : Nat
  after : Json
  errClass : String := ""
  err : String := ""
  heartbeats : Nat := 0
  cap : Nat
  wallMs : Nat := 0
  deriving Inhabited

def Step.toJson (s : Step) : Json :=
  Json.mkObj [("pos", Json.num s.pos), ("kind", Json.str s.kind), ("tactic", Json.str s.tactic),
              ("before", Json.num s.before), ("after", s.after), ("err_class", Json.str s.errClass),
              ("err", Json.str s.err), ("heartbeats", Json.num s.heartbeats), ("heartbeat_cap", Json.num s.cap),
              ("wall_ms", Json.num s.wallMs)]

def errClassOf (msg : String) : String :=
  if msg.startsWith "parse:" then "parse"
  else if (msg.splitOn "made no progress").length > 1 then "no_progress"
  else if (msg.splitOn "failed").length > 1 then "failed"
  else "error"

/-- Run one tactic syntax on one goal; the remaining goals. Ordinary tactic
errors are caught here; runtime (heartbeat) exceptions propagate to the caller. -/
def runTacOn (g : MVarId) (stx : Syntax) : MetaM (Except String (List MVarId)) := do
  try
    let gs ← Term.TermElabM.run' (ctx := {}) (s := {}) do
      Term.withoutErrToSorry do
        let gs ← Tactic.run g (Tactic.withoutRecover (Tactic.evalTactic stx))   -- Q-28: simp's argument elaborator LOGS an unknown lemma under recover=true
        Term.synthesizeSyntheticMVarsNoPostponing
        pure gs
    return .ok gs
  catch e => return .error (← e.toMessageData.toString)

/-- Run one rung `(intros; tac)` as two recorded steps on a fresh goal of
type `ty`. Returns the steps and, if the goal closed, the proof term. The
heartbeat cap applies to the whole rung; hitting it yields a `budget` step. -/
def tryRung (w : Walk) (ty : Expr) (lps : List Name) (pos : Nat) (tac : String) (heartbeats : Nat)
    : MetaM (Array Step × Except String Expr) := do
  let env ← getEnv
  let parse (s : String) : Except String Syntax :=
    match Parser.runParserCategory env `tactic s "<attempt>" with
    | .ok stx => .ok stx | .error e => .error s!"parse: {e}"
  let goalId := goalId w
  let mvar ← mkFreshExprMVar ty
  let g0 := mvar.mvarId!
  let gid0 ← goalId g0 lps
  let cur : Step := { pos, kind := "intros", tactic := "intros", before := gid0, after := Json.str "error", cap := heartbeats }
  -- the heartbeat counter is process-global and monotone; deltas are the step's cost
  let hb0 ← IO.getNumHeartbeats
  let t0 ← IO.monoMsNow
  let r : Except (Step × String) (Array Step × Expr) ← tryCatchRuntimeEx
    (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := heartbeats }) do
      withCurrHeartbeats (do
        -- step 1: intros
        let introsStx ← match parse "intros" with
          | .ok s => pure s | .error e => return .error (cur, e)
        let gs1 ← match ← runTacOn g0 introsStx with
          | .ok gs => pure gs
          | .error e => return .error ({ cur with errClass := errClassOf e, err := (e.take 160).toString }, "intros failed")
        let hb1 ← IO.getNumHeartbeats; let t1 ← IO.monoMsNow
        let ids1 ← gs1.mapM (goalId · lps)
        let after1 := if gs1.isEmpty then Json.str "closed" else Json.arr (ids1.map Json.num).toArray
        let s1 : Step := { cur with after := after1, heartbeats := hb1 - hb0, wallMs := t1 - t0 }
        match gs1 with
        | [] => return .ok (#[s1], mvar)          -- intros alone closed it (degenerate; recorded)
        | g1 :: _ =>
          -- step 2: the rung's tactic on the first (normally only) goal
          let s2base : Step := { pos, kind := "rung", tactic := tac, before := ids1.head!, after := Json.str "error", cap := heartbeats }
          let tacStx ← match parse tac with
            | .ok s => pure s | .error e => return .error (s2base, e)
          let hb2 ← IO.getNumHeartbeats; let t2 ← IO.monoMsNow
          match ← runTacOn g1 tacStx with
          | .error e =>
            let hb3 ← IO.getNumHeartbeats; let t3 ← IO.monoMsNow
            let s2 : Step := { s2base with errClass := errClassOf e, err := (e.take 160).toString, heartbeats := hb3 - hb2, wallMs := t3 - t2 }
            return .error (s2, e)
          | .ok gs2 =>
            let hb3 ← IO.getNumHeartbeats; let t3 ← IO.monoMsNow
            let ids2 ← gs2.mapM (goalId · lps)
            let after2 := if gs2.isEmpty then Json.str "closed" else Json.arr (ids2.map Json.num).toArray
            let s2 : Step := { s2base with after := after2, heartbeats := hb3 - hb2, wallMs := t3 - t2 }
            if gs2.isEmpty then return .ok (#[s1, s2], mvar)
            else return .error (s2, s!"open goals: {gs2.length}")
        : MetaM (Except (Step × String) (Array Step × Expr))))
    (fun _ => do
      let hb ← IO.getNumHeartbeats; let t ← IO.monoMsNow
      let sb : Step := { cur with kind := "rung", tactic := tac, errClass := "budget", err := "budget exceeded", heartbeats := hb - hb0, wallMs := t - t0 }
      return .error (sb, "budget exceeded"))
  match r with
  | .ok (ss, mv) =>
    let pf ← instantiateMVars mv
    if pf.hasMVar || pf.hasSorry then
      return (ss.push { (ss.back!) with after := Json.str "error", errClass := "error", err := "open goals or sorry" }, .error "open goals or sorry")
    return (ss, .ok pf)
  | .error (s, e) =>
    -- a failed rung: the intros step (which succeeded iff the failure is at the
    -- rung step) followed by the failing step
    let introsStep : Step := { pos, kind := "intros", tactic := "intros", before := gid0, after := Json.arr #[Json.num s.before], cap := heartbeats }
    let ss : Array Step := if s.kind == "rung" then #[introsStep, s] else #[s]
    return (ss, .error e)

/-- Kernel check: add the term as a theorem. Returns the axioms it depends on. -/
def kernelAccept (nm : Name) (lps : List Name) (ty pf : Expr) : MetaM (Except String (Array Name)) := do
  try
    addDecl (.thmDecl { name := nm, levelParams := lps, type := ty, value := pf })
    let axs ← collectAxioms nm
    return .ok axs
  catch e => return .error (← e.toMessageData.toString)

/-- Budgeted, exception-safe type-correctness (as MutantWalk's `elaborates`). -/
def wellTyped (t : Expr) : MetaM Bool :=
  tryCatchRuntimeEx
    (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 20000000 }) do
      withCurrHeartbeats do
        try isTypeCorrect t catch _ => pure false)
    (fun _ => pure false)

/-- Run the ladder on one goal type; kernel-check a success. Returns the ATT
json (without the base fields) and the next attempt counter. -/
def attemptType (w : Walk) (n : Name) (ci : ConstantInfo) (ty : Expr) (ladder : List String) (hb k aid : Nat)
    : MetaM (Json × Nat) := do
  let emit := (← w.get).emit
  let mut rungs : Array Json := #[]
  let mut found : Option (String × Expr × Nat) := none
  let mut pos := 0
  for tac in ladder do
    if found.isSome then break
    -- Theorem statements are ∀-telescopes; every rung needs the binders
    -- introduced first. Parenthesized: `runParserCategory \`tactic` parses ONE
    -- tactic and `a; b` is a tacticSeq. The recorded script is replayed verbatim
    -- by the gate module; the transition record splits it into its two steps.
    let script := s!"(intros; {tac})"
    let (steps, res) ← tryRung w ty ci.levelParams pos tac hb
    -- the intros step is identical for every rung; record it once (pos 0)
    for s in steps do
      if s.kind == "intros" && pos > 0 then continue
      emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid)]).mergeObj s.toJson |>.compress}"
    match res with
    | .ok pf =>
      rungs := rungs.push (Json.mkObj [("tactic", Json.str script), ("ok", Json.bool true)])
      found := some (script, pf, pos)
    | .error e =>
      rungs := rungs.push (Json.mkObj [("tactic", Json.str script), ("ok", Json.bool false),
                                       ("err", Json.str (e.take 160).toString)])
    pos := pos + 1
  let ladderJ := Json.mkObj [("ladder", Json.arr rungs), ("aid", Json.num aid)]
  match found with
  | none => return (ladderJ.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found")]), k)
  | some (tac, pf, apos) =>
    let ladderJ := ladderJ.mergeObj (Json.mkObj [("accepted_pos", Json.num apos)])
    let k := k + 1
    let nm := Name.mkSimple s!"attempt_{k}"
    let used := pf.getUsedConstants
    let kres ← kernelAccept nm ci.levelParams ty pf
    let pfStr ← ppExpr pf
    let extra := match kres with
      | .ok axs => Json.mkObj [
          ("outcome", Json.str "accepted"), ("tactic", Json.str tac), ("kernel_ok", Json.bool true),
          ("axioms", Json.arr (axs.map (Json.str ·.toString))),
          ("used_consts", Json.arr (used.map (Json.str ·.toString))),
          ("uses_self", Json.bool (used.contains n)),
          ("proof_pp", Json.str (((toString pfStr).replace "\n" " ").take 4000).toString)]
      | .error e => Json.mkObj [
          ("outcome", Json.str "kernel_rejected"), ("tactic", Json.str tac), ("kernel_ok", Json.bool false),
          ("kernel_err", Json.str (e.take 300).toString),
          ("used_consts", Json.arr (used.map (Json.str ·.toString))),
          ("uses_self", Json.bool (used.contains n))]
    return (ladderJ.mergeObj extra, k)

/-- Kernel-check a found proof and build the ATT fields shared by both provers. -/
def acceptFound (n : Name) (ci : ConstantInfo) (ty : Expr) (script : String) (pf : Expr) (k : Nat)
    : MetaM (Json × Nat) := do
  let k := k + 1
  let nm := Name.mkSimple s!"attempt_{k}"
  let used := pf.getUsedConstants
  let kres ← kernelAccept nm ci.levelParams ty pf
  let pfStr ← ppExpr pf
  let extra := match kres with
    | .ok axs => Json.mkObj [
        ("outcome", Json.str "accepted"), ("tactic", Json.str script), ("kernel_ok", Json.bool true),
        ("axioms", Json.arr (axs.map (Json.str ·.toString))),
        ("used_consts", Json.arr (used.map (Json.str ·.toString))),
        ("uses_self", Json.bool (used.contains n)),
        ("proof_pp", Json.str (((toString pfStr).replace "\n" " ").take 4000).toString)]
    | .error e => Json.mkObj [
        ("outcome", Json.str "kernel_rejected"), ("tactic", Json.str script), ("kernel_ok", Json.bool false),
        ("kernel_err", Json.str (e.take 300).toString),
        ("used_consts", Json.arr (used.map (Json.str ·.toString))),
        ("uses_self", Json.bool (used.contains n))]
  return (extra, k)

/-- Search bookkeeping for the stepping prover. -/
structure Search where
  expanded : Nat := 0        -- states expanded
  deadEnds : Nat := 0        -- states where every tactic failed, or the depth cap was hit
  budgetOut : Bool := false  -- node budget exhausted
  sid : Nat := 0             -- per-attempt step id (TRANS rows carry it; the ATT lists the accepted path)
  maxDepth : Nat := 0

/-- The STEPPING prover (ladder-S): depth-first over goal lists. At each state
the step ladder is tried on the FIRST goal; a tactic that errors is a recorded
dead branch, one that makes progress recurses (remaining goals appended)
until every goal is closed, the depth cap, or the node budget. Meta state is
saved/restored around every branch so backtracking is exact. Every step is a
transition; the accepted path is returned as step ids. -/
partial def stepSearch (w : Walk) (aid : Nat) (lps : List Name) (ladder : List String) (hb depthCap : Nat)
    (budget : IO.Ref Nat) (st : IO.Ref Search) (goals : List MVarId) (depth : Nat)
    : MetaM (Option (List (String × Nat))) := do
  match goals with
  | [] => return some []
  | g :: rest =>
    let emit := (← w.get).emit
    if depth ≥ depthCap then
      st.modify fun s => { s with deadEnds := s.deadEnds + 1 }
      return none
    if (← budget.get) == 0 then
      st.modify fun s => { s with budgetOut := true }
      return none
    budget.modify (· - 1)
    st.modify fun s => { s with expanded := s.expanded + 1, maxDepth := max s.maxDepth depth }
    let env ← getEnv
    let gid ← goalId w g lps
    let mut anyProgress := false
    for tac in ladder do
      let stx ← match Parser.runParserCategory env `tactic tac "<step>" with
        | .ok s => pure s | .error _ => continue
      let saved ← Meta.saveState
      let hb0 ← IO.getNumHeartbeats; let t0 ← IO.monoMsNow
      let res ← tryCatchRuntimeEx
        (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := hb }) do
          withCurrHeartbeats do runTacOn g stx)
        (fun _ => pure (.error "budget exceeded"))
      let hb1 ← IO.getNumHeartbeats; let t1 ← IO.monoMsNow
      let sid := (← st.get).sid
      st.modify fun s => { s with sid := s.sid + 1 }
      let base : Step := { pos := depth, kind := "rung", tactic := tac, before := gid, after := Json.str "error",
                           cap := hb, heartbeats := hb1 - hb0, wallMs := t1 - t0 }
      match res with
      | .error e =>
        let cls := if e == "budget exceeded" then "budget" else errClassOf e
        let s := { base with errClass := cls, err := (e.take 160).toString }
        emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid), ("sid", Json.num sid)]).mergeObj s.toJson |>.compress}"
        saved.restore
      | .ok gs' =>
        -- a tactic that returns the same single goal made no progress: dead branch
        let ids ← gs'.mapM (goalId w · lps)
        let same := ids == [gid]
        let after := if gs'.isEmpty then Json.str "closed" else Json.arr (ids.map Json.num).toArray
        let s := { base with after := after, errClass := if same then "no_progress" else "", err := if same then "goal unchanged" else "" }
        emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid), ("sid", Json.num sid)]).mergeObj s.toJson |>.compress}"
        if same then
          saved.restore
        else
          anyProgress := true
          match ← stepSearch w aid lps ladder hb depthCap budget st (gs' ++ rest) (depth + 1) with
          | some path => return some ((tac, sid) :: path)
          | none => saved.restore
    if !anyProgress then st.modify fun s => { s with deadEnds := s.deadEnds + 1 }
    return none

/-- Stepping-prover attempt: `intros` first (recorded), then the search. -/
def attemptStep (w : Walk) (n : Name) (ci : ConstantInfo) (ty : Expr) (ladder : List String)
    (hb depthCap nodes k aid : Nat) : MetaM (Json × Nat) := do
  let emit := (← w.get).emit
  let env ← getEnv
  let mvar ← mkFreshExprMVar ty
  let g0 := mvar.mvarId!
  let gid0 ← goalId w g0 ci.levelParams
  let st ← IO.mkRef ({} : Search)
  let budget ← IO.mkRef nodes
  let introsStx ← match Parser.runParserCategory env `tactic "intros" "<step>" with
    | .ok s => pure s | .error e => throwError "intros parse: {e}"
  let hb0 ← IO.getNumHeartbeats; let t0 ← IO.monoMsNow
  let r0 ← tryCatchRuntimeEx
    (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := hb }) do
      withCurrHeartbeats do runTacOn g0 introsStx)
    (fun _ => pure (.error "budget exceeded"))
  let hb1 ← IO.getNumHeartbeats; let t1 ← IO.monoMsNow
  let goals ← match r0 with
    | .ok gs => pure gs
    | .error e =>
      let s : Step := { pos := 0, kind := "intros", tactic := "intros", before := gid0, after := Json.str "error",
                        errClass := errClassOf e, err := (e.take 160).toString, cap := hb, heartbeats := hb1 - hb0, wallMs := t1 - t0 }
      emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid), ("sid", Json.num 0)]).mergeObj s.toJson |>.compress}"
      return (Json.mkObj [("aid", Json.num aid), ("outcome", Json.str "no_proof_found"), ("search", Json.mkObj [("intros_failed", Json.bool true)])], k)
  let ids ← goals.mapM (goalId w · ci.levelParams)
  let s0 : Step := { pos := 0, kind := "intros", tactic := "intros", before := gid0,
                     after := if goals.isEmpty then Json.str "closed" else Json.arr (ids.map Json.num).toArray,
                     cap := hb, heartbeats := hb1 - hb0, wallMs := t1 - t0 }
  emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid), ("sid", Json.num 0)]).mergeObj s0.toJson |>.compress}"
  st.modify fun s => { s with sid := 1 }
  let path ← stepSearch w aid ci.levelParams ladder hb depthCap budget st goals 1
  let fin ← st.get
  let searchJ := Json.mkObj [("expanded", Json.num fin.expanded), ("dead_ends", Json.num fin.deadEnds),
                             ("budget_exhausted", Json.bool fin.budgetOut), ("max_depth", Json.num fin.maxDepth),
                             ("steps", Json.num fin.sid)]
  let baseJ := Json.mkObj [("aid", Json.num aid), ("search", searchJ)]
  match path with
  | none => return (baseJ.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found")]), k)
  | some p =>
    let pf ← instantiateMVars mvar
    if pf.hasMVar || pf.hasSorry then
      return (baseJ.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found"), ("note", Json.str "open goals or sorry after search")]), k)
    let script := "(" ++ "; ".intercalate ("intros" :: p.map (·.1)) ++ ")"
    let sids := Json.arr ((0 :: p.map (·.2)).map Json.num).toArray
    let (extra, k') ← acceptFound n ci ty script pf k
    return ((baseJ.mergeObj (Json.mkObj [("path_sids", sids), ("depth", Json.num p.length)])).mergeObj extra, k')

/-- Run one tactic on a whole goal list (main goal first), as Lean would inside
a `by` block; the remaining goals. -/
def runTacOnGoals (goals : List MVarId) (stx : Syntax) : MetaM (Except String (List MVarId)) := do
  match goals with
  | [] => return .error "no goals"
  | g :: _ =>
    try
      let gs ← Term.TermElabM.run' (ctx := {}) (s := {}) do
        Term.withoutErrToSorry do
          let gs ← Tactic.run g (do Tactic.setGoals goals; Tactic.withoutRecover (Tactic.evalTactic stx))
          Term.synthesizeSyntheticMVarsNoPostponing
          pure gs
      return .ok gs
    catch e => return .error (← e.toMessageData.toString)

/-- Split a proof script (the body of a `by` block) into its top-level tactics,
each with its source text. The script is parsed as ONE parenthesised tactic
`(script)`; the tacticSeq inside is walked. -/
def splitScript (env : Environment) (script : String) : Except String (Array (Syntax × String)) := do
  -- inside `( … )` every line of the sequence must sit at a column ≥ the first tactic's (column 1): shift the script right by one
  let wrapped := "(" ++ script.replace "\n" "\n " ++ "\n)"
  let stx ← match Parser.runParserCategory env `tactic wrapped "<script>" with
    | .ok s => pure s | .error e => throw s!"parse: {e}"
  -- paren: args = ["(", tacticSeq, ")"]; tacticSeq -> tacticSeq1Indented -> sepByIndent items (even indices)
  let seq := stx.getArg 1
  let items := (seq.getArg 0).getArg 0
  let mut out := #[]
  for i in [0:items.getNumArgs] do
    if i % 2 == 0 then
      let t := items.getArg i
      let src := match t.getPos?, t.getTailPos? with
        | some a, some b => (String.Pos.Raw.extract wrapped a b)
        | _, _ => "<?>"
      out := out.push (t, src)
  return out

/-- SCRIPT mode (tier B): replay an externally proposed proof script STEPWISE
on the demonstrandum's goal, recording every top-level tactic as a transition
(source = search, set by the driver), and returning the first failing step's
Lean error for the next round. A script that closes every goal is kernel-
checked exactly like a ladder proof; the driver then runs the external gates. -/
def attemptScript (w : Walk) (n : Name) (ci : ConstantInfo) (ty : Expr) (script : String) (hb k aid : Nat)
    : MetaM (Json × Nat) := do
  let emit := (← w.get).emit
  let env ← getEnv
  let tactics ← match splitScript env script with
    | .ok ts => pure ts
    | .error e => return (Json.mkObj [("aid", Json.num aid), ("outcome", Json.str "no_proof_found"),
                                      ("error_step", Json.num 0), ("err_class", Json.str "parse"), ("err", Json.str (e.take 600).toString)], k)
  let mvar ← mkFreshExprMVar ty
  let mut goals := [mvar.mvarId!]
  let mut failed : Option (Nat × String × String) := none
  let mut sids : Array Nat := #[]
  for i in [0:tactics.size] do
    if failed.isSome then break
    let (stx, src) := tactics[i]!
    let gidB ← goalId w goals.head! ci.levelParams
    let hb0 ← IO.getNumHeartbeats; let t0 ← IO.monoMsNow
    let res ← tryCatchRuntimeEx
      (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := hb }) do
        withCurrHeartbeats do runTacOnGoals goals stx)
      (fun _ => pure (.error "budget exceeded"))
    let hb1 ← IO.getNumHeartbeats; let t1 ← IO.monoMsNow
    let base : Step := { pos := i, kind := "script", tactic := src, before := gidB, after := Json.str "error",
                         cap := hb, heartbeats := hb1 - hb0, wallMs := t1 - t0 }
    sids := sids.push i
    match res with
    | .error e =>
      let cls := if e == "budget exceeded" then "budget" else errClassOf e
      let s := { base with errClass := cls, err := (e.take 160).toString }
      emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid), ("sid", Json.num i)]).mergeObj s.toJson |>.compress}"
      failed := some (i, cls, e)
    | .ok gs =>
      let ids ← gs.mapM (goalId w · ci.levelParams)
      let s := { base with after := if gs.isEmpty then Json.str "closed" else Json.arr (ids.map Json.num).toArray }
      emit s!"TRANS\t{(Json.mkObj [("aid", Json.num aid), ("sid", Json.num i)]).mergeObj s.toJson |>.compress}"
      goals := gs
      if gs.isEmpty && i + 1 < tactics.size then
        failed := some (i + 1, "error", "no goals to be proved (script continues after the goal closed)")
  let baseJ := Json.mkObj [("aid", Json.num aid), ("script_steps", Json.num tactics.size), ("steps_run", Json.num sids.size)]
  match failed with
  | some (i, cls, e) =>
    return (baseJ.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found"), ("error_step", Json.num i),
                                         ("err_class", Json.str cls), ("err", Json.str (e.take 1200).toString)]), k)
  | none =>
    if !goals.isEmpty then
      return (baseJ.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found"), ("error_step", Json.num tactics.size),
                                           ("err_class", Json.str "open_goals"),
                                           ("err", Json.str s!"unsolved goals: {goals.length} remain after the script")]), k)
    let pf ← instantiateMVars mvar
    if pf.hasMVar || pf.hasSorry then
      return (baseJ.mergeObj (Json.mkObj [("outcome", Json.str "no_proof_found"), ("err_class", Json.str "error"),
                                           ("err", Json.str "open metavariables or sorry in the term")]), k)
    let (extra, k') ← acceptFound n ci ty ("(" ++ script.replace "\n" "\n " ++ ")") pf k
    return ((baseJ.mergeObj (Json.mkObj [("path_sids", Json.arr (sids.map fun (i : Nat) => Json.num i))])).mergeObj extra, k')

set_option maxHeartbeats 0 in
run_meta do
  let env ← getEnv
  let limit := (((← IO.getEnv "CORPUS_LIMIT").getD "0").toNat?).getD 0
  let resumeAfter := (← IO.getEnv "CORPUS_RESUME_AFTER").getD ""
  let only := (((← IO.getEnv "CORPUS_ONLY").getD "").splitOn ",").filter (· != "")
  let sampleMod := (((← IO.getEnv "CORPUS_SAMPLE_MOD").getD "1").toNat?).getD 1
  let negate := (← IO.getEnv "CORPUS_NEGATE").getD "0" == "1"
  let mutate := (← IO.getEnv "CORPUS_MUTATE").getD "0" == "1"
  let hb := (((← IO.getEnv "ATTEMPT_HEARTBEATS").getD "20000000").toNat?).getD 20000000
  let ladder := (((← IO.getEnv "ATTEMPT_LADDER").getD "rfl,decide,simp,omega,exact?,aesop").splitOn ",").filter (· != "")
  let step := (← IO.getEnv "CORPUS_PROVER").getD "ladder" == "step"
  let scriptsPath := (← IO.getEnv "CORPUS_SCRIPTS").getD ""
  let stepDepth := (((← IO.getEnv "STEP_DEPTH").getD "4").toNat?).getD 4
  let stepNodes := (((← IO.getEnv "STEP_NODES").getD "30").toNat?).getD 30
  let outPath := (← IO.getEnv "CORPUS_OUT").getD "/dev/stdout"
  let out ← IO.FS.Handle.mk outPath IO.FS.Mode.append
  let emit (s : String) : IO Unit := do out.putStr (s ++ "\n"); out.flush
  let w : Walk ← IO.mkRef { emit }
  let mut aid := 0
  let names : Array Name := env.constants.fold (init := #[]) fun acc n ci =>
    if wanted env n ci && (only.isEmpty || only.contains n.toString)
       && (sampleMod ≤ 1 || (hash n.toString).toNat % sampleMod == 0) then acc.push n else acc
  let sorted := names.qsort fun a b => a.toString < b.toString
  if scriptsPath != "" then
    -- SCRIPT mode: one line per proposal {"id":..,"name":..,"script":..}; replayed in file order
    let lines := ((← IO.FS.readFile scriptsPath).splitOn "\n").filter (· != "")
    emit s!"INFO\t{lines.length} scripts (mode=script, heartbeats={hb})"
    let mut k := 0
    for line in lines do
      let j ← match Json.parse line with
        | .ok j => pure j | .error e => do emit s!"INFO\tBAD LINE {e}"; continue
      let some nm := (j.getObjValAs? String "name").toOption | do emit s!"INFO\tBAD LINE no name"; continue
      let some script := (j.getObjValAs? String "script").toOption | do emit s!"INFO\tBAD LINE no script"; continue
      let sid := (j.getObjValAs? String "id").toOption.getD ""
      let n := nm.toName
      emit s!"START\t{n}"
      match env.find? n with
      | none => emit s!"INFO\tVANISHED {n}"
      | some ci =>
        aid := aid + 1
        let base := Json.mkObj [("demonstrandum", Json.str n.toString), ("script_id", Json.str sid),
          ("module", Json.str ((env.getModuleFor? n).getD `_local).toString),
          ("n_levels", Json.num ci.levelParams.length), ("negated", Json.bool negate)]
        let ty := if negate then mkApp (mkConst ``Not) ci.type else ci.type
        let (r, k') ← tryCatchRuntimeEx (attemptScript w n ci ty script hb k aid)
          (fun _ => pure (Json.mkObj [("outcome", Json.str "no_proof_found"), ("budget", Json.bool true), ("aid", Json.num aid),
                                      ("err_class", Json.str "budget"), ("err", Json.str "budget exceeded")], k))
        k := k'
        emit s!"ATT\t{(base.mergeObj r).compress}"
    emit s!"INFO\tdone, {lines.length} scripts"
    return
  emit s!"INFO\t{sorted.size} demonstranda (negate={negate}, mutate={mutate}, prover={if step then "step" else "ladder"}, ladder={ladder}, depth={stepDepth}, nodes={stepNodes}, heartbeats={hb}, limit={limit})"
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
        let base := Json.mkObj [
          ("demonstrandum", Json.str n.toString),
          ("module", Json.str ((env.getModuleFor? n).getD `_local).toString),
          ("n_levels", Json.num ci.levelParams.length),
          ("negated", Json.bool negate)]
        if mutate then
          -- attempt every ELABORATED statement mutant of this theorem, built by
          -- the same shared operators as the corpus; the driver verifies the
          -- lock of `mutant_canonical` against the corpus record
          let muts ← tryCatchRuntimeEx
            (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 400000 }) do
              withCurrHeartbeats do
                try Quod.Mutate.mutantsOf ci.type catch _ => pure #[])
            (fun _ => pure #[])
          for m in muts do
            if !(← wellTyped m.ty) then continue
            let ty := if negate then mkApp (mkConst ``Not) m.ty else m.ty
            let canon ← Quod.Mutate.canonOf m.ty ci.levelParams
            aid := aid + 1
            let (j, k') ← tryCatchRuntimeEx
              (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := if step then 0 else 400000 }) do
                withCurrHeartbeats do (if step then attemptStep w n ci ty ladder hb stepDepth stepNodes k aid else attemptType w n ci ty ladder hb k aid))
              (fun _ => pure (Json.mkObj [("outcome", Json.str "no_proof_found"), ("budget", Json.bool true), ("aid", Json.num aid)], k))
            k := k'
            let mj := Json.mkObj [("mutant_operator", Json.str m.op), ("mutant_canonical", Json.str canon)]
            emit s!"ATT\t{((base.mergeObj mj).mergeObj j).compress}"
        else
          let ty := if negate then mkApp (mkConst ``Not) ci.type else ci.type
          aid := aid + 1
          let (j, k') ← tryCatchRuntimeEx
            (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := if step then 0 else 400000 }) do
              withCurrHeartbeats do (if step then attemptStep w n ci ty ladder hb stepDepth stepNodes k aid else attemptType w n ci ty ladder hb k aid))
            (fun _ => pure (Json.mkObj [("outcome", Json.str "no_proof_found"), ("budget", Json.bool true), ("aid", Json.num aid)], k))
          k := k'
          emit s!"ATT\t{(base.mergeObj j).compress}"
      emitted := emitted + 1
      if emitted % 100 == 0 then emit s!"INFO\t{emitted}/{sorted.size}"
  emit s!"INFO\tdone, {emitted} demonstranda"
