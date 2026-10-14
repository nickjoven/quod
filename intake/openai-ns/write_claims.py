#!/usr/bin/env python3
"""write_claims.py — assemble claims and RESULTS.json for the openai-ns intake from sealed evidence.

    write_claims.py                      # legacy: evidence/ -> RESULTS.json + claims/openai-ns/ (the historical paths)
    write_claims.py --evidence DIR --out-results FILE --out-claims DIR [--closure-modules FILE] [--checker-modules FILE]

Computed status only (SEMANTICS.md lattice): a demonstrandum is `proven` iff the offered proof's lock
equals the demonstrandum's lock AND the axiom gate is clean AND the independent checker replay exited 0
AND, when the closure is known, the replay covered every module of the proof's non-standard import closure.
No checker log → `pending: lean4checker`, status `stated`: the absence of the replay is never acceptance
(github #7; this intake's writer never had the generic calibrate.py path, and tests/test_reproduce_ns.py
pins that). Fidelity to the DeepMind statement is a DESCRIPTOR (registry_match cannot be a lock relation
across pins: decision 3). Prose states what was computed, nothing about the authors.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))

HIST_CHECKER_DESC = ("lean4checker master 91a7f0e8e9dffe927089f5a6edcfeeb8a0e07709 (toolchain v4.29.0-rc8) on lean-toolchain "
                     "v4.34.0-rc2 with a one-line API patch (evidence/lean4checker-v4.34-patch.diff)")


def jload(p):
    t = open(p).read(); return json.loads(t[t.index("{"):t.rindex("}") + 1])


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def b3(p):
    import blake3  # type: ignore
    return blake3.blake3(open(p, "rb").read()).hexdigest()


def ketput(p):
    """Store in ket and return the CID; the CID is BLAKE3 of the bytes, so it must equal b3(p)."""
    r = subprocess.run(["ket", "put", p], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ket put {p} failed:\n{r.stderr.strip()}")
    cid = r.stdout.strip().split()[-1]
    if cid != b3(p):
        sys.exit(f"ket returned {cid} but blake3 of {p} is {b3(p)}")
    return cid


def read_modules(path):
    return [l for l in open(path).read().split() if l] if path and os.path.exists(path) else None


def checker_record(E, checker_desc, workers, closure_modules=None, checker_modules=None, ket=False):
    """What the independent replay established, from its log and the module lists alone."""
    log = os.path.join(E, "checker.log")
    ck = open(log).read() if os.path.exists(log) else ""
    m = re.search(r"^checker exit (\d+) (\S+)", ck, re.M)
    rec = {"ran": m is not None, "exit": int(m.group(1)) if m else None, "finished": m.group(2) if m else None,
           "modules": int(re.search(r"modules=(\d+)", ck).group(1)) if "modules=" in ck else None,
           "checker": checker_desc,
           "checker_sha256": re.search(r"checker_sha256=([0-9a-f]+)", ck).group(1) if "checker_sha256=" in ck else None,
           "workers": workers,
           "log_cid": (ketput(log) if ket else b3(log)) if m else None,
           "log_sha256": sha(log) if os.path.exists(log) else None}
    if closure_modules is not None:
        replayed = set(checker_modules or [])
        missing = sorted(set(closure_modules) - replayed)
        rec["closure_modules"] = len(closure_modules)
        rec["covers_closure"] = not missing and rec["modules"] == len(closure_modules)
        rec["closure_modules_not_replayed"] = missing[:20]
    else:
        rec["closure_modules"] = None; rec["covers_closure"] = None
    rec["ok"] = bool(rec["ran"] and rec["exit"] == 0 and rec["covers_closure"] is not False)
    return rec


def write(evidence, pin, cids, out_results, out_claims, closure_modules=None, checker_modules=None, build_info=None,
          checker_desc=HIST_CHECKER_DESC, workers=2, toolchain_checker=None, run_id=None, ket=False):
    """Write RESULTS.json and the two claim files from the evidence directory. Returns {"results":…, "checker":…}.

    cids maps evidence-relative paths ("lock-challenge_R3.json", "PIN.json", …) to {"cid", "sha256"}; the
    legacy index uses "evidence/…" keys and both spellings are accepted.
    """
    E = evidence

    def cid(rel):
        for k in (rel, f"evidence/{rel}", rel.removeprefix("evidence/")):
            if k in cids: return cids[k]["cid"]
        raise KeyError(f"no CID recorded for {rel}")

    checker = checker_record(E, checker_desc, workers, read_modules(closure_modules), read_modules(checker_modules), ket=ket)
    checker_ok = checker["ok"]
    # Q-32: when the run compared what the statement's names MEAN on both sides, equality is required
    defs_path = os.path.join(E, "definitions.json")
    defs = json.load(open(defs_path)) if os.path.exists(defs_path) else None
    ax = jload(os.path.join(E, "axioms-solution.json"))
    axioms = {r["decl"]: r for r in ax["results"]}
    fid = json.load(open(os.path.join(E, "fidelity.json")))
    results = {}
    os.makedirs(out_claims, exist_ok=True)
    for key, name in (("R3", "navier_stokes_breakdown_R3"), ("periodic", "navier_stokes_breakdown_periodic")):
        full = f"NavierStokes.Comparator.{name}"
        lc, ls = jload(os.path.join(E, f"lock-challenge_{key}.json")), jload(os.path.join(E, f"lock-solution_{key}.json"))
        cl = jload(os.path.join(E, f"closure-challenge_{key}.json"))
        lock_eq = lc["lock"] == ls["lock"]
        d = (defs or {}).get("per_demonstrandum", {}).get(key) if defs else None
        defs_eq = None if d is None else bool(d.get("equal"))
        axr = axioms[full]; ax_ok = axr["ok"]
        if lock_eq and defs_eq is not False and ax_ok and checker_ok:
            verdict, status = "accepted", "proven"
        elif not lock_eq:
            verdict, status = "rejected: lock mismatch", "stated"
        elif defs_eq is False:
            verdict, status = "rejected: definitions differ", "stated"
        elif not ax_ok:
            verdict, status = f"rejected: extra axioms {axr['extra']}", "stated"
        elif checker["ran"] and checker["exit"] == 0 and checker["covers_closure"] is False:
            verdict, status = "rejected: replay did not cover the closure", "stated"
        elif checker["ran"]:
            verdict, status = "rejected: lean4checker", "stated"
        else:
            verdict, status = "pending: lean4checker", "stated"
        frows = ([r for r in fid["rows"] if r["decl"] == name or r["decl"].endswith(("Decay", "Decay.mk", "Rn", "Rn.mk"))] if key == "R3"
                 else [r for r in fid["rows"] if r["decl"] == name or "Periodic" in r["decl"]])
        claim = {
            "id": f"OPENAI-NS-{key.upper()}",
            "gloss": f"Clay alternative {'C' if key == 'R3' else 'D'} as stated in OpenAI's challenge file at commit {pin['commit'][:12]}: "
                     f"the demonstrandum is `{full}` in module ComparatorChallenges.NavierStokes (a `sorry` placeholder); "
                     f"the offered proof is the same-named theorem in module NavierStokes.ComparatorSolution. Computed at the claim's own pin "
                     f"({pin['expected']['lean_toolchain']}, mathlib {pin['expected']['mathlib'][:12]}). Nothing here is a statement about the authors.",
            "demonstrandum": f"ComparatorChallenges.NavierStokes:{full}",
            "lock": lc["lock"],
            "offered": f"NavierStokes.ComparatorSolution:{full}",
            "offered_lock": ls["lock"],
            "proof_verdict": verdict,
            "refutation": None, "refutation_verdict": None,
            "status": status,
            "descriptors": {
                "hypotheses": [{"name": h["name"], "type": h["type"]} for h in lc.get("hypotheses", [])],
                "custom_constants": [c["name"] for c in lc.get("custom_constants", [])],
                "grounded": cl["grounded"], "closure_custom": [c["name"] for c in cl["custom"]], "closure_axioms": cl["axioms"], "closure_opaque": cl["opaque"],
                "reduces_to_True": lc.get("reduces_to_True"),
                "registry_match": None,
                "statement_fidelity": {
                    "upstream": "google-deepmind/formal-conjectures FormalConjectures/Millenium/NavierStokes.lean @ 8bf45ed7 (the commit OpenAI's file cites; blob 6fd45b55...), ported into this pin with import/attribute/notation/namespace changes only (evidence/port-diff.txt)",
                    "canonical_forms_equal_after_namespace_normalization": all(r.get("namespace_normalized_equal") for r in frows),
                    "compared": [r["decl"] for r in frows],
                    "note": "a descriptor, never a status: the upstream file lives at a different pin (v4.33.1), so this is a same-pin port, not a cross-pin lock",
                },
                "checker_closure_modules": checker["modules"],
                "checker_covers_closure": checker["covers_closure"],
                "definitions_identical": defs_eq,
                "definitions_note": ("not checked: the historical run compared locks only (Q-32)" if defs_eq is None else
                                     f"{d.get('constants')} non-standard constants reachable from the statement carry the same canonical "
                                     f"type and value in the challenge module and in the solution's definitions module (evidence/definitions.json)"
                                     if defs_eq else f"differ: {d.get('differ')}; only in challenge: {d.get('only_challenge')}; only in solution: {d.get('only_solution')}"),
            },
            "controls": [],
            "reasons": [x for x in [None if lock_eq else "lock mismatch", None if defs_eq is not False else "definitions differ",
                                    None if ax_ok else f"extra axioms {axr['extra']}",
                                    None if checker_ok else ("lean4checker pending" if not checker["ran"]
                                                             else f"lean4checker exit {checker['exit']}" if checker["exit"] != 0
                                                             else "replay did not cover the closure")] if x],
            "evidence": {
                "pin_cid": cids["PIN.json"]["cid"] if "PIN.json" in cids else None,
                "lock_cid": cid(f"lock-challenge_{key}.json"),
                "offered_lock_cid": cid(f"lock-solution_{key}.json"), "closure_cid": cid(f"closure-challenge_{key}.json"),
                "axioms_cid": cid("axioms-solution.json"), "fidelity_cid": cid("fidelity.json"),
                "checker_cid": checker["log_cid"],
                "checker_patch_cid": cid("lean4checker-v4.34-patch.diff") if any(k.endswith("lean4checker-v4.34-patch.diff") for k in cids)
                                     else cid("lean4checker-applied.diff"),
                "definitions_cid": cid("definitions.json") if defs is not None else None,
            },
        }
        if toolchain_checker and toolchain_checker.get("available"):
            claim["descriptors"]["toolchain_leanchecker"] = {"exit": toolchain_checker.get("exit"), "modules": toolchain_checker.get("modules"),
                                                             "chunks": toolchain_checker.get("chunks"), "failed_chunks": toolchain_checker.get("failed_chunks"),
                                                             "note": toolchain_checker.get("caveat")}
        if run_id:
            claim["run_id"] = run_id
        with open(os.path.join(out_claims, f"{claim['id'].lower()}.yml"), "w") as f:
            yaml.safe_dump(claim, f, sort_keys=False, allow_unicode=True)
        results[claim["id"]] = {"status": status, "proof_verdict": verdict, "lock": lc["lock"], "lock_equal": lock_eq, "axioms": axr["axioms"],
                                "grounded": cl["grounded"], "definitions_identical": defs_eq,
                                "fidelity_equal": claim["descriptors"]["statement_fidelity"]["canonical_forms_equal_after_namespace_normalization"]}

    scripts = {f: sha(os.path.join(ROOT, "scripts", f)) for f in sorted(os.listdir(os.path.join(ROOT, "scripts"))) if f.endswith((".py", ".lean", ".sh"))}
    pin_verified = os.path.join(HERE, "PIN-verified.txt")
    out = {"intake": "openai-ns", "run_id": run_id, "pin": pin["expected"] | {"commit": pin["commit"], "repo": pin["repo"]},
           "pin_verified": (open(pin_verified).read().strip() if run_id is None and os.path.exists(pin_verified) else "see evidence/pin-check.json"),
           "build": build_info or {"wall": "12 min (04:25:19Z-04:37:37Z, 9,372 jobs incl. cached Mathlib)",
                                   "log_cid": cids.get("build.log", {}).get("cid")},
           "checker": checker, "toolchain_checker": toolchain_checker, "results": results, "evidence_cids": cids,
           "runner": {"lock.py": scripts.get("lock.py"), "axiom_gate.py": scripts.get("axiom_gate.py"), "closure.py": scripts.get("closure.py"),
                      "write_claims.py": sha(__file__), "reproduce.py": sha(os.path.join(HERE, "reproduce.py")) if os.path.exists(os.path.join(HERE, "reproduce.py")) else None},
           "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    with open(out_results, "w") as f:
        json.dump(out, f, indent=1)
    return {"results": results, "checker": checker}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    ap.add_argument("--out-results", default=os.path.join(HERE, "RESULTS.json"))
    ap.add_argument("--out-claims", default=os.path.join(ROOT, "claims", "openai-ns"))
    ap.add_argument("--closure-modules"); ap.add_argument("--checker-modules")
    ap.add_argument("--cids", help="CID index (default: <evidence>/CIDS.json)")
    ap.add_argument("--run-id")
    ap.add_argument("--ket", action="store_true", help="store the checker log in ket (CID is blake3 either way)")
    a = ap.parse_args()
    pin = json.load(open(os.path.join(HERE, "PIN.json")))
    cids = json.load(open(a.cids or os.path.join(a.evidence, "CIDS.json")))
    out = write(a.evidence, pin, cids, a.out_results, a.out_claims, a.closure_modules, a.checker_modules, run_id=a.run_id, ket=a.ket)
    print(json.dumps(out["results"], indent=1)); print("checker:", {k: out["checker"][k] for k in ("ran", "exit", "modules", "covers_closure")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
