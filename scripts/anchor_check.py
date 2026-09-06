#!/usr/bin/env python3
"""anchor_check.py <project_dir> <Module.Import> <Anchor.Decl> <Custom.Constant> [--json]

Anchor shape gate. An anchor for a custom constant `c` is admissible only if,
after stripping its binders, its statement is `c x₁ … xₖ = rhs` or
`c x₁ … xₖ ↔ rhs` where the xᵢ are distinct bound variables (so the anchor is
the general definitional bridge, not a special case) and `rhs` does not
mention `c`. The constants of `rhs` are reported; the caller must see every
custom one anchored in turn (the chain has to end in the pinned libraries).

Without this gate the anchor table is a hand-typed map that nothing checks,
and any rfl lemma under any name would launder any constant.

Exit 0: admissible. Exit 1: not admissible (reason printed). Exit 3: Lean failed.
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

run_meta do
  let env ← getEnv
  let c : Name := `__CONST__
  let ci ← getConstInfo `__ANCHOR__
  let res ← forallTelescope ci.type fun _ body => do
    let body := body.consumeMData
    let some (lhs, rhs, k) := (match body.getAppFnArgs with
      | (``Eq, #[_, l, r]) => some (l, r, "Eq")
      | (``Iff, #[l, r]) => some (l, r, "Iff")
      | _ => none) | return "ANCHOR-BAD head is not Eq or Iff"
    let lhs := lhs.consumeMData
    unless lhs.getAppFn.isConstOf c do
      return s!"ANCHOR-BAD lhs head is {lhs.getAppFn} not {c}"
    let args := lhs.getAppArgs
    unless args.all (·.isFVar) do return "ANCHOR-BAD lhs applied to non-variable arguments"
    let ids := (args.map (·.fvarId!)).toList
    unless ids.eraseDups.length == ids.length do return "ANCHOR-BAD lhs repeats a variable"
    let consts := rhs.getUsedConstants
    if consts.contains c then return "ANCHOR-BAD rhs mentions the constant"
    let mut out := s!"ANCHOR-OK {k} args {args.size}"
    for d in consts do
      let m := (env.getModuleFor? d).getD `_local
      out := out ++ s!"\nCONST {d} {m} {if isStd m then "std" else "custom"}"
    return out
  IO.println res
'''


def main() -> int:
    argv = sys.argv[1:]
    skip = {i + 1 for i, a in enumerate(argv) if a == "--extra-path"}
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in skip]
    if len(args) != 4:
        print(__doc__); return 2
    proj, module, anchor, const = args
    src = (LEAN.replace("__MODULE__", module).replace("__ANCHOR__", anchor)
           .replace("__CONST__", const).replace("__STD__", ", ".join("`" + s for s in STD)))
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=proj, delete=False) as f:
        f.write(src); path = f.name
    try:
        r = run_lean(proj, path, extra_from_argv(sys.argv))
    finally:
        os.unlink(path)
    out = r.stdout
    if r.returncode != 0 or "ANCHOR-" not in out:
        sys.stdout.write(out); sys.stderr.write(r.stderr); return 3
    ok = "ANCHOR-OK" in out
    reason = next(l for l in out.splitlines() if l.startswith("ANCHOR-"))
    consts = [l.split()[1:] for l in out.splitlines() if l.startswith("CONST ")]
    custom = [{"name": n, "module": m} for n, m, k in consts if k == "custom"]
    res = {"anchor": anchor, "constant": const, "ok": ok, "reason": reason,
           "rhs_constants": len(consts), "rhs_custom": custom}
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        print(reason + (f"  rhs constants {len(consts)} custom {len(custom)}" if ok else ""))
        for x in custom: print(f"  custom {x['name']}  ({x['module']})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
