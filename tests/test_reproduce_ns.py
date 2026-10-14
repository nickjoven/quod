"""github #8 (deliverable 2/3): the fresh-checkout runner's decisions, with no Lean.

Pure functions of intake/openai-ns/reproduce.py are exercised on the tracked
historical evidence, and write_claims.write() on a copy of that evidence with
one thing changed at a time: the historical records must reproduce their own
statuses, and every removed or broken input must turn `proven` into a recorded
rejection or a pending verdict, never silent acceptance (github #7 for this
intake's own claim writer).
"""
import importlib.util
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTAKE = os.path.join(ROOT, "intake", "openai-ns")
E = os.path.join(INTAKE, "evidence")


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(INTAKE, f"{name}.py"))
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


R = load("reproduce")
W = load("write_claims")
PIN = json.load(open(os.path.join(INTAKE, "PIN.json")))


def jload(p):
    t = open(p).read(); return json.loads(t[t.index("{"):t.rindex("}") + 1])


# ----------------------------------------------------------------------------- pin check

def good_inputs():
    manifest = {"packages": [{"name": "mathlib", "rev": PIN["expected"]["mathlib"]},
                             {"name": "Comparator", "rev": PIN["expected"]["comparator"]},
                             {"name": "lean4export", "rev": PIN["expected"]["lean4export"] + "d75f00"}]}
    files = {k: {"path": PIN["expected"][k]["path"], "got": {}, "mismatch": [], "ok": True} for k in ("statement_file", "challenge_spec")}
    return PIN["commit"], PIN["expected"]["lean_toolchain"], manifest, files


def test_pin_check_accepts_the_recorded_pin():
    rep = R.check_pin(*good_inputs())
    assert rep["ok"] and rep["failures"] == []


@pytest.mark.parametrize("field", ["commit", "toolchain", "mathlib", "comparator", "statement_file"])
def test_pin_check_refuses_every_drift(field):
    head, tc, manifest, files = good_inputs()
    if field == "commit": head = "0" * 40
    if field == "toolchain": tc = "leanprover/lean4:v4.34.1"
    if field == "mathlib": manifest["packages"][0]["rev"] = "deadbeef" * 5
    if field == "comparator": manifest["packages"][1]["rev"] = ""
    if field == "statement_file": files["statement_file"] = {"path": "x", "got": {}, "mismatch": ["sha256"], "ok": False}
    rep = R.check_pin(head, tc, manifest, files)
    assert not rep["ok"] and rep["failures"]


def test_check_file_hashes_the_tracked_statement_copy(tmp_path):
    # the tracked upstream copy is a real file with known identities: a changed byte must be caught
    p = tmp_path / "f.lean"; p.write_bytes(b"theorem t : True := trivial\n")
    rec = R.check_file(str(p), {"bytes": 28})
    assert rec["ok"] and rec["got"]["git_blob"] and len(rec["got"]["blake3"]) == 64
    bad = R.check_file(str(p), {"bytes": 28, "sha256": "0" * 64})
    assert not bad["ok"] and bad["mismatch"] == ["sha256"]


# ----------------------------------------------------------------------------- closure modules

def test_nonstd_modules_drops_the_pinned_libraries_and_keeps_the_proof():
    names = ["Init.Prelude", "Lean.Meta", "Mathlib.Topology.Basic", "Batteries.Data.List", "Aesop", "Qq.Macro",
             "NavierStokes.ComparatorSolution", "ComparatorChallenges.NavierStokes", "Comparator.Nanoda", "Leanish.NotStd"]
    out = R.nonstd_modules(names)
    assert out == ["Comparator.Nanoda", "ComparatorChallenges.NavierStokes", "Leanish.NotStd", "NavierStokes.ComparatorSolution"]


def test_historical_checker_list_is_exactly_the_nonstd_closure_shape():
    mods = open(os.path.join(E, "checker-modules.txt")).read().split()
    assert len(mods) == 610 and R.nonstd_modules(mods) == sorted(mods)
    assert "ComparatorChallenges.NavierStokes" in mods and "NavierStokes.ComparatorSolution" in mods


# ----------------------------------------------------------------------------- fidelity

def historical_locks():
    locks = {"upstream": {}, "adapted": {}}
    for side in locks:
        for d in R.FIDELITY_DECLS:
            locks[side][d] = jload(os.path.join(E, "fidelity", f"{side}--{d}.json"))
    return locks


def test_fidelity_rows_reproduce_the_tracked_table():
    want = json.load(open(os.path.join(E, "fidelity.json")))["rows"]
    got = R.fidelity_rows(historical_locks())
    assert [{k: r[k] for k in ("decl", "raw_equal", "namespace_normalized_equal", "lock_upstream", "lock_adapted")} for r in got] == want
    assert all(r["namespace_normalized_equal"] for r in got) and not all(r["raw_equal"] for r in got)


def test_fidelity_rows_detect_a_changed_statement():
    locks = historical_locks()
    locks["adapted"]["navier_stokes_breakdown_R3"]["canonical_type"] += " (changed)"
    rows = {r["decl"]: r for r in R.fidelity_rows(locks)}
    assert rows["navier_stokes_breakdown_R3"]["namespace_normalized_equal"] is False
    assert rows["navier_stokes_breakdown_periodic"]["namespace_normalized_equal"] is True


def test_fidelity_rows_mark_a_missing_lock():
    locks = historical_locks(); del locks["upstream"]["ForceConditionDecay"]
    rows = {r["decl"]: r for r in R.fidelity_rows(locks)}
    assert rows["ForceConditionDecay"]["namespace_normalized_equal"] is None and rows["ForceConditionDecay"]["missing"]


# ----------------------------------------------------------------------------- checker log

def test_parse_checker_log():
    p = R.parse_checker_log("start 2026 modules=610 checker_sha256=" + "ab" * 32 + "\nFound 610 modules to check\nchecker exit 0 2026-09-13T06:26:09Z\n")
    assert p == {"ran": True, "exit": 0, "finished": "2026-09-13T06:26:09Z", "modules": 610, "checker_sha256": "ab" * 32}
    assert R.parse_checker_log("start modules=3\n")["ran"] is False


# ----------------------------------------------------------------------------- write_claims on a copy of the evidence

@pytest.fixture
def evidence(tmp_path):
    """A copy of the historical evidence plus module lists; returns (dir, cids, write)."""
    d = tmp_path / "evidence"; shutil.copytree(E, d)
    (d / "closure-modules.txt").write_text(open(os.path.join(E, "checker-modules.txt")).read())
    cids = json.load(open(os.path.join(E, "CIDS.json")))

    def write(**kw):
        out = W.write(str(d), PIN, cids, str(tmp_path / "RESULTS.json"), str(tmp_path / "claims"),
                      closure_modules=str(d / "closure-modules.txt"), checker_modules=str(d / "checker-modules.txt"), **kw)
        return out, json.load(open(tmp_path / "RESULTS.json"))
    return d, cids, write


def test_historical_evidence_reproduces_its_statuses(evidence):
    d, cids, write = evidence
    out, res = write()
    hist = json.load(open(os.path.join(INTAKE, "RESULTS.json")))["results"]
    assert {k: v["status"] for k, v in out["results"].items()} == {k: v["status"] for k, v in hist.items()}
    assert {k: v["lock"] for k, v in out["results"].items()} == {k: v["lock"] for k, v in hist.items()}
    assert out["checker"]["covers_closure"] is True and out["checker"]["ok"]
    assert res["checker"]["log_cid"] == json.load(open(os.path.join(INTAKE, "RESULTS.json")))["checker"]["log_cid"]


def test_missing_checker_log_is_pending_never_proven(evidence):
    d, cids, write = evidence
    os.unlink(d / "checker.log")
    out, _ = write()
    assert all(v["status"] == "stated" and v["proof_verdict"] == "pending: lean4checker" for v in out["results"].values())
    assert out["checker"]["ran"] is False and out["checker"]["log_cid"] is None


def test_failed_checker_is_rejected(evidence):
    d, cids, write = evidence
    (d / "checker.log").write_text((d / "checker.log").read_text().replace("checker exit 0", "checker exit 1"))
    out, _ = write()
    assert all(v["proof_verdict"] == "rejected: lean4checker" for v in out["results"].values())


def test_replay_that_misses_a_closure_module_is_rejected(evidence):
    d, cids, write = evidence
    mods = (d / "checker-modules.txt").read_text().split()
    (d / "checker-modules.txt").write_text("\n".join(m for m in mods if m != "NavierStokes.ComparatorTheorem") + "\n")
    out, _ = write()
    assert out["checker"]["covers_closure"] is False
    assert out["checker"]["closure_modules_not_replayed"] == ["NavierStokes.ComparatorTheorem"]
    assert all(v["proof_verdict"] == "rejected: replay did not cover the closure" for v in out["results"].values())


def test_lock_mismatch_is_rejected(evidence):
    d, cids, write = evidence
    p = d / "lock-solution_R3.json"; j = jload(str(p)); j["lock"] = "f" * 64; p.write_text(json.dumps(j))
    out, _ = write()
    assert out["results"]["OPENAI-NS-R3"]["proof_verdict"] == "rejected: lock mismatch"
    assert out["results"]["OPENAI-NS-PERIODIC"]["proof_verdict"] == "accepted"


def test_extra_axiom_is_rejected(evidence):
    d, cids, write = evidence
    p = d / "axioms-solution.json"; j = jload(str(p))
    j["results"][1].update({"ok": False, "extra": ["sorryAx"], "axioms": j["results"][1]["axioms"] + ["sorryAx"]})
    p.write_text(json.dumps(j))
    out, _ = write()
    assert out["results"]["OPENAI-NS-PERIODIC"]["proof_verdict"] == "rejected: extra axioms ['sorryAx']"
    assert out["results"]["OPENAI-NS-R3"]["proof_verdict"] == "accepted"


def test_unknown_closure_does_not_pretend_coverage(evidence):
    d, cids, write = evidence
    out = W.write(str(d), PIN, cids, str(d.parent / "R2.json"), str(d.parent / "c2"))
    assert out["checker"]["covers_closure"] is None and out["checker"]["ok"]


# ----------------------------------------------------------------------------- Q-32: definitions behind the names

def defs_record(equal=True, differ=()):
    one = {"demonstrandum": "x", "equal": equal, "differ": list(differ), "only_challenge": [], "only_solution": [],
           "digest_challenge": "a" * 64, "digest_solution": ("a" if equal else "b") * 64, "constants": 12,
           "modules_challenge": ["ComparatorChallenges.NavierStokes"], "modules_solution": ["NavierStokes.ComparatorDefinitions"], "missing": []}
    return {"method": "test", "all_equal": equal, "per_demonstrandum": {"R3": one, "periodic": dict(one)}}


def test_definitions_equal_is_recorded_and_accepted(evidence):
    d, cids, write = evidence
    json.dump(defs_record(True), open(d / "definitions.json", "w"))
    cids = dict(cids); cids["evidence/definitions.json"] = {"cid": "c" * 64, "sha256": "d" * 64}
    out = W.write(str(d), PIN, cids, str(d.parent / "R3.json"), str(d.parent / "c3"),
                  closure_modules=str(d / "closure-modules.txt"), checker_modules=str(d / "checker-modules.txt"))
    assert all(v["status"] == "proven" and v["definitions_identical"] is True for v in out["results"].values())


def test_definitions_differ_is_rejected_even_with_equal_locks(evidence):
    d, cids, write = evidence
    json.dump(defs_record(False, ["NavierStokes.Comparator.divergence"]), open(d / "definitions.json", "w"))
    cids = dict(cids); cids["evidence/definitions.json"] = {"cid": "c" * 64, "sha256": "d" * 64}
    out = W.write(str(d), PIN, cids, str(d.parent / "R4.json"), str(d.parent / "c4"),
                  closure_modules=str(d / "closure-modules.txt"), checker_modules=str(d / "checker-modules.txt"))
    assert all(v["status"] == "stated" and v["proof_verdict"] == "rejected: definitions differ" for v in out["results"].values())


def test_historical_evidence_has_no_definitions_record(evidence):
    d, cids, write = evidence
    out, _ = write()
    assert all(v["definitions_identical"] is None for v in out["results"].values())
