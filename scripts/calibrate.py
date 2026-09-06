#!/usr/bin/env python3
"""calibrate.py [--no-ket]

Runs the calibration set (ARCHITECTURE.md section 7) against the calib/
project and COMPUTES a status for every control from the gate outputs. Writes
calib/RESULTS.json, one claims/<id>.yml per control, and stores every raw
gate output in the ket store (KET_HOME, default ~/code/handoffs/.ket) so the
record is by CID. Exit 0 iff every control reaches its required outcome.

Status rules (L2):
  axiom gate FAIL with sorryAx                 -> stated        (unproved)
  axiom gate FAIL with any other extra axiom   -> axiom-fail    (never a claim)
  lock unfolds to True                         -> stated: type is True
  custom constant without an admissible anchor -> stated: unanchored <c>
    (admissible = anchor_check.py shape OK, axiom gate clean, and every
     custom constant on the anchor's right-hand side anchored in turn)
  a required hypothesis mutant survives        -> stated: dead premise
  lean4checker rc != 0                         -> checker-fail
  negation proven (refuted_by)                 -> refuted
    (refuted_by is a nomination: refute_check.py must find the nominated
     declaration's type is ¬T with T's canonical form equal to the claim's,
     and its axiom set must be the triple; N8 covers the forgery)
  otherwise                                    -> proven
Drift (N5): a claim file whose recorded lock differs from the recomputed lock
fails the drift gate regardless of everything else.
"""
import json, os, subprocess, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIB = os.path.join(ROOT, "calib")
JIN = os.path.join(CALIB, "jin", "Lean")
CHECKER = os.path.join(CALIB, "lean4checker", ".lake", "build", "bin", "lean4checker")
SCRIPTS = os.path.join(ROOT, "scripts")
KET_HOME = os.environ.get("KET_HOME", os.path.expanduser("~/code/handoffs/.ket"))
USE_KET = "--no-ket" not in sys.argv

# anchors: custom constant -> (project, module, anchor decl). A row here is a
# NOMINATION only: anchor_check.py verifies the lemma has the shape
# `c x₁ … xₖ = rhs` / `↔ rhs` with distinct variable arguments, and the rhs's
# custom constants must themselves be anchored (N6, N7 cover the two forgeries).
ANCHORS = {
    "CrouzeixConjecture.SquareMatrix": (CALIB, "Quod.P1Anchors", "anchor_SquareMatrix"),
    "CrouzeixConjecture.EuclideanVector": (CALIB, "Quod.P1Anchors", "anchor_EuclideanVector"),
    "CrouzeixConjecture.polynomialEval": (CALIB, "Quod.P1Anchors", "anchor_polynomialEval"),
    "CrouzeixConjecture.numericalRange": (CALIB, "Quod.P1Anchors", "anchor_numericalRange"),
    "CrouzeixConjecture.maxPolynomialModulusOnNumericalRange":
        (CALIB, "Quod.P1Anchors", "anchor_maxPolynomialModulusOnNumericalRange"),
    "QuodP2.J": (CALIB, "Quod.P2", "QuodP2.anchor_J"),
}

CONTROLS = [
    dict(id="P1", polarity="positive", require="proven", proj=JIN, module="CrouzeixConjecture",
         decl="CrouzeixConjecture.crouzeixConjecture",
         statement="Crouzeix's conjecture for complex square matrices and polynomials, constant 2, induced Euclidean operator norm (jinshanmu/CrouzeixConjecture at f9d5c8d).",
         mutants=[dict(file="CrouzeixConjecture/FinalTheorems.lean", delete=" [Nonempty n]")],
         checker_module="CrouzeixConjecture.FinalTheorems"),
    dict(id="P2", polarity="positive", require="proven", proj=CALIB, module="Quod.P2",
         decl="QuodP2.sharp_two",
         statement="Sharpness of the constant 2 at the 2x2 nilpotent Jordan block with p = X: 2 * sup_{W(J)} |z| <= ||J||.",
         mutants=[], checker_module="Quod.P2"),
    dict(id="P3", polarity="positive", require="proven", proj=CALIB, module="Quod.P3",
         decl="QuodP3.infinitely_many_primes_again",
         statement="For every n there is a prime p >= n (restatement of Nat.exists_infinite_primes).",
         mutants=[], checker_module="Quod.P3", dedup_with="Nat.exists_infinite_primes"),
    dict(id="N1", polarity="negative", require="stated", proj=CALIB, module="Quod.Controls.N1",
         decl="navier_stokes",
         statement="The AIX template: a step hypothesis over a private predicate Tower.declInv, proved by induction.",
         mutants=[], checker_module="Quod.Controls.N1"),
    dict(id="N2", polarity="negative", require="stated", proj=CALIB, module="Quod.Controls.N2",
         decl="p_vs_np", statement="A named proposition whose definition is True.",
         mutants=[], checker_module="Quod.Controls.N2"),
    dict(id="N3", polarity="negative", require="axiom-fail", proj=CALIB, module="Quod.Controls.N3",
         decl="all_primes_small", statement="A theorem resting on an uninterpreted axiom `oracle`.",
         mutants=[], checker_module="Quod.Controls.N3"),
    dict(id="N4", polarity="negative", require="refuted", proj=CALIB, module="Quod.Controls.N4",
         decl="crouzeix_constant_one",
         statement="Crouzeix's inequality with constant 1 (false; refuted by P2's witness).",
         mutants=[], checker_module="Quod.Controls.N4",
         refuted_by=dict(module="Quod.P2", decl="QuodP2.N4_refuted")),
    dict(id="N6", polarity="negative", require="stated", proj=CALIB, module="Quod.Controls.N1",
         decl="navier_stokes",
         statement="N1 with a forged anchor row: Tower.declInv nominated to an unrelated rfl lemma (QuodP2.anchor_J).",
         mutants=[], checker_module="Quod.Controls.N1",
         anchors={"Tower.declInv": (CALIB, "Quod.P2", "QuodP2.anchor_J")}),
    dict(id="N7", polarity="negative", require="stated", proj=CALIB, module="Quod.Controls.N7",
         decl="navier_stokes_laundered",
         statement="N1 with an anchor of admissible shape whose right-hand side is another private constant (chain does not end in Mathlib).",
         mutants=[], checker_module="Quod.Controls.N7",
         anchors={"Tower7.declInv": (CALIB, "Quod.Controls.N7", "Tower7.anchor_declInv")}),
    dict(id="N8", polarity="negative", require="stated", proj=CALIB, module="Quod.Controls.N4",
         decl="crouzeix_constant_one",
         statement="N4 with a forged refutation row: an unrelated clean theorem (QuodP2.sharp_two) nominated as the negation.",
         mutants=[], checker_module="Quod.Controls.N4",
         refuted_by=dict(module="Quod.P2", decl="QuodP2.sharp_two")),
    dict(id="N5", polarity="negative", require="drift-fail", proj=JIN, module="CrouzeixConjecture",
         decl="CrouzeixConjecture.crouzeixConjecture",
         statement="P1's claim file with a stale recorded lock (the statement changed, the prose did not).",
         mutants=[], checker_module=None, stale_lock="0" * 64),
]


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def ket_put(text):
    if not USE_KET:
        return None
    r = subprocess.run(["ket", "put", "-"], input=text, capture_output=True, text=True,
                       env={**os.environ, "KET_HOME": KET_HOME})
    return r.stdout.strip() if r.returncode == 0 else None


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


def evaluate(c, checker=CHECKER):
    """Run every gate on one claim dict and return the record with its COMPUTED status.
    c: id, decl, module, proj, mutants, checker_module, optional anchors/refuted_by/
    dedup_with/stale_lock/polarity/require."""
    c = {"polarity": "claim", "require": None, "mutants": [], **c}
    rec = {"id": c["id"], "polarity": c["polarity"], "required": c["require"],
           "decl": c["decl"], "module": c["module"], "evidence": {}, "reasons": []}
    # L1 lock
    lk, raw = lock(c["proj"], c["module"], c["decl"])
    rec["evidence"]["lock_cid"] = ket_put(raw)
    if lk is None:
        rec["reasons"].append("lock failed"); status = "stated"
    else:
        rec["lock"] = lk["lock"]
        rec["custom_constants"] = [x["name"] for x in lk["custom_constants"]]
        status = None
        # L0 axiom gate
        arc, ax, raw = axioms(c["proj"], c["module"], c["decl"])
        rec["evidence"]["axioms_cid"] = ket_put(raw); rec["axioms"] = ax["axioms"]
        if not ax["ok"]:
            if ax["extra"] == ["sorryAx"]:
                status = "stated"; rec["reasons"].append("proof uses sorry")
            else:
                status = "axiom-fail"; rec["reasons"].append(f"extra axioms {ax['extra']}")
        # type is True
        if lk["reduces_to_True"]:
            status = status or "stated"; rec["reasons"].append("type unfolds to True")
        # anchors
        table = {**ANCHORS, **c.get("anchors", {})}
        unanchored = []
        for cc in rec["custom_constants"]:
            unanchored += anchored(cc, table, rec)
        if unanchored:
            status = status or "stated"; rec["reasons"].append(f"unanchored {unanchored}")
        # mutants
        for m in c["mutants"]:
            mrc, mout = run(["python3", f"{SCRIPTS}/hyp_mutant.py", c["proj"], m["file"],
                             "--delete", m["delete"]])
            rec["evidence"][f"mutant_{m['delete'].strip()}"] = ket_put(mout)
            rec.setdefault("mutants", []).append({"delete": m["delete"], "killed": mrc == 0})
            if mrc != 0:
                status = status or "stated"; rec["reasons"].append(f"dead premise {m['delete']!r}")
        # lean4checker
        if c.get("checker_module"):
            krc, kout = run(["lake", "env", checker, c["checker_module"]], cwd=c["proj"])
            rec["evidence"]["checker_cid"] = ket_put(kout); rec["checker_rc"] = krc
            if krc != 0:
                status = "checker-fail"; rec["reasons"].append("lean4checker failed")
        # refutation
        if c.get("refuted_by"):
            rb = c["refuted_by"]
            src, sout = run(["python3", f"{SCRIPTS}/refute_check.py", c["proj"], rb["module"],
                             rb["decl"], c["module"], c["decl"], "--json"])
            rec["evidence"]["refutation_shape_cid"] = ket_put(sout)
            rrc, rax, rraw = axioms(c["proj"], rb["module"], rb["decl"])
            rec["evidence"]["refutation_cid"] = ket_put(rraw)
            if src == 0 and rax["ok"]:
                status = "refuted"; rec["reasons"].append(f"negation proven: {rb['decl']}")
            else:
                why = "shape" if src != 0 else f"axioms {rax['extra']}"
                rec["reasons"].append(f"refutation {rb['decl']} rejected ({why})")
        # dedup
        if c.get("dedup_with"):
            lk2, _ = lock(c["proj"], c["module"], c["dedup_with"])
            rec["dedup"] = {"with": c["dedup_with"], "same_lock": bool(lk2 and lk2["lock"] == lk["lock"])}
            if not rec["dedup"]["same_lock"]:
                rec["reasons"].append("lock differs from the Mathlib declaration")
        # drift (N5): a recorded lock that no longer matches
        if c.get("stale_lock") is not None:
            rec["recorded_lock"] = c["stale_lock"]
            if c["stale_lock"] != lk["lock"]:
                status = "drift-fail"; rec["reasons"].append("recorded lock differs from recomputed lock")
        status = status or "proven"
    rec["status"] = status
    return rec


def main() -> int:
    results, all_ok = [], True
    os.makedirs(os.path.join(ROOT, "claims"), exist_ok=True)
    for c in CONTROLS:
        rec = evaluate(c)
        rec["ok"] = status == c["require"]
        all_ok &= rec["ok"]
        results.append(rec)
        print(f"{c['id']} {c['polarity']:8s} required {c['require']:11s} computed {status:11s} {'OK ' if rec['ok'] else 'MISS'}  {'; '.join(rec['reasons'])}")
        # claim file (status computed, never declared)
        claim = {"id": c["id"], "statement": c["statement"], "lean": f"{c['module']}:{c['decl']}",
                 "lock": rec.get("recorded_lock", rec.get("lock")), "custom_constants": rec.get("custom_constants", []),
                 "controls": [c["polarity"]], "status": status, "reasons": rec["reasons"],
                 "evidence": rec["evidence"]}
        with open(os.path.join(ROOT, "claims", f"{c['id'].lower()}.yml"), "w") as f:
            yaml.safe_dump(claim, f, sort_keys=False, allow_unicode=True)
    out = {"pins": {"crouzeix": {"lean": "v4.28.0", "mathlib": "8f9d9cff", "jin": "f9d5c8d"}},
           "controls": results, "pass": all_ok}
    with open(os.path.join(CALIB, "RESULTS.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("calibration:", "PASS" if all_ok else "FAIL",
          f"({sum(r['ok'] for r in results)}/{len(results)} controls at required outcome)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
