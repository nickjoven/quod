#!/usr/bin/env python3
"""refute_check.py <project_dir> <Ref.Module> <Refutation.Decl> <Claim.Module> <Claim.Decl> [--json]

Refutation shape gate. A `refuted_by` row in the runner is a nomination.
It is admissible only if the nominated declaration's type is `¬ T` (or
`T → False`) where T's canonical form (same canonicalization as lock.py:
level params renamed, binder names erased, pp.all) is byte-identical to the
claim's canonical type. Both modules are imported so both declarations are visible. Axiom cleanliness of the refutation is checked separately.

Without this gate any clean theorem under any name could mark any claim
`refuted` (control N8).

Exit 0: admissible. Exit 1: not. Exit 3: Lean failed.
"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leanenv import run_lean, extra_from_argv

LEAN = r'''
import __MODULE__
import __CMODULE__
open Lean Meta

partial def eraseBinders : Expr → Expr
  | .forallE _ t b bi => .forallE `_ (eraseBinders t) (eraseBinders b) bi
  | .lam _ t b bi => .lam `_ (eraseBinders t) (eraseBinders b) bi
  | .letE _ t v b nd => .letE `_ (eraseBinders t) (eraseBinders v) (eraseBinders b) nd
  | .app f a => .app (eraseBinders f) (eraseBinders a)
  | .mdata _ e => eraseBinders e
  | .proj n i e => .proj n i (eraseBinders e)
  | e => e

def canon (ci : ConstantInfo) (t : Expr) : MetaM String := do
  let k := ci.levelParams.length
  let us := (List.range k).map fun i => Level.param (Name.mkSimple s!"u_{i}")
  let t := eraseBinders (t.instantiateLevelParams ci.levelParams us)
  let fmt ← withOptions (fun o => ((o.setBool `pp.all true).setBool `pp.universes true).setBool `pp.fullNames true) do
    ppExpr t
  return toString fmt

run_meta do
  let r ← getConstInfo `__REF__
  let c ← getConstInfo `__CLAIM__
  let rt := r.type.consumeMData
  let negated? : Option Expr :=
    match rt.getAppFnArgs with
    | (``Not, #[t]) => some t
    | _ => match rt with
      | .forallE _ t (.const ``False []) _ => some t
      | _ => none
  match negated? with
  | none => IO.println "REFUTE-BAD refutation type is not a negation"
  | some t =>
    let a ← canon r t
    let b ← canon c c.type
    IO.println "CANON-REF-BEGIN"; IO.println a; IO.println "CANON-REF-END"
    IO.println "CANON-CLAIM-BEGIN"; IO.println b; IO.println "CANON-CLAIM-END"
    if a == b then IO.println "REFUTE-OK negated statement equals the claim"
    else IO.println "REFUTE-BAD negated statement differs from the claim"
'''


def main() -> int:
    argv = sys.argv[1:]
    skip = {i + 1 for i, a in enumerate(argv) if a == "--extra-path"}
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in skip]
    if len(args) != 5:
        print(__doc__); return 2
    proj, module, ref, cmodule, claim = args
    src = (LEAN.replace("__MODULE__", module).replace("__CMODULE__", cmodule)
           .replace("__REF__", ref).replace("__CLAIM__", claim))
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=proj, delete=False) as f:
        f.write(src); path = f.name
    try:
        r = run_lean(proj, path, extra_from_argv(sys.argv))
    finally:
        os.unlink(path)
    out = r.stdout
    if r.returncode != 0 or "REFUTE-" not in out:
        sys.stdout.write(out); sys.stderr.write(r.stderr); return 3
    ok = "REFUTE-OK" in out
    reason = next(l for l in out.splitlines() if l.startswith("REFUTE-"))
    res = {"refutation": ref, "claim": claim, "ok": ok, "reason": reason}
    print(json.dumps(res, indent=1) if "--json" in sys.argv else reason)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
