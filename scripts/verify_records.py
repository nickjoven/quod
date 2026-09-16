#!/usr/bin/env python3
"""verify_records.py — the ledger's own consistency check (runs in CI, no Lean needed).

Checks, over the tracked records only:
  claims/**/*.yml      parse; required keys; status in the SEMANTICS lattice; lock and offered_lock are
                       64-hex; every evidence CID is 64-hex or null; a `proven` claim has proof_verdict
                       `accepted` and a `refuted` one refutation_verdict `accepted`; either carries the
                       independent replay's output CID (evidence.checker_cid) (reasons are descriptors)
  attempts/*/manifest-*.json  parse; attempts_sha256 matches the committed attempts.jsonl when present;
                       by_outcome counts sum to `attempts`; pins (when present) are full 40-hex commits
  attempts/exit*.json  parse; `pass` is a bool; cited manifest CIDs are 64-hex
  intake/*/PIN.json + RESULTS.json  parse; commit is 40-hex; recorded hashes are the right widths;
                       RESULTS.results statuses are in the lattice
  calib/RESULTS.json   parse; pins.crouzeix commits are 40-hex
Exit 0 iff every check passes; every failure is printed with its file.
"""
from __future__ import annotations

import glob, hashlib, json, os, re, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = {"stated", "proven", "refuted", "drift-fail"}   # SEMANTICS.md status lattice
HEX64 = re.compile(r"^[0-9a-f]{64}$"); HEX40 = re.compile(r"^[0-9a-f]{40}$")
problems: list[str] = []


def bad(f, msg): problems.append(f"{os.path.relpath(f, ROOT)}: {msg}")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_claims():
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "claims", "**", "*.yml"), recursive=True)):
        n += 1
        try:
            c = yaml.safe_load(open(f))
        except Exception as e:
            bad(f, f"yaml: {e}"); continue
        for k in ("id", "demonstrandum", "lock", "status", "proof_verdict", "descriptors", "evidence"):
            if k not in c: bad(f, f"missing key {k}")
        if c.get("status") not in STATUS: bad(f, f"status {c.get('status')!r} not in lattice")
        for k in ("lock", "offered_lock"):
            if k in c and c[k] is not None and not HEX64.match(str(c[k])): bad(f, f"{k} is not 64-hex")
        for k, v in (c.get("evidence") or {}).items():
            if v is not None and not HEX64.match(str(v)): bad(f, f"evidence.{k} is not a CID")
        # `reasons` are descriptor-derived (unanchored, dedup, unfolds to True): they annotate, never block, a status
        if c.get("status") == "proven" and c.get("proof_verdict") != "accepted": bad(f, "proven but proof_verdict != accepted")
        if c.get("status") == "refuted" and c.get("refutation_verdict") != "accepted": bad(f, "refuted but refutation_verdict != accepted")
        # an accepted verdict means the independent replay ran (github #7): its output CID is required
        if c.get("status") in ("proven", "refuted") and not HEX64.match(str((c.get("evidence") or {}).get("checker_cid") or "")):
            bad(f, f"{c.get('status')} without replay evidence (evidence.checker_cid)")
    return n


def check_manifests():
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "attempts", "*", "manifest-*.json"))):
        if os.path.basename(f).startswith("manifest-pre-"): continue
        n += 1
        try:
            m = json.load(open(f))
        except Exception as e:
            bad(f, f"json: {e}"); continue
        att = os.path.join(os.path.dirname(f), "attempts.jsonl")
        if os.path.exists(att) and m.get("attempts_sha256") and sha256(att) != m["attempts_sha256"]:
            bad(f, "attempts_sha256 does not match the committed attempts.jsonl")
        if "by_outcome" in m and "attempts" in m and sum(m["by_outcome"].values()) != m["attempts"]:
            bad(f, f"by_outcome sums to {sum(m['by_outcome'].values())}, attempts = {m['attempts']}")
        for k, v in (m.get("pins") or {}).items():
            if k != "lean" and not HEX40.match(str(v)): bad(f, f"pins.{k} is not a full 40-hex commit")
    return n


def check_exits():
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "attempts", "exit*.json"))):
        n += 1
        try:
            e = json.load(open(f))
        except Exception as ex:
            bad(f, f"json: {ex}"); continue
        if not isinstance(e.get("pass", e.get("pass_level1")), bool): bad(f, "no boolean pass field")
        for k, v in e.items():
            if k.endswith("manifest_cid") and v is not None and not HEX64.match(str(v)): bad(f, f"{k} is not a CID")
    return n


def check_intake():
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "intake", "*", "PIN.json"))):
        n += 1
        p = json.load(open(f))
        if not HEX40.match(p.get("commit", "")): bad(f, "commit is not 40-hex")
        for k in ("statement_file", "challenge_spec"):
            e = p.get("expected", {}).get(k, {})
            if not HEX64.match(e.get("sha256", "")) or not HEX64.match(e.get("blake3", "")): bad(f, f"expected.{k} hashes malformed")
        r = os.path.join(os.path.dirname(f), "RESULTS.json")
        if os.path.exists(r):
            res = json.load(open(r))
            for cid, v in res.get("results", {}).items():
                if v.get("status") not in STATUS: bad(r, f"{cid} status {v.get('status')!r} not in lattice")
            if any(v.get("status") in ("proven", "refuted") for v in res.get("results", {}).values()):
                ck = res.get("checker") or {}
                if not (ck.get("ran") and ck.get("exit") == 0): bad(r, "proven/refuted results without a passing checker replay")
    return n


def check_calib():
    f = os.path.join(ROOT, "calib", "RESULTS.json")
    if not os.path.exists(f): return 0
    r = json.load(open(f))
    for k, v in (r.get("pins", {}).get("crouzeix") or {}).items():
        if k != "lean" and not HEX40.match(str(v)): bad(f, f"pins.crouzeix.{k} is not a full 40-hex commit")
    for rec in r.get("controls", []):
        if rec.get("status") in ("proven", "refuted"):
            if rec.get("checker_rc") != 0: bad(f, f"{rec.get('id')}: {rec['status']} with checker_rc {rec.get('checker_rc')!r}")
            if not HEX64.match(str((rec.get("evidence") or {}).get("checker_cid") or "")): bad(f, f"{rec.get('id')}: {rec['status']} without evidence.checker_cid")
    return 1


def main() -> int:
    counts = {"claims": check_claims(), "manifests": check_manifests(), "exit_records": check_exits(), "intakes": check_intake(), "calib": check_calib()}
    print("checked:", counts)
    for p in problems: print("FAIL", p)
    print("records:", "OK" if not problems else f"{len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
