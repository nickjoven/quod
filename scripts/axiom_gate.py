#!/usr/bin/env python3
"""axiom_gate.py <project_dir> <Module.Import> <Decl.Name>... [--json]

The axiom gate that can fail. Runs `#print axioms` for each declaration
inside the project's environment and FAILS unless every declaration's axiom
set is a subset of {propext, Classical.choice, Quot.sound}. `sorryAx` fails.
A declaration that does not exist fails (Lean error).

Exit 0: all clean. Exit 1: at least one declaration outside the triple.
Exit 3: Lean failed. Prints one line per declaration and the raw output
block so the record can be stored by CID.
"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leanenv import run_lean, extra_from_argv

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def main() -> int:
    argv = sys.argv[1:]
    skip = {i + 1 for i, a in enumerate(argv) if a == "--extra-path"}
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in skip]
    if len(args) < 3:
        print(__doc__); return 2
    proj, module, decls = args[0], args[1], args[2:]
    src = f"import {module}\n" + "".join(f"#print axioms {d}\n" for d in decls)
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=proj, delete=False) as f:
        f.write(src); path = f.name
    try:
        r = run_lean(proj, path, extra_from_argv(sys.argv))
    finally:
        os.unlink(path)
    if r.returncode != 0:
        sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)
        print("axiom gate: LEAN ERROR"); return 3
    results, bad = [], False
    for d in decls:
        m = re.search(rf"'{re.escape(d)}' depends on axioms: \[([^\]]*)\]", r.stdout)
        if m:
            axs = {a.strip() for a in m.group(1).split(",") if a.strip()}
        elif re.search(rf"'{re.escape(d)}' does not depend on any axioms", r.stdout):
            axs = set()
        else:
            axs = {"<unparsed>"}
        extra = sorted(axs - ALLOWED)
        ok = not extra
        bad |= not ok
        results.append({"decl": d, "axioms": sorted(axs), "extra": extra, "ok": ok})
        print(f"{'ok  ' if ok else 'FAIL'} {d}: {sorted(axs)}" + (f"  EXTRA {extra}" if extra else ""))
    if "--json" in sys.argv:
        print(json.dumps({"results": results, "raw": r.stdout}, indent=1))
    print("axiom gate:", "FAIL" if bad else "clean", f"({len(decls)} declaration(s))")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
