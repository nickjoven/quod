/- CorpusWalk.lean — the Q-13 batch runner as a corpus extractor.

One Lean process imports Mathlib once and walks the whole environment,
emitting one JSON line per declaration. The canonicalization is a verbatim
copy of the pipeline embedded in scripts/lock.py (eraseBinders, universes
renamed to u_0.., pp.all + pp.universes + pp.fullNames); the BLAKE3 lock is
computed by the Python driver over the whitespace-normalized string so the
hash stays byte-identical to lock.py's. corpus_extract.py --selftest holds
the two implementations to field-exact agreement before any full run.

Driven by `lake env lean scripts/CorpusWalk.lean` from the calib project.
Environment variables (a lean script gets no argv through lake):
  CORPUS_LIMIT         stop after N emitted declarations (0 = no limit)
  CORPUS_RESUME_AFTER  skip until after this declaration name
  CORPUS_ONLY          comma-separated declaration names; emit exactly these
Markers: each record line is prefixed DECL\t; progress goes to stderr. -/
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

def stdPrefixes : List Name := [`Init, `Lean, `Std, `Mathlib, `Batteries, `Aesop, `Qq,
  `ProofWidgets, `Plausible, `ImportGraph, `LeanSearchClient]

def isStd (m : Name) : Bool := stdPrefixes.any fun p => p.isPrefixOf m

def kindOf : ConstantInfo → String
  | .thmInfo _ => "theorem"
  | .defnInfo _ => "def"
  | .axiomInfo _ => "axiom"
  | .opaqueInfo _ => "opaque"
  | .inductInfo _ => "inductive"
  | _ => "other"

/-- Declarations the corpus wants: public theorems/defs/axioms/opaques/inductives
declared in a Mathlib module, no compiler-generated auxiliaries. -/
def wanted (env : Environment) (n : Name) (ci : ConstantInfo) : Bool :=
  !n.isInternal
  && kindOf ci != "other"
  && !(`Mathlib.Tactic).isPrefixOf ((env.getModuleFor? n).getD `_local)
  && (match env.getModuleFor? n with
      | some m => (`Mathlib).isPrefixOf m
      | none => false)

def ppCanonical (ci : ConstantInfo) : MetaM String := do
  let k := ci.levelParams.length
  let us := (List.range k).map fun i => Level.param (Name.mkSimple s!"u_{i}")
  let t := eraseBinders (ci.type.instantiateLevelParams ci.levelParams us)
  let fmt ← withOptions (fun o =>
      ((o.setBool `pp.all true).setBool `pp.universes true).setBool `pp.fullNames true) do
    ppExpr t
  return toString fmt

def emitDecl (env : Environment) (n : Name) (ci : ConstantInfo) : MetaM Json := do
  let canon ← ppCanonical ci
  -- whnf through every definition: `True` behind a grand name is not a claim.
  -- Capped at ~2e7 heartbeats (1/10th of lock.py's default) and freshly
  -- counted: a trivial `True` unfolds in a handful of steps, so anything that
  -- burns this budget is by definition NOT trivially True and is recorded as
  -- "timeout" in ~1-2s rather than spinning for minutes. lock.py can afford
  -- the full default because it is run one hand-picked decl at a time; a walk
  -- over all 318k cannot — one expensive reduction would stall the whole run.
  let reduces : Json ←
    tryCatchRuntimeEx
      (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 20000000 }) do
        withCurrHeartbeats do
          let tw ← withTransparency .all (whnf ci.type)
          pure (Json.bool (tw.isConstOf ``True)))
      (fun _ => pure (Json.str "timeout"))
  -- explicit Prop binders are the hypotheses descriptor (elaborated type, so
  -- `variable`-introduced binders are visible — the Q-6 blind spot).
  let (hyps, iffSides) ← forallTelescope ci.type fun xs body => do
    let mut hs : Array Json := #[]
    for x in xs do
      let d ← x.fvarId!.getDecl
      if d.binderInfo == .default && (← isProp d.type) then
        let tyFmt ← ppExpr d.type
        hs := hs.push (Json.str ((toString tyFmt).replace "\n" " "))
    let sides ← match body.iff? with
      | some (lhs, rhs) => do
          let l ← ppExpr lhs
          let r ← ppExpr rhs
          pure (some (toString l, toString r))
      | none => pure none
    return (hs, sides)
  let consts := (eraseBinders (ci.type.instantiateLevelParams ci.levelParams
      ((List.range ci.levelParams.length).map fun i =>
        Level.param (Name.mkSimple s!"u_{i}")))).getUsedConstants
  let mut stdC : Array Json := #[]
  let mut customC : Array Json := #[]
  for c in consts do
    let m := (env.getModuleFor? c).getD `_local
    if isStd m then stdC := stdC.push (Json.str c.toString)
    else customC := customC.push (Json.str c.toString)
  let proofConsts : Array Json := match ci.value? with
    | some v => v.getUsedConstants.map (Json.str ·.toString)
    | none => #[]
  let axioms ← collectAxioms n
  let doc ← findDocString? env n
  return Json.mkObj [
    ("name", Json.str n.toString),
    ("module", Json.str ((env.getModuleFor? n).getD `_local).toString),
    ("kind", Json.str (kindOf ci)),
    ("canonical_type", Json.str canon),
    ("type_consts_std", Json.arr stdC),
    ("type_consts_custom", Json.arr customC),
    ("proof_consts", Json.arr proofConsts),
    ("axioms", Json.arr (axioms.map (Json.str ·.toString))),
    ("hypotheses", Json.arr hyps),
    ("reduces_to_true", reduces),
    ("docstring", match doc with | some s => Json.str s | none => Json.null),
    ("iff_lhs", match iffSides with | some (l, _) => Json.str l | none => Json.null),
    ("iff_rhs", match iffSides with | some (_, r) => Json.str r | none => Json.null)]

-- The walk is one command; its own budget must be unlimited (per-decl work
-- is capped individually above and below).
set_option maxHeartbeats 0 in
run_meta do
  let env ← getEnv
  let limit := (((← IO.getEnv "CORPUS_LIMIT").getD "0").toNat?).getD 0
  let resumeAfter := (← IO.getEnv "CORPUS_RESUME_AFTER").getD ""
  let only := (((← IO.getEnv "CORPUS_ONLY").getD "").splitOn ",").filter (· != "")
  -- Select by folding the env, keeping only Names (not the ConstantInfo
  -- pairs): the umbrella environment is already ~9 GB resident, and the old
  -- `env.constants.toList` materialized all ~330k constants into a List on
  -- top of it — a transient spike that OOM-killed the process at 14.9 GB RSS
  -- before a single record was emitted (2026-09-07). ConstantInfo is looked
  -- up lazily during the walk, where it is used once and freed.
  let names : Array Name := env.constants.fold (init := #[]) fun acc n ci =>
    if wanted env n ci && (only.isEmpty || only.contains n.toString) then acc.push n
    else acc
  -- deterministic order (Python-string sort): resume and sharding depend on it
  let sorted := names.qsort fun a b => a.toString < b.toString
  -- Write to an EXPLICITLY-OPENED file handle (path from CORPUS_OUT), flushed
  -- after every line. Neither stdout nor stderr redirected to a file flushes
  -- incrementally here: a separate `2>file` was empty even after a clean exit,
  -- and stdout `>file` only appeared on process exit — so a watchdog SIGKILL
  -- lost everything and could never see progress. An explicit Handle.flush is
  -- reliable. Fall back to /dev/stdout when CORPUS_OUT is unset (standalone).
  let outPath := (← IO.getEnv "CORPUS_OUT").getD "/dev/stdout"
  let out ← IO.FS.Handle.mk outPath IO.FS.Mode.append
  let emit (s : String) : IO Unit := do out.putStr (s ++ "\n"); out.flush
  let mut emitted := 0
  let mut skipping := resumeAfter != ""
  emit s!"INFO\t{sorted.size} declarations selected (limit={limit}, resumeAfter={resumeAfter})"
  for n in sorted do
    if skipping then
      if n.toString == resumeAfter then skipping := false
    else
      if limit > 0 && emitted ≥ limit then break
      -- Announce the declaration BEFORE processing it: some types explode under
      -- `pp.all` (ppExpr is not reliably heartbeat-checked), so the per-decl cap
      -- below cannot bound them. The driver's wall-clock watchdog learns which
      -- declaration hung from this START line and resumes past exactly that one.
      emit s!"START\t{n}"
      match env.find? n with
      | none => emit s!"INFO\tVANISHED {n}"
      | some ci =>
        -- Per-declaration budget (400k heartbeats): a legit declaration
        -- processes well within it, a heartbeat-checked runaway (whnf) trips
        -- in ~1-2s and is downgraded to a logged skip.
        tryCatchRuntimeEx
          (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 400000 }) do
            withCurrHeartbeats do
              try
                let js ← emitDecl env n ci
                emit s!"DECL\t{js.compress}"
              catch e =>
                emit s!"INFO\tERROR {n}: {← e.toMessageData.toString}")
          (fun _ => emit s!"INFO\tBUDGET {n}: declaration exceeded its heartbeat cap")
      emitted := emitted + 1
      if emitted % 1000 == 0 then emit s!"INFO\t{emitted}/{sorted.size}"
  emit s!"INFO\tdone, {emitted} emitted"
