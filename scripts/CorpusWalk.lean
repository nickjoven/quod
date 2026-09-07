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
  -- whnf through every definition: `True` behind a grand name is not a
  -- claim. Fresh 200k-heartbeat budget per call (the same limit lock.py's
  -- one-decl command gives it); blowing it is caught as a runtime exception
  -- and recorded as "timeout", never fatal.
  let reduces : Json ←
    tryCatchRuntimeEx
      (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 200000 * 1000 }) do
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
  let mut names : Array (Name × ConstantInfo) := #[]
  for (n, ci) in env.constants.toList do
    if wanted env n ci then
      if only.isEmpty || only.contains n.toString then
        names := names.push (n, ci)
  -- deterministic order: resume and sharding depend on it
  let sorted := names.qsort fun a b => a.1.toString < b.1.toString
  let mut emitted := 0
  let mut skipping := resumeAfter != ""
  IO.eprintln s!"corpus-walk: {sorted.size} declarations selected"
  for (n, ci) in sorted do
    if skipping then
      if n.toString == resumeAfter then skipping := false
    else
      if limit > 0 && emitted ≥ limit then break
      -- Per-declaration budget: generous but finite, freshly counted, with
      -- both normal and runtime exceptions downgraded to a logged skip.
      tryCatchRuntimeEx
        (withTheReader Core.Context (fun ctx => { ctx with maxHeartbeats := 1000000 * 1000 }) do
          withCurrHeartbeats do
            try
              let js ← emitDecl env n ci
              IO.println s!"DECL\t{js.compress}"
            catch e =>
              IO.eprintln s!"corpus-walk: ERROR {n}: {← e.toMessageData.toString}")
        (fun _ => IO.eprintln s!"corpus-walk: BUDGET {n}: declaration exceeded its heartbeat cap")
      emitted := emitted + 1
      if emitted % 1000 == 0 then IO.eprintln s!"corpus-walk: {emitted}/{sorted.size}"
  IO.eprintln s!"corpus-walk: done, {emitted} emitted"
