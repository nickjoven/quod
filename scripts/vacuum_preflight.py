#!/usr/bin/env python3
"""Exact development controls and holdout accounting; never executes target cells."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "research/vacuum-spectrum"


def target_ids():
    return [f"{theory}:g={g}:eta={eta}"
            for theory in ("SU2", "U1")
            for g in ("0.125", "0.25", "0.40", "0.60", "0.85", "1.25", "2.50")
            for eta in ("0", "0.5", "1")]


def multiply_p(state):
    # Exact character identity P chi_j = (chi_(j+1/2)+chi_(j-1/2))/2.
    out = {}
    for n, value in state.items():
        for neighbor in (n - 1, n + 1):
            if neighbor >= 0:
                out[neighbor] = out.get(neighbor, F(0)) + value / 2
    return out


def controls(mutant=None):
    omega = {0: F(1)}
    p = multiply_p(omega)
    p2 = multiply_p(p)  # multiply in the infinite basis before projecting
    mean2 = F(1, 2) if mutant == "wrong_haar" else p2[0]
    centered = dict(p2)
    if mutant != "omitted_centering":
        centered[0] -= mean2
    g = F(1, 2)  # development coordinate; eta=0 analytic calibration
    gap = 3 * g * g
    offset = F(7)
    reported_shifted_gap = offset + gap if mutant == "absolute_E1" else gap
    rows = target_ids()
    if mutant == "missing_target":
        rows.pop()
    return {
        "haar_mean_p2": mean2 == F(1, 4),
        "centering_vacuum_component": centered[0] == 0,
        "free_p_weight": p == {1: F(1, 2)},
        "free_p2_excited_weight": centered.get(2) ** 2 == F(1, 16),
        "energy_offset_gap": reported_shifted_gap == gap,
        "target_coverage": len(rows) == 42 and set(rows) == set(target_ids()),
        # A finite cutoff square loses the path N -> N+1 -> N.
        "cutoff_edge": multiply_p(multiply_p({4: F(1)}))[4] == F(1, 2),
    }


def evaluate():
    checks = controls()
    named = {"wrong_haar": "haar_mean_p2",
             "omitted_centering": "centering_vacuum_component",
             "absolute_E1": "energy_offset_gap",
             "missing_target": "target_coverage"}
    mutants = {name: {"named_check": check, "rejected": not controls(name)[check]}
               for name, check in named.items()}
    return checks, mutants


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    print(json.dumps({"event": "started", "task": "ym-vacuum-gap-litcheck"}), flush=True)
    checks, mutants = evaluate()
    ok = all(checks.values()) and all(m["rejected"] for m in mutants.values())
    sources = [Path(__file__), STUDY / "README.md", STUDY / "sieve-dims.json"]
    report = {
        "schema_version": 1, "state": "unregistered", "P_id": None, "LC_id": None,
        "preflight_pass": ok, "target_execution_enabled": False,
        "checks": checks, "mutants": mutants,
        "targets": [{"id": row, "status": "unrun", "reason": "registration prerequisites incomplete"}
                    for row in target_ids()],
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "limitations": ["Exact fixture checks only; no numerical solver validated",
                        "No independent discretization or semigroup implemented",
                        "No registered numerical error budget or P/LC assignment"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"event": "completed", "preflight_pass": ok,
                      "elapsed_seconds": time.monotonic() - start,
                      "target_rows": len(report["targets"]), "targets_run": 0}), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
