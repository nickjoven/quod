"""github #7 / Q-31: an accepted proof or refutation requires the independent
replay, and the replay must cover the module that DECLARES the offered
declaration as the environment reports it (lock.py DECLMOD), never a module
nominated by a table.

evaluate() is exercised with every gate stubbed: the lock gate returns a valid
lock plus a declaring module per declaration, the axiom gate is clean, `run`
records what it is asked to run and answers per case, and ket_put is a no-op.
No Lean runs and nothing is forged; only the acceptance logic is under test.
"""
import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("calibrate", os.path.join(ROOT, "scripts", "calibrate.py"))
C = importlib.util.module_from_spec(spec)
sys.modules["calibrate"] = C
spec.loader.exec_module(C)

LOCK = {"lock": "a" * 64, "custom_constants": [], "hypotheses": [], "reduces_to_True": False}
AX_OK = {"ok": True, "extra": [], "axioms": ["propext", "Classical.choice", "Quot.sound"]}
CHK = "/bin/lean4checker"


@pytest.fixture
def gates(monkeypatch):
    """Stub every external gate. `declaring` maps decl -> the module the
    environment says declares it (default Review.Decl, which is deliberately
    NOT the `module` the claim passes); `checker_rc` is what the replay
    answers; `refute_rc` what refute_check answers; `calls` is every argv."""
    calls, state = [], {"checker_rc": 0, "refute_rc": 0, "declaring": {}}
    monkeypatch.setattr(C, "ket_put", lambda text: None)

    def lock(proj, module, decl):
        return {**LOCK, "declaring_module": state["declaring"].get(decl, "Review.Decl")}, "raw"

    monkeypatch.setattr(C, "lock", lock)
    monkeypatch.setattr(C, "axioms", lambda proj, module, decl: (0, dict(AX_OK), "raw"))

    def run(cmd, cwd=None):
        calls.append(list(cmd))
        if "refute_check.py" in cmd[1]:
            return state["refute_rc"], "{}"
        if cmd[:2] == ["lake", "env"]:
            return state["checker_rc"], "checker output"
        raise AssertionError(f"unexpected command {cmd}")

    monkeypatch.setattr(C, "run", run)
    state["calls"] = calls
    return state


def checker_calls(state):
    return [c[3] for c in state["calls"] if c[:2] == ["lake", "env"]]


def claim(**kw):
    return dict(id="review", proj="/unused", module="Review", decl="claim", **kw)


def test_absent_checker_module_replays_the_declaring_module_not_the_import_module(gates):
    rec = C.evaluate(claim(), checker=CHK)
    assert rec["status"] == "proven" and rec["proof_verdict"] == "accepted"
    assert rec["checker_rc"] == 0 and rec["checker_module"] == "Review.Decl"
    assert checker_calls(gates) == ["Review.Decl"]


def test_explicit_module_equal_to_the_declaring_one_is_replayed(gates):
    rec = C.evaluate(claim(checker_module="Review.Decl"), checker=CHK)
    assert rec["status"] == "proven" and checker_calls(gates) == ["Review.Decl"]


@pytest.mark.parametrize("nominated", ["Review", "Review.Other", ""])
def test_nominated_module_that_does_not_declare_the_proof_is_rejected(gates, nominated):
    rec = C.evaluate(claim(checker_module=nominated), checker=CHK)
    assert rec["status"] == "stated" and rec["proof_verdict"] == "rejected: replay module mismatch"
    assert rec["checker_rc"] is None and rec["checker_module"] is None and checker_calls(gates) == []


def test_explicit_none_checker_module_is_rejected_not_proven(gates):
    rec = C.evaluate(claim(checker_module=None), checker=CHK)
    assert rec["status"] == "stated" and rec["proof_verdict"] == "rejected: no replay"
    assert rec["checker_rc"] is None and checker_calls(gates) == []


def test_unknown_declaring_module_is_rejected(gates):
    gates["declaring"]["claim"] = "_local"
    rec = C.evaluate(claim(), checker=CHK)
    assert rec["status"] == "stated" and rec["proof_verdict"] == "rejected: no replay"
    assert checker_calls(gates) == []


def test_checker_failure_rejects_the_proof(gates):
    gates["checker_rc"] = 1
    rec = C.evaluate(claim(), checker=CHK)
    assert rec["status"] == "stated" and rec["proof_verdict"] == "rejected: lean4checker"
    assert rec["checker_rc"] == 1 and rec["checker_module"] == "Review.Decl"


def test_refutation_replays_its_own_declaring_module_under_its_own_keys(gates):
    gates["declaring"]["not_claim"] = "Review.NegDecl"
    refutation = dict(module="Review.Neg", decl="not_claim")
    rec = C.evaluate(claim(refutation=refutation), checker=CHK)
    assert rec["status"] == "refuted" and rec["refutation_verdict"] == "accepted"
    assert rec["refutation_checker_module"] == "Review.NegDecl" and rec["refutation_checker_rc"] == 0
    assert "checker_module" not in rec and checker_calls(gates) == ["Review.NegDecl"]
    # a nomination of the module that merely IMPORTS the refutation is refused
    rec = C.evaluate(claim(refutation=refutation, checker_module="Review.Neg"), checker=CHK)
    assert rec["status"] == "stated" and rec["refutation_verdict"] == "rejected: replay module mismatch"
    gates["checker_rc"] = 1
    rec = C.evaluate(claim(refutation=refutation), checker=CHK)
    assert rec["status"] == "stated" and rec["refutation_verdict"] == "rejected: lean4checker"
    rec = C.evaluate(claim(refutation=refutation, checker_module=None), checker=CHK)
    assert rec["status"] == "stated" and rec["refutation_verdict"] == "rejected: no replay"


def test_proof_and_refutation_keep_both_replays(gates):
    gates["declaring"]["not_claim"] = "Review.NegDecl"
    rec = C.evaluate(claim(refutation=dict(module="Review.Neg", decl="not_claim"),
                           demonstrandum=dict(proj="/unused", module="Review.D", decl="d")), checker=CHK)
    assert rec["status"] == "inconsistent"
    assert rec["checker_module"] == "Review.Decl" and rec["checker_rc"] == 0
    assert rec["refutation_checker_module"] == "Review.NegDecl" and rec["refutation_checker_rc"] == 0
    assert sorted(checker_calls(gates)) == ["Review.Decl", "Review.NegDecl"]


def test_stale_lock_still_fails_early_without_replay(gates):
    rec = C.evaluate(claim(stale_lock="0" * 64), checker=CHK)
    assert rec["status"] == "drift-fail" and checker_calls(gates) == []
