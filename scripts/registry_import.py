#!/usr/bin/env python3
"""registry_import.py [--no-ket]

Imports the Millennium registry (millennium/PIN.yml) as claims: runs the same
gates as calibrate.evaluate on each `clay_prize_*` declaration at the
registry's own pin (own Lake project, own lean4checker build), writes
claims/millennium/<slug>.yml with the COMPUTED status and
millennium/RESULTS.json. Expected on import: every declaration `stated`
(bodies are sorry), custom constants listed, none anchored yet. Exit 0 iff
every declaration got a lock (a status of any kind); exit 1 if any lock
failed, which means the pin or the build is wrong, not the mathematics.
"""
import json, os, sys, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibrate as C

ROOT = C.ROOT
MILL = os.path.join(ROOT, "millennium")
REG = os.path.join(MILL, "registry")
CHECKER = os.path.join(MILL, "lean4checker", ".lake", "build", "bin", "lean4checker")


def module_of(decl):
    """Find the registry module declaring `decl` by grepping the source (the
    Registry.lean table names declarations, not modules)."""
    short = decl.rsplit(".", 1)[1]
    import subprocess
    r = subprocess.run(["grep", "-rl", "-E", rf"^(theorem|def) {short}\b", os.path.join(REG, "Problems")],
                       capture_output=True, text=True)
    files = [f for f in r.stdout.split() if f]
    if len(files) != 1:
        raise SystemExit(f"{decl}: expected one declaring file, found {files}")
    rel = os.path.relpath(files[0], REG)[:-5]
    return rel.replace(os.sep, ".")


def main() -> int:
    pin = yaml.safe_load(open(os.path.join(MILL, "PIN.yml")))
    os.makedirs(os.path.join(ROOT, "claims", "millennium"), exist_ok=True)
    results, ok = [], True
    for decl in pin["declarations"]:
        slug = decl.rsplit(".", 1)[1].replace("clay_prize_", "")
        module = module_of(decl)
        anchors = {k: (REG, v[0], v[1]) for k, v in (pin.get("anchors") or {}).items()}
        c = dict(id=f"M-{slug}", decl=decl, module=module, proj=REG, mutants=[],
                 checker_module=module, anchors=anchors)
        rec = C.evaluate(c, checker=CHECKER)
        got_lock = "lock" in rec
        ok &= got_lock
        results.append(rec)
        print(f"{rec['id']:28s} computed {rec['status']:11s} kind? custom {len(rec.get('custom_constants', []))}"
              f"  {'; '.join(rec['reasons'])[:120]}")
        claim = {"id": rec["id"], "registry": pin["source"], "pin": {k: pin[k] for k in ("rev", "lean", "mathlib", "physlib")},
                 "lean": f"{module}:{decl}", "lock": rec.get("lock"),
                 "custom_constants": rec.get("custom_constants", []),
                 "anchors": {k: v[2] for k, v in anchors.items() if k in rec.get("custom_constants", [])},
                 "hypotheses": rec.get("hypotheses", []), "grounded": rec.get("grounded"),
                 "closure": rec.get("closure", {}),
                 "status": rec["status"], "reasons": rec["reasons"], "evidence": rec["evidence"]}
        with open(os.path.join(ROOT, "claims", "millennium", f"{slug}.yml"), "w") as f:
            yaml.safe_dump(claim, f, sort_keys=False, allow_unicode=True)
    with open(os.path.join(MILL, "RESULTS.json"), "w") as f:
        json.dump({"pin": pin, "claims": results, "all_locked": ok}, f, indent=1)
    print("registry import:", "OK" if ok else "LOCK FAILURES", f"({len(results)} declarations)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
