#!/usr/bin/env python3
"""fixtures.py — controlled failures for the openai-ns intake (github #8, deliverable 3), evidence level.

    fixtures.py [--keep DIR] [--run DIR]

Each fixture is an isolated copy of the sealed evidence (the historical records by default, or a
runs/<id> directory with --run) with exactly one thing changed, never the upstream proof and never
the tracked evidence. The claim writer and the integrity check are then run on the copy and the
observed verdict / exit code is compared with the expected one. Exit 0 iff every fixture behaves as
expected, including the positive control.

Why a positive control: a writer that rejected everything would pass every negative fixture. The
untouched copy must come out `proven` with integrity 0, or the rejections prove nothing.

What these fixtures do NOT exercise: Lean. A fixture that changes bytes in a lock file shows what the
writer does when a lock differs; it does not show lock.py computing a different lock from a changed
theorem. Lean-level fixtures (a module with a changed statement, a `sorry`, a replay that fails on a
planted kernel error) are listed in OPEN.yml Q-34 and need the pinned toolchain and the Lean lock.
"""
import argparse
import io
import json
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import reproduce as R  # noqa: E402
import write_claims as W  # noqa: E402

PIN = json.load(open(os.path.join(HERE, "PIN.json")))


def jload(p):
    t = open(p).read(); return json.loads(t[t.index("{"):t.rindex("}") + 1])


def make_copy(src_run: str | None, dst: str) -> dict:
    """A run-shaped directory: evidence/, RESULTS.json, claims/, PIN.json, port/, and the
    historical build.log + Intake port substitute when copying the historical records."""
    os.makedirs(dst, exist_ok=True)
    if src_run:
        for name in ("evidence", "claims"):
            shutil.copytree(os.path.join(src_run, name), os.path.join(dst, name))
        shutil.copyfile(os.path.join(src_run, "RESULTS.json"), os.path.join(dst, "RESULTS.json"))
        closure, checker = os.path.join(dst, "evidence", "closure-modules.txt"), os.path.join(dst, "evidence", "checker-modules.txt")
    else:
        shutil.copytree(os.path.join(HERE, "evidence"), os.path.join(dst, "evidence"))
        shutil.copytree(os.path.join(ROOT, "claims", "openai-ns"), os.path.join(dst, "claims"))
        shutil.copyfile(os.path.join(HERE, "RESULTS.json"), os.path.join(dst, "RESULTS.json"))
        shutil.copytree(os.path.join(HERE, "port"), os.path.join(dst, "port"))
        for f in ("PIN.json", "PIN-verified.txt", "build.log"):
            if os.path.exists(os.path.join(HERE, f)): shutil.copyfile(os.path.join(HERE, f), os.path.join(dst, f))
        checker = os.path.join(dst, "evidence", "checker-modules.txt")
        # the historical closure list includes the port module, which the historical checker rightly skipped;
        # the fixture's closure list lives outside evidence/ so no cited byte changes
        closure = os.path.join(dst, "closure-for-fixtures.txt")
        open(closure, "w").write(open(checker).read())
    cids_path = os.path.join(dst, "evidence", "CIDS.json")
    return {"dir": dst, "E": os.path.join(dst, "evidence"), "cids": json.load(open(cids_path)), "closure": closure, "checker": checker}


def write(c: dict) -> dict:
    out = W.write(c["E"], PIN, c["cids"], os.path.join(c["dir"], "RESULTS-fixture.json"), os.path.join(c["dir"], "claims-fixture"),
                  closure_modules=c["closure"], checker_modules=c["checker"])
    return {k: v["proof_verdict"] for k, v in out["results"].items()}


def integrity(c: dict) -> int:
    with redirect_stdout(io.StringIO()):
        return R.integrity(c["dir"])


# ---------------------------------------------------------------- the fixtures: (name, mutation, expected verdicts, expected integrity exit, why)

def mut_positive(c): pass


def mut_mismatched_target(c):
    p = os.path.join(c["E"], "lock-solution_R3.json"); j = jload(p); j["lock"] = "f" * 64
    json.dump(j, open(p, "w"))


def mut_disallowed_axiom(c):
    p = os.path.join(c["E"], "axioms-solution.json"); j = jload(p)
    j["results"][1].update({"ok": False, "extra": ["sorryAx"], "axioms": j["results"][1]["axioms"] + ["sorryAx"]})
    json.dump(j, open(p, "w"))


def mut_modified_artifact(c):
    with open(os.path.join(c["E"], "checker.log"), "a") as f: f.write(" ")


def mut_missing_replay(c):
    os.unlink(os.path.join(c["E"], "checker.log"))


def mut_failed_replay(c):
    p = os.path.join(c["E"], "checker.log"); text = open(p).read()
    open(p, "w").write(text.replace("checker exit 0", "checker exit 1"))


def mut_partial_replay(c):
    mods = open(c["checker"]).read().split()
    open(c["checker"], "w").write("\n".join(m for m in mods if m != "NavierStokes.ComparatorTheorem") + "\n")


def mut_definitions_differ(c):
    one = {"equal": False, "differ": ["NavierStokes.Comparator.divergence"], "only_challenge": [], "only_solution": [], "constants": 12}
    json.dump({"all_equal": False, "per_demonstrandum": {"R3": dict(one), "periodic": dict(one)}}, open(os.path.join(c["E"], "definitions.json"), "w"))
    c["cids"]["evidence/definitions.json"] = {"cid": "0" * 64, "sha256": "0" * 64}


ACCEPT = {"OPENAI-NS-R3": "accepted", "OPENAI-NS-PERIODIC": "accepted"}
FIXTURES = [
    ("positive-control", mut_positive, ACCEPT, 0,
     "untouched copy: proven and every byte matches; without this the rejections below prove nothing"),
    ("mismatched-target", mut_mismatched_target, {"OPENAI-NS-R3": "rejected: lock mismatch", "OPENAI-NS-PERIODIC": "accepted"}, R.EXIT_STEP,
     "the offered proof's lock no longer equals the demonstrandum's: the proof proves something else"),
    ("disallowed-axiom", mut_disallowed_axiom, {"OPENAI-NS-R3": "accepted", "OPENAI-NS-PERIODIC": "rejected: extra axioms ['sorryAx']"}, R.EXIT_STEP,
     "the axiom gate reports sorryAx on the periodic theorem: a placeholder, not a proof"),
    ("modified-artifact", mut_modified_artifact, ACCEPT, R.EXIT_STEP,
     "one byte appended to the checker log: the writer still reads 'exit 0', integrity catches the changed bytes; "
     "the two assurances are different and both are needed"),
    ("missing-replay", mut_missing_replay, {"OPENAI-NS-R3": "pending: lean4checker", "OPENAI-NS-PERIODIC": "pending: lean4checker"}, R.EXIT_MISSING,
     "no checker log: pending, never proven (github #7 for this writer); integrity reports the cited file absent"),
    ("failed-replay", mut_failed_replay, {"OPENAI-NS-R3": "rejected: lean4checker", "OPENAI-NS-PERIODIC": "rejected: lean4checker"}, R.EXIT_STEP,
     "the replay exited 1: the kernel rejected something in the closure"),
    ("partial-replay", mut_partial_replay, {"OPENAI-NS-R3": "rejected: replay did not cover the closure", "OPENAI-NS-PERIODIC": "rejected: replay did not cover the closure"}, R.EXIT_STEP,
     "one closure module left out of the replay: a passing replay over the wrong set is not a replay (Q-31 for intakes)"),
    ("definitions-differ", mut_definitions_differ, {"OPENAI-NS-R3": "rejected: definitions differ", "OPENAI-NS-PERIODIC": "rejected: definitions differ"}, 0,
     "equal locks but the names mean different things on the two sides (Q-32); the bytes are what they claim to be, so integrity "
     "passes: a verdict and an integrity check answer different questions"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keep", help="directory to keep the fixture copies in (default: a temporary directory, removed)")
    ap.add_argument("--run", help="a runs/<id> directory to take the evidence from (default: the historical records)")
    a = ap.parse_args()
    base = a.keep or tempfile.mkdtemp(prefix="openai-ns-fixtures-")
    ok = True
    print(f"{'fixture':20} {'verdicts':64} {'integrity':9} result")
    for name, mut, want, want_rc, why in FIXTURES:
        c = make_copy(a.run, os.path.join(base, name))
        mut(c)
        got, rc = write(c), integrity(c)
        good = got == want and rc == want_rc
        ok &= good
        v = ", ".join(f"{k[10:]}={got[k]}" for k in sorted(got))
        print(f"{name:20} {v:64} exit {rc:<4} {'as expected' if good else 'UNEXPECTED (wanted ' + str(want) + ' exit ' + str(want_rc) + ')'}")
        print(f"{'':20} {why}")
    if not a.keep:
        shutil.rmtree(base)
    else:
        print(f"fixture copies kept under {base}")
    print("fixtures: " + ("every rejection and the positive control behaved as expected" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
