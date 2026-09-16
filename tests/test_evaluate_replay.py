"""github #7: an accepted proof or refutation requires the independent replay.

evaluate() is exercised with every gate stubbed: the lock and axiom gates return
valid results, `run` records what it is asked to run and answers per case, and
ket_put is a no-op. No Lean runs and nothing is forged; only the acceptance
logic is under test.
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


@pytest.fixture
def gates(monkeypatch):
    """Stub every external gate; `calls` collects each argv `run` saw; `checker_rc`
    is what the replay answers; `refute_rc` what refute_check answers."""
    calls, state = [], {"checker_rc": 0, "refute_rc": 0}
    monkeypatch.setattr(C, "ket_put", lambda text: None)
    monkeypatch.setattr(C, "lock", lambda proj, module, decl: (dict(LOCK), "raw"))
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
    return [c for c in state["calls"] if c[:2] == ["lake", "env"]]


def claim(**kw):
    return dict(id="review", proj="/unused", module="Review", decl="claim", **kw)


def test_absent_checker_module_derives_the_declaring_module_and_replays(gates):
    rec = C.evaluate(claim(), checker="/bin/lean4checker")
    assert rec["status"] == "proven" and rec["proof_verdict"] == "accepted"
    assert rec["checker_rc"] == 0 and rec["checker_module"] == "Review"
    assert checker_calls(gates) == [["lake", "env", "/bin/lean4checker", "Review"]]


def test_explicit_none_checker_module_is_rejected_not_proven(gates):
    rec = C.evaluate(claim(checker_module=None), checker="/bin/lean4checker")
    assert rec["status"] == "stated" and rec["proof_verdict"] == "rejected: no replay"
    assert rec["checker_rc"] is None and checker_calls(gates) == []


def test_checker_failure_rejects_the_proof(gates):
    gates["checker_rc"] = 1
    rec = C.evaluate(claim(checker_module="Review.Mod"), checker="/bin/lean4checker")
    assert rec["status"] == "stated" and rec["proof_verdict"] == "rejected: lean4checker"
    assert rec["checker_rc"] == 1 and rec["checker_module"] == "Review.Mod"


def test_checker_success_proves_with_explicit_module(gates):
    rec = C.evaluate(claim(checker_module="Review.Mod"), checker="/bin/lean4checker")
    assert rec["status"] == "proven" and rec["checker_rc"] == 0
    assert checker_calls(gates) == [["lake", "env", "/bin/lean4checker", "Review.Mod"]]


def test_refutation_requires_replay_too(gates):
    refutation = dict(module="Review.Neg", decl="not_claim")
    rec = C.evaluate(claim(refutation=refutation), checker="/bin/lean4checker")
    assert rec["status"] == "refuted" and rec["refutation_verdict"] == "accepted"
    assert rec["checker_module"] == "Review.Neg"
    gates["checker_rc"] = 1
    gates["calls"].clear()
    rec = C.evaluate(claim(refutation=refutation), checker="/bin/lean4checker")
    assert rec["status"] == "stated" and rec["refutation_verdict"] == "rejected: lean4checker"
    rec = C.evaluate(claim(refutation=refutation, checker_module=None), checker="/bin/lean4checker")
    assert rec["status"] == "stated" and rec["refutation_verdict"] == "rejected: no replay"


def test_stale_lock_still_fails_early_without_replay(gates):
    rec = C.evaluate(claim(stale_lock="0" * 64, checker_module=None), checker="/bin/lean4checker")
    assert rec["status"] == "drift-fail" and checker_calls(gates) == []
