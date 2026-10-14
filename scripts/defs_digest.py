#!/usr/bin/env python3
"""defs_digest.py <project_dir> <Module.Import> <Const> [<Const> ...] [--json] [--extra-path DIR]

Definitions digest: what the names in a statement MEAN in one environment.

Starting from each constant, walks every non-standard constant reachable through
TYPES (always), VALUES (definitions; theorem proofs are excluded) and, for
inductive types, their CONSTRUCTORS' types (so a structure's fields count — the
closure survey's walk of `value?` never sees them, Q-32). For each constant it
prints the canonical pp.all form of its type and, for definitions, of its value
(binder names erased, universes renamed, as scripts/lock.py). The digest is
BLAKE3 over the sorted (name, kind, type, value) rows: two environments give the
same digest iff the same names carry the same definitions, whatever module
declares them. That is the check a statement lock cannot make on its own: a
lock hashes the statement's canonical type, in which custom constants appear by
NAME; when a challenge and an offered proof carry separate copies of the same
names (openai-ns: ComparatorChallenges.NavierStokes vs
NavierStokes.ComparatorDefinitions), lock equality says the statements read the
same and this digest says the words mean the same.

Exit 0: printed. Exit 2: usage. Exit 3: Lean failed (output shown).
"""
import hashlib
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leanenv import run_lean, extra_from_argv  # noqa: E402

STD = ["Init", "Lean", "Std", "Mathlib", "Batteries", "Aesop", "Qq",
       "ProofWidgets", "Plausible", "ImportGraph", "LeanSearchClient"]

LEAN = r'''
import __MODULE__
open Lean Meta

partial def eraseBinders : Expr → Expr
  | .forallE _ t b bi => .forallE `_ (eraseBinders t) (eraseBinders b) bi
  | .lam _ t b bi => .lam `_ (eraseBinders t) (eraseBinders b) bi
  | .letE _ t v b nd => .letE `_ (eraseBinders t) (eraseBinders v) (eraseBinders b) nd
  | .app f a => .app (eraseBinders f) (eraseBinders a)
  | .mdata _ e => eraseBinders e
  | .proj n i e => .proj n i (eraseBinders e)
  | e => e

def stdPrefixes : List Name := [__STD__]
def isStd (m : Name) : Bool := stdPrefixes.any fun p => p.isPrefixOf m

def kindOf : ConstantInfo → String
  | .thmInfo _ => "theorem" | .defnInfo _ => "def" | .axiomInfo _ => "axiom"
  | .opaqueInfo _ => "opaque" | .inductInfo _ => "inductive" | .ctorInfo _ => "ctor"
  | .recInfo _ => "rec" | .quotInfo _ => "quot"

def canon (ci : ConstantInfo) (e : Expr) : MetaM String := do
  let k := ci.levelParams.length
  let us := (List.range k).map fun i => Level.param (Name.mkSimple s!"u_{i}")
  let t := eraseBinders (e.instantiateLevelParams ci.levelParams us)
  let fmt ← withOptions (fun o => ((o.setBool `pp.all true).setBool `pp.universes true).setBool `pp.fullNames true) do
    ppExpr t
  return toString fmt

/-- Non-std constants reachable from the roots through types, definition values
and constructor types; recursors are reached through their types only. -/
partial def walk (env : Environment) (seen : NameSet) (todo : List Name) (out : Array Name) : Array Name :=
  match todo with
  | [] => out
  | n :: rest =>
    if seen.contains n then walk env seen rest out else
    let seen := seen.insert n
    match env.find? n with
    | none => walk env seen rest (out.push n)
    | some ci =>
      let m := (env.getModuleFor? n).getD `_local
      if isStd m then walk env seen rest out else
      let fromType := ci.type.getUsedConstants.toList
      let fromValue := match ci with
        | .thmInfo _ => []
        | .defnInfo v => v.value.getUsedConstants.toList
        | .opaqueInfo v => v.value.getUsedConstants.toList
        | _ => []
      let fromCtors := match ci with
        | .inductInfo v => v.ctors
        | _ => []
      walk env seen (fromType ++ fromValue ++ fromCtors ++ rest) (out.push n)

run_meta do
  let env ← getEnv
  let names := walk env {} [__ROOTS__] #[]
  for n in names do
    match env.find? n with
    | none => IO.println s!"DEF {n} missing _none"
    | some ci =>
      let m := (env.getModuleFor? n).getD `_local
      IO.println s!"DEF {n} {kindOf ci} {m}"
      IO.println "TYPE-BEGIN"
      IO.println (← canon ci ci.type)
      IO.println "TYPE-END"
      match ci with
      | .defnInfo v =>
        IO.println "VALUE-BEGIN"
        IO.println (← canon ci v.value)
        IO.println "VALUE-END"
      | _ => pure ()
  IO.println "DONE"
'''


def parse(out: str) -> list[dict]:
    rows, cur, buf, mode = [], None, [], None
    for l in out.splitlines():
        if l.startswith("DEF "):
            _, n, k, m = l.split()[:4]
            cur = {"name": n, "kind": k, "module": m, "type": None, "value": None}; rows.append(cur)
        elif l in ("TYPE-BEGIN", "VALUE-BEGIN"):
            mode, buf = l.split("-")[0].lower(), []
        elif l in ("TYPE-END", "VALUE-END"):
            cur[mode] = re.sub(r"\s+", " ", "\n".join(buf)).strip(); mode = None
        elif mode:
            buf.append(l)
    return rows


def digest(rows: list[dict]) -> str:
    """BLAKE3 of the sorted (name, kind, type, value) rows; modules are not part of it."""
    body = json.dumps(sorted([r["name"], r["kind"], r.get("type"), r.get("value")] for r in rows), ensure_ascii=False)
    try:
        import blake3  # type: ignore
        return blake3.blake3(body.encode()).hexdigest()
    except ImportError:
        return hashlib.blake2b(body.encode(), digest_size=32).hexdigest()


def compare(a: list[dict], b: list[dict]) -> dict:
    """Which names differ between two digests' rows, and how."""
    ra, rb = {r["name"]: r for r in a}, {r["name"]: r for r in b}
    only_a, only_b = sorted(set(ra) - set(rb)), sorted(set(rb) - set(ra))
    differ = sorted(n for n in set(ra) & set(rb)
                    if (ra[n]["kind"], ra[n].get("type"), ra[n].get("value")) != (rb[n]["kind"], rb[n].get("type"), rb[n].get("value")))
    return {"equal": not (only_a or only_b or differ), "only_a": only_a, "only_b": only_b, "differ": differ,
            "digest_a": digest(a), "digest_b": digest(b)}


def main() -> int:
    argv = sys.argv[1:]
    skip = {i + 1 for i, a in enumerate(argv) if a == "--extra-path"}
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in skip]
    if len(args) < 3:
        print(__doc__); return 2
    proj, module, roots = args[0], args[1], args[2:]
    src = (LEAN.replace("__MODULE__", module).replace("__STD__", ", ".join("`" + s for s in STD))
           .replace("__ROOTS__", ", ".join("`" + r for r in roots)))
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=proj, delete=False) as f:
        f.write(src); path = f.name
    try:
        r = run_lean(proj, path, extra_from_argv(sys.argv))
    finally:
        os.unlink(path)
    if r.returncode != 0 or "DONE" not in r.stdout:
        sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); return 3
    rows = parse(r.stdout)
    rep = {"module": module, "roots": roots, "constants": len(rows), "digest": digest(rows),
           "missing": [x["name"] for x in rows if x["kind"] == "missing"],
           "modules": sorted({x["module"] for x in rows}), "rows": rows}
    if "--json" in sys.argv:
        print(json.dumps(rep, indent=1, ensure_ascii=False))
    else:
        print(f"digest {rep['digest']} over {len(rows)} constants from {module} ({', '.join(rep['modules'])})")
        for x in rows:
            print(f"  {x['kind']:9} {x['name']}  ({x['module']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
