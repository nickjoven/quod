#!/usr/bin/env python3
"""lock.py <project_dir> <Module.Import> <Decl.Name> [--json]

Statement lock (L1): the canonical elaborated type of a declaration and the
transitive constants in that type that are NOT from the pinned standard
libraries. Runs a Lean meta script inside the project's own environment
(`lake env lean`), so the pin is the project's pin.

Canonical form: pp.all, universes printed and renamed to u_0.., binder
names erased, mdata dropped. lock = BLAKE3 (falls back to BLAKE2b and says
so) of the UTF-8 canonical string.

Exit 0: printed lock. Exit 2: usage. Exit 3: Lean failed (output shown).
"""
import hashlib, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leanenv import run_lean, extra_from_argv

STD = ["Init", "Lean", "Std", "Mathlib", "Batteries", "Aesop", "Qq",
       "ProofWidgets", "Plausible", "ImportGraph", "LeanSearchClient"]

LEAN = r'''
import {module}
open Lean Meta

partial def eraseBinders : Expr → Expr
  | .forallE _ t b bi => .forallE `_ (eraseBinders t) (eraseBinders b) bi
  | .lam _ t b bi => .lam `_ (eraseBinders t) (eraseBinders b) bi
  | .letE _ t v b nd => .letE `_ (eraseBinders t) (eraseBinders v) (eraseBinders b) nd
  | .app f a => .app (eraseBinders f) (eraseBinders a)
  | .mdata _ e => eraseBinders e
  | .proj n i e => .proj n i (eraseBinders e)
  | e => e

def stdPrefixes : List Name := [{std}]

def isStd (m : Name) : Bool := stdPrefixes.any fun p => p.isPrefixOf m

run_meta do
  let env ← getEnv
  let n : Name := {decl}
  let ci ← getConstInfo n
  let k := ci.levelParams.length
  let us := (List.range k).map fun i => Level.param (Name.mkSimple s!"u_{{i}}")
  let t := eraseBinders (ci.type.instantiateLevelParams ci.levelParams us)
  let fmt ← withOptions (fun o => ((o.setBool `pp.all true).setBool `pp.universes true).setBool `pp.fullNames true) do
    ppExpr t
  IO.println "LOCKTYPE-BEGIN"
  IO.println (toString fmt)
  IO.println "LOCKTYPE-END"
  -- unfold the head of the statement through every definition: a claim whose
  -- type is `True` behind a name is not a claim
  let tw ← withTransparency .all (whnf ci.type)
  IO.println s!"WHNF-IS-TRUE {{tw.isConstOf ``True}}"
  let consts := t.getUsedConstants
  for c in consts do
    let m := (env.getModuleFor? c).getD `_local
    IO.println s!"CONST {{c}} {{m}} {{if isStd m then "std" else "custom"}}"
  match ci with
  | .thmInfo _ => IO.println "KIND theorem"
  | .defnInfo _ => IO.println "KIND def"
  | .axiomInfo _ => IO.println "KIND axiom"
  | .opaqueInfo _ => IO.println "KIND opaque"
  | _ => IO.println "KIND other"
'''


def main() -> int:
    argv = sys.argv[1:]
    skip = {i + 1 for i, a in enumerate(argv) if a == "--extra-path"}
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in skip]
    if len(args) != 3:
        print(__doc__); return 2
    proj, module, decl = args
    src = LEAN.format(module=module, decl="`" + decl,
                      std=", ".join("`" + s for s in STD))
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=proj, delete=False) as f:
        f.write(src); path = f.name
    try:
        r = run_lean(proj, path, extra_from_argv(sys.argv))
    finally:
        os.unlink(path)
    if r.returncode != 0 or "LOCKTYPE-END" not in r.stdout:
        sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); return 3
    out = r.stdout
    canon = out.split("LOCKTYPE-BEGIN\n", 1)[1].split("\nLOCKTYPE-END", 1)[0]
    canon = re.sub(r"\s+", " ", canon).strip()
    try:
        import blake3  # type: ignore
        h = blake3.blake3(canon.encode()).hexdigest(); algo = "blake3"
    except ImportError:
        h = hashlib.blake2b(canon.encode(), digest_size=32).hexdigest(); algo = "blake2b"
    consts = [l.split()[1:] for l in out.splitlines() if l.startswith("CONST ")]
    kind = [l.split()[1] for l in out.splitlines() if l.startswith("KIND ")][0]
    custom = [{"name": c, "module": m} for c, m, k in consts if k == "custom"]
    res = {"decl": decl, "module": module, "kind": kind, "lock": h, "hash": algo,
           "canonical_type": canon, "constants": len(consts), "custom_constants": custom,
           "reduces_to_True": "WHNF-IS-TRUE true" in out}
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        print(f"lock {h} ({algo}) {decl} [{kind}] constants {len(consts)} custom {len(custom)}"
              + ("  TYPE UNFOLDS TO True" if res["reduces_to_True"] else ""))
        for c in custom: print(f"  custom {c['name']}  ({c['module']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
