#!/usr/bin/env python3
"""closure.py <project_dir> <Module.Import> <Const> [<Const> ...] [--json]

Definitional closure survey. Starting from each constant, walks the constants
of its TYPE and, for definitions/structures/inductives/opaques, of its VALUE,
stopping at the pinned standard libraries (Mathlib, Lean core, ...). Reports:
  custom      non-std constants reached, with kind and module
  axioms      non-std axioms reached (any = not grounded)
  opaque      opaque constants reached (any = not grounded)
  sorry       sorryAx reached inside a definition (not grounded)
  grounded    every path ends in a std library and none of the above occurred
`grounded` says the notion is DEFINED in library terms with nothing hidden;
it says nothing about fidelity to a named problem (that is an anchor Iff).
Theorems reached inside definitions contribute their types only, not proofs.

Exit 0 always on Lean success (the report is the output). Exit 3: Lean failed.
"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leanenv import run_lean, extra_from_argv

STD = ["Init", "Lean", "Std", "Mathlib", "Batteries", "Aesop", "Qq",
       "ProofWidgets", "Plausible", "ImportGraph", "LeanSearchClient"]

LEAN = r'''
import __MODULE__
open Lean Meta

def stdPrefixes : List Name := [__STD__]
def isStd (m : Name) : Bool := stdPrefixes.any fun p => p.isPrefixOf m

def kindOf : ConstantInfo → String
  | .thmInfo _ => "theorem" | .defnInfo _ => "def" | .axiomInfo _ => "axiom"
  | .opaqueInfo _ => "opaque" | .inductInfo _ => "inductive" | .ctorInfo _ => "ctor"
  | .recInfo _ => "rec" | .quotInfo _ => "quot"

partial def walk (env : Environment) (seen : NameSet) (todo : List Name)
    (out : Array (Name × String × Name)) : Array (Name × String × Name) :=
  match todo with
  | [] => out
  | n :: rest =>
    if seen.contains n then walk env seen rest out else
    let seen := seen.insert n
    match env.find? n with
    | none => walk env seen rest (out.push (n, "missing", `_none))
    | some ci =>
      let m := (env.getModuleFor? n).getD `_local
      if isStd m then walk env seen rest out else
      let k := kindOf ci
      let next := ci.type.getUsedConstants.toList ++
        (match ci with
         | .thmInfo _ => []
         | _ => (ci.value?.map (·.getUsedConstants.toList)).getD [])
      walk env seen (next ++ rest) (out.push (n, k, m))

run_meta do
  let env ← getEnv
  for root in [__ROOTS__] do
    let res := walk env {} [root] #[]
    IO.println s!"ROOT {root}"
    for (n, k, m) in res do
      IO.println s!"  C {n} {k} {m}"
    -- std axioms reachable through the whole closure (proofs excluded)
    IO.println "END"
'''


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
    if r.returncode != 0 or "ROOT " not in r.stdout:
        sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); return 3
    reports, cur = [], None
    for l in r.stdout.splitlines():
        if l.startswith("ROOT "):
            cur = {"root": l.split()[1], "custom": [], "axioms": [], "opaque": [], "missing": [], "sorry": False}
            reports.append(cur)
        elif l.startswith("  C ") and cur is not None:
            n, k, m = l.split()[1:4]
            if n == cur["root"]:
                cur["root_kind"] = k; cur["root_module"] = m
            if n == "sorryAx":
                cur["sorry"] = True; continue
            cur["custom"].append({"name": n, "kind": k, "module": m})
            if k == "axiom": cur["axioms"].append(n)
            if k == "opaque": cur["opaque"].append(n)
            if k == "missing": cur["missing"].append(n)
    for rep in reports:
        rep["grounded"] = not (rep["axioms"] or rep["opaque"] or rep["missing"] or rep["sorry"])
        mods = sorted({c["module"].split(".")[0] for c in rep["custom"]})
        rep["top_level_modules"] = mods
    if "--json" in sys.argv:
        print(json.dumps(reports, indent=1, ensure_ascii=False))
    else:
        for rep in reports:
            print(f"{rep['root']} [{rep.get('root_kind','?')}] custom {len(rep['custom'])} "
                  f"grounded={rep['grounded']} modules={rep['top_level_modules']}"
                  + (f" axioms={rep['axioms']}" if rep["axioms"] else "")
                  + (f" opaque={rep['opaque']}" if rep["opaque"] else "")
                  + (" SORRY-IN-DEFINITION" if rep["sorry"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
