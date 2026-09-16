#!/usr/bin/env python3
"""calibrate.py [--no-ket] [--only ID[,ID..]]

Runs the calibration set under SEMANTICS.md against the calib/ project and
COMPUTES, for every control, the status of its demonstrandum and the
verdict on what was offered against it. Writes calib/RESULTS.json, one
claims/<id>.yml per control, and stores every raw gate output in the ket
store (KET_HOME, default ~/code/handoffs/.ket). Exit 0 iff every control
reaches its required status AND its required descriptors.

Status of a demonstrandum D (never typed by hand):
  drift-fail   recorded lock differs from the recomputed lock
  refuted      a refutation discharges ¬D (shape gate + axiom triple + checker)
  proven       a proof discharges D (lock equal + axiom triple + checker)
  stated       otherwise (no proof, incomplete proof, or rejected proof)
  inconsistent both proven and refuted at one pin: halts the ledger

Verdict on an offered proof / refutation:
  accepted | incomplete: sorry | rejected: lock mismatch | rejected: shape
  | rejected: extra axioms [...] | rejected: lean4checker | rejected: no replay
(`accepted` always means the independent replay ran and passed; a claim with no
module to replay cannot be accepted, github #7.)

Descriptors (computed, never affect status): hypotheses, custom_constants,
grounded, anchored (per constant, with the gate's reason), reduces_to_True,
registry_match, dedup, mutants.
"""
import glob, hashlib, json, os, subprocess, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIB = os.path.join(ROOT, "calib")
JIN = os.path.join(CALIB, "jin", "Lean")
CHECKER = os.path.join(CALIB, "lean4checker", ".lake", "build", "bin", "lean4checker")
SCRIPTS = os.path.join(ROOT, "scripts")
KET_HOME = os.environ.get("KET_HOME", os.path.expanduser("~/code/handoffs/.ket"))
USE_KET = "--no-ket" not in sys.argv

# anchor NOMINATIONS: custom constant -> (project, module, anchor decl). Verified by
# anchor_check.py (shape) + axiom gate + recursion through the rhs (N6, N7).
ANCHORS = {
    "CrouzeixConjecture.SquareMatrix": (CALIB, "Quod.P1Anchors", "anchor_SquareMatrix"),
    "CrouzeixConjecture.EuclideanVector": (CALIB, "Quod.P1Anchors", "anchor_EuclideanVector"),
    "CrouzeixConjecture.polynomialEval": (CALIB, "Quod.P1Anchors", "anchor_polynomialEval"),
    "CrouzeixConjecture.numericalRange": (CALIB, "Quod.P1Anchors", "anchor_numericalRange"),
    "CrouzeixConjecture.maxPolynomialModulusOnNumericalRange":
        (CALIB, "Quod.P1Anchors", "anchor_maxPolynomialModulusOnNumericalRange"),
    "QuodP2.J": (CALIB, "Quod.P2", "QuodP2.anchor_J"),
}

# A control: a demonstrandum D (proj, module, decl), what is offered against it
# (default: D's own declaration as its proof), and the required outcome on
# status and descriptors. See SEMANTICS.md "Calibration under these semantics".
CONTROLS = [
    dict(id="P1", polarity="positive", proj=JIN, module="CrouzeixConjecture",
         decl="CrouzeixConjecture.crouzeixConjecture",
         gloss="Crouzeix's conjecture for complex square matrices and polynomials, constant 2, induced Euclidean operator norm (jinshanmu/CrouzeixConjecture at f9d5c8d).",
         mutants=[dict(file="CrouzeixConjecture/FinalTheorems.lean", delete=" [Nonempty n]")],
         checker_module="CrouzeixConjecture.FinalTheorems",
         require=dict(status="proven", grounded=True, anchored_all=True, hypotheses=[])),
    dict(id="P2", polarity="positive", proj=CALIB, module="Quod.P2", decl="QuodP2.sharp_two",
         gloss="Sharpness of the constant 2 at the 2x2 nilpotent Jordan block with p = X: 2 * sup_{W(J)} |z| <= ||J||.",
         checker_module="Quod.P2", require=dict(status="proven")),
    dict(id="P3", polarity="positive", proj=CALIB, module="Quod.P3",
         decl="QuodP3.infinitely_many_primes_again",
         gloss="For every n there is a prime p >= n (restatement of Nat.exists_infinite_primes).",
         checker_module="Quod.P3", dedup_with="Nat.exists_infinite_primes",
         require=dict(status="proven", dedup=True)),
    dict(id="N1", polarity="negative", proj=CALIB, module="Quod.Controls.N1", decl="navier_stokes",
         gloss="The induction-template control: a step hypothesis over a private predicate Tower.declInv, proved by induction. Proven as the implication it is; counts against nothing.",
         checker_module="Quod.Controls.N1",
         require=dict(status="proven", hypotheses=["step"], registry_match=None, anchored_all=False)),
    dict(id="N2", polarity="negative", proj=CALIB, module="Quod.Controls.N2", decl="p_vs_np",
         gloss="A named proposition whose definition is True. Proven, trivially, and the record says so.",
         checker_module="Quod.Controls.N2",
         require=dict(status="proven", reduces_to_True=True, registry_match=None)),
    dict(id="N3", polarity="negative", proj=CALIB, module="Quod.Controls.N3", decl="all_primes_small",
         gloss="A theorem resting on an uninterpreted axiom `oracle`.",
         checker_module="Quod.Controls.N3",
         require=dict(status="stated", proof_verdict="rejected: extra axioms")),
    dict(id="N4", polarity="negative", proj=CALIB, module="Quod.Controls.N4",
         decl="crouzeix_constant_one",
         gloss="Crouzeix's inequality with constant 1 (false; refuted by P2's witness).",
         checker_module="Quod.Controls.N4",
         refutation=dict(module="Quod.P2", decl="QuodP2.N4_refuted"),
         require=dict(status="refuted")),
    dict(id="N5", polarity="negative", proj=JIN, module="CrouzeixConjecture",
         decl="CrouzeixConjecture.crouzeixConjecture",
         gloss="P1's demonstrandum with a stale recorded lock (the statement changed, the record did not).",
         checker_module=None, stale_lock="0" * 64, require=dict(status="drift-fail")),
    dict(id="N6", polarity="negative", proj=CALIB, module="Quod.Controls.N1", decl="navier_stokes",
         gloss="N1 with a forged anchor row: Tower.declInv nominated to an unrelated rfl lemma (QuodP2.anchor_J).",
         checker_module="Quod.Controls.N1",
         anchors={"Tower.declInv": (CALIB, "Quod.P2", "QuodP2.anchor_J")},
         require=dict(status="proven", anchored_all=False, anchor_reason="ANCHOR-BAD")),
    dict(id="N7", polarity="negative", proj=CALIB, module="Quod.Controls.N7",
         decl="navier_stokes_laundered",
         gloss="N1 with an anchor of admissible shape whose right-hand side is another private constant (chain does not end in Mathlib).",
         checker_module="Quod.Controls.N7",
         anchors={"Tower7.declInv": (CALIB, "Quod.Controls.N7", "Tower7.anchor_declInv")},
         require=dict(status="proven", anchored_all=False, anchor_reason="via")),
    dict(id="N8", polarity="negative", proj=CALIB, module="Quod.Controls.N4",
         decl="crouzeix_constant_one",
         gloss="N4 with a forged refutation row: an unrelated clean theorem (QuodP2.sharp_two) nominated as the negation.",
         checker_module="Quod.Controls.N4",
         refutation=dict(module="Quod.P2", decl="QuodP2.sharp_two"),
         require=dict(status="stated", refutation_verdict="rejected: shape")),
    dict(id="N9", polarity="negative", proj=CALIB, module="Quod.P2",
         decl="QuodP2.sharp_two",
         gloss="A clean theorem offered as the proof of a different demonstrandum (P1's lock recorded as the target).",
         checker_module="Quod.P2",
         demonstrandum=dict(proj=JIN, module="CrouzeixConjecture", decl="CrouzeixConjecture.crouzeixConjecture"),
         require=dict(status="stated", proof_verdict="rejected: lock mismatch")),
]


PINS = {  # full 40-char commits; verified against the checkouts before they are recorded
    "lean": "v4.28.0",
    "mathlib": "8f9d9cff6bd728b17a24e163c9402775d9e6a365",
    "jin": "f9d5c8d39bece41ceedf6346ef50ad1fb393260e",
    "lean4checker": "66e11cea12f5ba215d76b15b7f8495141bf52c6c",
}
PIN_DIRS = {"mathlib": os.path.join(CALIB, ".lake", "packages", "mathlib"),
            "jin": os.path.join(CALIB, "jin"), "lean4checker": os.path.join(CALIB, "lean4checker")}


def verified_pins() -> dict:
    """The pin table, after checking every checkout's HEAD equals the recorded
    full commit. A mismatch is fatal: nothing downstream may run at a pin other
    than the one it records."""
    for k, d in PIN_DIRS.items():
        rc, out = run(["git", "-C", d, "rev-parse", "HEAD"])
        head = out.strip().splitlines()[-1] if out.strip() else ""
        if rc != 0 or head != PINS[k]:
            sys.exit(f"pin mismatch: {k} checkout at {d} is {head!r}, recorded {PINS[k]}")
    return dict(PINS)


def runner_shas():
    """sha256 of every gate script (Q-23): the run record names the exact
    runner that produced it, so a mid-run refactor is detectable after the fact."""
    return {os.path.basename(p): hashlib.sha256(open(p, "rb").read()).hexdigest()
            for p in sorted(glob.glob(os.path.join(SCRIPTS, "*.py")))}


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def ket_put(text):
    if not USE_KET:
        return None
    r = subprocess.run(["ket", "put", "-"], input=text, capture_output=True, text=True,
                       env={**os.environ, "KET_HOME": KET_HOME})
    if r.returncode != 0:
        # A ket failure must never masquerade as --no-ket (null CIDs): evidence
        # was promised, so its absence is a run failure, not a degradation.
        sys.exit(f"ket put failed (KET_HOME={KET_HOME}):\n{r.stderr.strip()}")
    return r.stdout.strip()


def lock(proj, module, decl):
    rc, out = run(["python3", f"{SCRIPTS}/lock.py", proj, module, decl, "--json"])
    if rc != 0:
        return None, out
    return json.loads(out[out.index("{"):]), out


def axioms(proj, module, decl):
    rc, out = run(["python3", f"{SCRIPTS}/axiom_gate.py", proj, module, decl, "--json"])
    try:
        js = json.loads(out[out.index("{"):out.rindex("}") + 1])
        res = js["results"][0]
    except Exception:
        res = {"ok": False, "extra": ["<lean error>"], "axioms": []}
    return rc, res, out


def anchor_shape(proj, module, anchor, const):
    rc, out = run(["python3", f"{SCRIPTS}/anchor_check.py", proj, module, anchor, const, "--json"])
    try:
        js = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except Exception:
        js = {"ok": False, "reason": "anchor_check failed to run", "rhs_custom": []}
    return js, out


def anchored(cc, table, rec, seen=()):
    """Reasons why `cc` is NOT anchored (empty list = anchored). Recurses through the
    anchor's right-hand side; a cycle counts as unanchored."""
    if cc in seen:
        return [f"{cc} (anchor cycle)"]
    a = table.get(cc)
    if a is None:
        return [cc]
    shape, raw = anchor_shape(*a, cc)
    rec["evidence"][f"anchor_shape_{cc}"] = ket_put(raw)
    if not shape["ok"]:
        return [f"{cc} ({shape['reason']})"]
    _, ax, raw2 = axioms(*a)
    rec["evidence"][f"anchor_axioms_{cc}"] = ket_put(raw2)
    if not ax["ok"]:
        return [f"{cc} (anchor axioms {ax['extra']})"]
    bad = []
    for d in shape["rhs_custom"]:
        bad += anchored(d["name"], table, rec, seen + (cc,))
    return [f"{cc} via {b}" for b in bad]


def registry_locks():
    """lock -> registry claim id, from claims/millennium/*.yml (empty before import)."""
    d = os.path.join(ROOT, "claims", "millennium")
    out = {}
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".yml"):
                y = yaml.safe_load(open(os.path.join(d, f)))
                if y.get("lock"):
                    out[y["lock"]] = y["id"]
    return out


REGISTRY_LOCKS = registry_locks()


def axiom_verdict(ax):
    if ax["ok"]:
        return "accepted"
    if ax["extra"] == ["sorryAx"]:
        return "incomplete: sorry"
    return f"rejected: extra axioms {ax['extra']}"


def replay_module(c, fallback):
    """The module lean4checker replays for an accepted verdict. An explicit
    checker_module wins. When the key is ABSENT the safe derivation is the
    module that declares the offered proof or refutation: the checker replays a
    whole module and the offered declaration lives in it. An explicit None
    means replay was switched off, and under SEMANTICS.md that is a rejection,
    never a pass (github #7: the old code skipped replay silently)."""
    if "checker_module" in c and c["checker_module"] is None:
        return None
    return c.get("checker_module") or fallback


def replay(c, rec, checker, module, verdict_key):
    """Independent replay is REQUIRED for an accepted verdict: no module, or a
    nonzero checker, rejects it. Records the module replayed, the checker's
    exit code and its output CID. Returns True iff the replay succeeded."""
    if module is None:
        rec[verdict_key] = "rejected: no replay"
        rec["checker_rc"] = None
        rec["reasons"].append("independent replay not configured; an accepted verdict requires lean4checker")
        return False
    krc, kout = run(["lake", "env", checker, module], cwd=c["proj"])
    rec["evidence"]["checker_cid"] = ket_put(kout); rec["checker_rc"] = krc; rec["checker_module"] = module
    if krc != 0:
        rec[verdict_key] = "rejected: lean4checker"
        return False
    return True


def evaluate(c, checker=CHECKER):
    """Compute the record for one control/claim under SEMANTICS.md.
    c: id, proj, module, decl (the offered declaration; also D unless `demonstrandum`
    names another), optional demonstrandum, refutation, anchors, stale_lock,
    dedup_with, mutants, checker_module, require."""
    c = {"polarity": "claim", "require": {}, "mutants": [], **c}
    D = c.get("demonstrandum") or dict(proj=c["proj"], module=c["module"], decl=c["decl"])
    rec = {"id": c["id"], "polarity": c["polarity"], "required": c["require"],
           "demonstrandum": f"{D['module']}:{D['decl']}", "offered": f"{c['module']}:{c['decl']}",
           "evidence": {}, "reasons": [], "proof_verdict": None, "refutation_verdict": None}
    # ---- demonstrandum lock and descriptors
    lkD, raw = lock(D["proj"], D["module"], D["decl"])
    rec["evidence"]["lock_cid"] = ket_put(raw)
    if lkD is None:
        rec["status"] = "lock-fail"; rec["reasons"].append("demonstrandum lock failed"); return rec
    rec["lock"] = lkD["lock"]
    rec["custom_constants"] = [x["name"] for x in lkD["custom_constants"]]
    rec["hypotheses"] = [{"name": h["name"], "type": h["type"]} for h in lkD.get("hypotheses", [])]
    rec["reduces_to_True"] = bool(lkD["reduces_to_True"])
    rec["registry_match"] = REGISTRY_LOCKS.get(lkD["lock"])
    if rec["reduces_to_True"]:
        rec["reasons"].append("type unfolds to True")
    if rec["custom_constants"]:
        grc, gout = run(["python3", f"{SCRIPTS}/closure.py", D["proj"], D["module"],
                         *rec["custom_constants"], "--json"])
        rec["evidence"]["closure_cid"] = ket_put(gout)
        try:
            reps = json.loads(gout[gout.index("["):gout.rindex("]") + 1])
            rec["grounded"] = all(r["grounded"] for r in reps)
            rec["closure"] = {r["root"]: {"custom": len(r["custom"]), "grounded": r["grounded"],
                                          "axioms": r["axioms"], "opaque": r["opaque"]} for r in reps}
        except Exception:
            rec["grounded"] = False; rec["reasons"].append("closure survey failed")
    else:
        rec["grounded"] = True
    table = {**ANCHORS, **c.get("anchors", {})}
    rec["anchored"] = {}
    for cc in rec["custom_constants"]:
        bad = anchored(cc, table, rec)
        rec["anchored"][cc] = "anchored" if not bad else "; ".join(bad)
    rec["anchored_all"] = all(v == "anchored" for v in rec["anchored"].values())
    if not rec["anchored_all"]:
        rec["reasons"].append("unanchored " + str([k for k, v in rec["anchored"].items() if v != "anchored"]))
    if c.get("dedup_with"):
        lk2, _ = lock(D["proj"], D["module"], c["dedup_with"])
        rec["dedup"] = bool(lk2 and lk2["lock"] == lkD["lock"])
        rec["reasons"].append(f"dedup with {c['dedup_with']}: {'same lock' if rec['dedup'] else 'different lock'}")
    # ---- drift
    if c.get("stale_lock") is not None:
        rec["recorded_lock"] = c["stale_lock"]
        if c["stale_lock"] != lkD["lock"]:
            rec["status"] = "drift-fail"; rec["reasons"].append("recorded lock differs from recomputed lock")
            return rec
    # ---- offered proof (default: D's own declaration)
    proof_ok = False
    if not c.get("refutation") or c.get("demonstrandum"):
        if c.get("demonstrandum"):
            lkP, rawP = lock(c["proj"], c["module"], c["decl"])
            rec["evidence"]["proof_lock_cid"] = ket_put(rawP)
            if lkP is None or lkP["lock"] != lkD["lock"]:
                rec["proof_verdict"] = "rejected: lock mismatch"
        if rec["proof_verdict"] is None:
            _, ax, raw = axioms(c["proj"], c["module"], c["decl"])
            rec["evidence"]["axioms_cid"] = ket_put(raw); rec["axioms"] = ax["axioms"]
            rec["proof_verdict"] = axiom_verdict(ax)
        # accepted by the axiom gate is not proven: the independent replay must also pass
        proof_ok = (rec["proof_verdict"] == "accepted"
                    and replay(c, rec, checker, replay_module(c, c["module"]), "proof_verdict"))
        for m in c["mutants"]:
            mrc, mout = run(["python3", f"{SCRIPTS}/hyp_mutant.py", c["proj"], m["file"],
                             "--delete", m["delete"]])
            rec["evidence"][f"mutant_{m['delete'].strip()}"] = ket_put(mout)
            rec.setdefault("mutants", []).append({"delete": m["delete"], "killed": mrc == 0})
            if mrc != 0:
                rec["reasons"].append(f"dead premise {m['delete']!r}")
    # ---- offered refutation
    ref_ok = False
    if c.get("refutation"):
        rb = c["refutation"]
        # the declaration D itself may carry a sorry body; record that verdict too
        _, axD, rawD = axioms(D["proj"], D["module"], D["decl"])
        rec["evidence"]["axioms_cid"] = ket_put(rawD); rec["axioms"] = axD["axioms"]
        rec["proof_verdict"] = axiom_verdict(axD)
        src, sout = run(["python3", f"{SCRIPTS}/refute_check.py", c["proj"], rb["module"],
                         rb["decl"], D["module"], D["decl"], "--json"])
        rec["evidence"]["refutation_shape_cid"] = ket_put(sout)
        if src != 0:
            rec["refutation_verdict"] = "rejected: shape"
        else:
            _, rax, rraw = axioms(c["proj"], rb["module"], rb["decl"])
            rec["evidence"]["refutation_cid"] = ket_put(rraw)
            rec["refutation_verdict"] = axiom_verdict(rax)
        ref_ok = (rec["refutation_verdict"] == "accepted"
                  and replay(c, rec, checker, replay_module(c, rb["module"]), "refutation_verdict"))
        rec["refutation"] = f"{rb['module']}:{rb['decl']}"
    # ---- status
    if proof_ok and ref_ok:
        rec["status"] = "inconsistent"
    elif ref_ok:
        rec["status"] = "refuted"
    elif proof_ok:
        rec["status"] = "proven"
    else:
        rec["status"] = "stated"
    return rec


def meets(rec, req):
    """Which required keys the record fails (empty = OK)."""
    misses = []
    for k, want in req.items():
        if k == "hypotheses":
            got = [h["name"] for h in rec.get("hypotheses", [])]
        elif k in ("proof_verdict", "refutation_verdict"):
            got = rec.get(k) or ""
            if want not in got:
                misses.append(f"{k}={got!r}")
            continue
        elif k == "anchor_reason":
            got = " ".join(rec.get("anchored", {}).values())
            if want not in got:
                misses.append(f"{k}={got!r}")
            continue
        else:
            got = rec.get(k)
        if got != want:
            misses.append(f"{k}={got!r} (want {want!r})")
    return misses


def main() -> int:
    # Preflight (environment error, not a verdict): a missing Lean toolchain
    # must abort before any status is computed or any claim file is touched.
    # Without this, every control degrades to lock-fail and overwrites the
    # recorded claims — observed live on 2026-09-06 when ~/.elan/bin was off
    # PATH outside bootstrap.sh's own shell.
    import shutil
    for tool in ("lake", "lean"):
        if shutil.which(tool) is None:
            elan_bin = os.path.expanduser("~/.elan/bin")
            hint = f' (try: export PATH="{elan_bin}:$PATH")' if os.path.isdir(elan_bin) else ""
            sys.exit(f"environment error: {tool!r} not on PATH{hint}; refusing to compute statuses")
    only = None
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only = set(sys.argv[i + 1].split(","))
    controls = [c for c in CONTROLS if only is None or c["id"] in only]
    results, all_ok = [], True
    os.makedirs(os.path.join(ROOT, "claims"), exist_ok=True)
    for c in controls:
        rec = evaluate(c)
        misses = meets(rec, c["require"])
        rec["ok"] = not misses
        all_ok &= rec["ok"]
        results.append(rec)
        verd = []
        if rec.get("proof_verdict"): verd.append(f"proof {rec['proof_verdict']}")
        if rec.get("refutation_verdict"): verd.append(f"refutation {rec['refutation_verdict']}")
        print(f"{c['id']} {c['polarity']:8s} required {c['require'].get('status','?'):10s} computed {rec['status']:10s} "
              f"{'OK ' if rec['ok'] else 'MISS ' + '; '.join(misses)}  {'; '.join(verd + rec['reasons'])}")
        claim = {"id": c["id"], "gloss": c["gloss"], "demonstrandum": rec["demonstrandum"],
                 "lock": rec.get("recorded_lock", rec.get("lock")),
                 "offered": rec["offered"], "proof_verdict": rec.get("proof_verdict"),
                 "refutation": rec.get("refutation"), "refutation_verdict": rec.get("refutation_verdict"),
                 "status": rec["status"],
                 "descriptors": {k: rec.get(k) for k in ("hypotheses", "custom_constants", "grounded",
                                                          "anchored", "reduces_to_True", "registry_match",
                                                          "dedup", "mutants") if k in rec},
                 "controls": [c["polarity"]], "reasons": rec["reasons"], "evidence": rec["evidence"]}
        with open(os.path.join(ROOT, "claims", f"{c['id'].lower()}.yml"), "w") as f:
            yaml.safe_dump(claim, f, sort_keys=False, allow_unicode=True)
    if only is None:
        out = {"semantics": "SEMANTICS.md", "pins": {"crouzeix": verified_pins()},
               "runner": runner_shas(), "controls": results, "pass": all_ok}
        with open(os.path.join(CALIB, "RESULTS.json"), "w") as f:
            json.dump(out, f, indent=1)
    print("calibration:", "PASS" if all_ok else "FAIL",
          f"({sum(r['ok'] for r in results)}/{len(results)} controls at required outcome)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
