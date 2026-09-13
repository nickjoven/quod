#!/usr/bin/env python3
"""write_claims.py — assemble claims/openai-ns/*.yml and intake/openai-ns/RESULTS.json from the sealed evidence.

Computed status only (SEMANTICS.md lattice): a demonstrandum is `proven` iff the offered proof's lock
equals the demonstrandum's lock AND the axiom gate is clean AND the independent checker replay of the
whole non-Mathlib closure exited 0. Fidelity to the DeepMind statement is a DESCRIPTOR (registry_match
cannot be a lock relation across pins: decision 3). Prose states what was computed, nothing about the authors.
"""
import glob, hashlib, json, os, re, subprocess, sys, time
import yaml

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
E = os.path.join(HERE, "evidence")
pin = json.load(open(os.path.join(HERE, "PIN.json")))
cids = json.load(open(os.path.join(E, "CIDS.json")))


def jload(p):
    t = open(p).read(); return json.loads(t[t.index("{"):t.rindex("}") + 1])


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def ketput(p):
    r = subprocess.run(["ket", "put", p], capture_output=True, text=True)
    return r.stdout.strip().split()[-1] if r.returncode == 0 else None


checker_log = os.path.join(E, "checker.log")
ck = open(checker_log).read() if os.path.exists(checker_log) else ""
m = re.search(r"^checker exit (\d+) (\S+)", ck, re.M)
checker = {"ran": m is not None, "exit": int(m.group(1)) if m else None, "finished": m.group(2) if m else None,
           "modules": int(re.search(r"modules=(\d+)", ck).group(1)) if "modules=" in ck else None,
           "checker": "lean4checker master 91a7f0e8e9dffe927089f5a6edcfeeb8a0e07709 (toolchain v4.29.0-rc8) on lean-toolchain v4.34.0-rc2 with a one-line API patch (evidence/lean4checker-v4.34-patch.diff)",
           "checker_sha256": re.search(r"checker_sha256=([0-9a-f]+)", ck).group(1) if "checker_sha256=" in ck else None,
           "workers": 2, "log_cid": ketput(checker_log) if m else None, "log_sha256": sha(checker_log) if os.path.exists(checker_log) else None}
checker_ok = checker["ran"] and checker["exit"] == 0

ax = jload(os.path.join(E, "axioms-solution.json"))
axioms = {r["decl"]: r for r in ax["results"]}
fid = json.load(open(os.path.join(E, "fidelity.json")))
results = {}
os.makedirs(os.path.join(ROOT, "claims", "openai-ns"), exist_ok=True)
for key, name in (("R3", "navier_stokes_breakdown_R3"), ("periodic", "navier_stokes_breakdown_periodic")):
    full = f"NavierStokes.Comparator.{name}"
    lc, ls = jload(os.path.join(E, f"lock-challenge_{key}.json")), jload(os.path.join(E, f"lock-solution_{key}.json"))
    cl = jload(os.path.join(E, f"closure-challenge_{key}.json"))
    lock_eq = lc["lock"] == ls["lock"]
    axr = axioms[full]; ax_ok = axr["ok"]
    if lock_eq and ax_ok and checker_ok:
        verdict, status = "accepted", "proven"
    elif not lock_eq:
        verdict, status = "rejected: lock mismatch", "stated"
    elif not ax_ok:
        verdict, status = f"rejected: extra axioms {axr['extra']}", "stated"
    elif checker["ran"]:
        verdict, status = "rejected: lean4checker", "stated"
    else:
        verdict, status = "pending: lean4checker", "stated"
    frows = [r for r in fid["rows"] if r["decl"] == name or r["decl"].endswith(("Decay", "Decay.mk", "Rn", "Rn.mk")) if key == "R3"] if key == "R3" else \
            [r for r in fid["rows"] if r["decl"] == name or "Periodic" in r["decl"]]
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
        },
        "controls": [],
        "reasons": [x for x in [None if lock_eq else "lock mismatch", None if ax_ok else f"extra axioms {axr['extra']}",
                                None if checker_ok else ("lean4checker pending" if not checker["ran"] else f"lean4checker exit {checker['exit']}")] if x],
        "evidence": {
            "pin_cid": cids["PIN.json"]["cid"], "lock_cid": cids[f"evidence/lock-challenge_{key}.json"]["cid"],
            "offered_lock_cid": cids[f"evidence/lock-solution_{key}.json"]["cid"], "closure_cid": cids[f"evidence/closure-challenge_{key}.json"]["cid"],
            "axioms_cid": cids["evidence/axioms-solution.json"]["cid"], "fidelity_cid": cids["evidence/fidelity.json"]["cid"],
            "checker_cid": checker["log_cid"], "checker_patch_cid": cids["evidence/lean4checker-v4.34-patch.diff"]["cid"],
        },
    }
    with open(os.path.join(ROOT, "claims", "openai-ns", f"{claim['id'].lower()}.yml"), "w") as f:
        yaml.safe_dump(claim, f, sort_keys=False, allow_unicode=True)
    results[claim["id"]] = {"status": status, "proof_verdict": verdict, "lock": lc["lock"], "lock_equal": lock_eq, "axioms": axr["axioms"], "grounded": cl["grounded"],
                            "fidelity_equal": claim["descriptors"]["statement_fidelity"]["canonical_forms_equal_after_namespace_normalization"]}

scripts = {f: sha(os.path.join(ROOT, "scripts", f)) for f in sorted(os.listdir(os.path.join(ROOT, "scripts"))) if f.endswith((".py", ".lean", ".sh"))}
out = {"intake": "openai-ns", "pin": pin["expected"] | {"commit": pin["commit"], "repo": pin["repo"]}, "pin_verified": open(os.path.join(HERE, "PIN-verified.txt")).read().strip(),
       "build": {"wall": "12 min (04:25:19Z-04:37:37Z, 9,372 jobs incl. cached Mathlib)", "log_cid": cids["build.log"]["cid"]},
       "checker": checker, "results": results, "evidence_cids": cids,
       "runner": {"lock.py": scripts.get("lock.py"), "axiom_gate.py": scripts.get("axiom_gate.py"), "closure.py": scripts.get("closure.py"), "write_claims.py": sha(__file__)},
       "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
with open(os.path.join(HERE, "RESULTS.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(results, indent=1)); print("checker:", {k: checker[k] for k in ("ran", "exit", "modules")})
