"""Checkpointed fixed-manifest SU(2) semigroup development run; no targets."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy

import vacuum_development as baseline
import vacuum_refinement as refinement
import vacuum_semigroup as semigroup

SOURCES = (*refinement.SOURCES, "scripts/vacuum_semigroup.py", "scripts/vacuum_semigroup_run.py")


def source_hashes():
    return {p: hashlib.sha256((baseline.ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def accounting(report):
    expected = [("character", j) for j in baseline.CHARACTER_J]
    expected += [("angle_fourth", n) for n in baseline.ANGLE_INTERIORS]
    if (report["targets_run"] != 0 or not baseline.coverage(report["targets"])
            or any(r["status"] != "unrun" for r in report["targets"])
            or [c["g"] for c in report["cells"]] != list(baseline.G_VALUES)):
        return False
    for cell in report["cells"]:
        if cell["eta"] != 1 or cell["partition"] != "development":
            return False
        if [(r["method"], r["rung"]) for r in cell["rungs"]] != expected:
            return False
        for rung in cell["rungs"]:
            if rung["status"] not in ("completed", "failure"):
                return False
            if rung["method"] == "angle_fourth":
                if [(e["rtol"], e["atol"]) for e in rung["evolutions"]] != list(semigroup.TOLERANCES):
                    return False
                if any(e["status"] not in ("completed", "failure") for e in rung["evolutions"]):
                    return False
    return True


def run(output):
    start = time.monotonic()
    report = {"schema_version": 1, "state": "running", "registered": False,
              "source_sha256": source_hashes(), "targets_run": 0,
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "scipy": scipy.__version__},
              "dimensionless_times": list(semigroup.TAU),
              "time_convention": "t=tau / finest character first gap, shared across all rungs",
              "targets": [{"id": row, "status": "unrun"} for row in baseline.target_ids()],
              "cells": [], "limitations": [
                  "Shared ground eigensolver and SciPy; independent propagation, not independent libraries",
                  "Tolerance refinement differences are not validated propagation error bounds",
                  "No certified mesh, quadrature, overlap or combined error budget",
                  "Time samples are diagnostics, not accepted windows or resolved thresholds",
                  "No U1, pilot replication, registration, ket validation or sieve verdict"]}
    for g in baseline.G_VALUES:
        rungs = [{"method": "character", "rung": j, "status": "pending"}
                 for j in baseline.CHARACTER_J]
        rungs += [{"method": "angle_fourth", "rung": n, "status": "pending",
                   "evolutions": [{"rtol": rtol, "atol": atol, "status": "pending"}
                                  for rtol, atol in semigroup.TOLERANCES]}
                  for n in baseline.ANGLE_INTERIORS]
        report["cells"].append({"g": g, "eta": 1, "partition": "development",
                                "status": "pending", "rungs": rungs})

    def checkpoint(event, **fields):
        baseline.write_report(output, report)
        print(json.dumps({"event": event, "elapsed_seconds": time.monotonic() - start,
                          **fields}), flush=True)

    def execute(slot, function, **fields):
        slot["status"] = "running"
        checkpoint("request_started", **fields)
        began = time.monotonic()
        try:
            result = function()
            # Strict finite serialization before admitting any result to a checkpoint.
            json.dumps(result, allow_nan=False)
            slot.update(status="completed", result=result)
        except Exception as exc:
            slot.update(status="failure", reason=f"{type(exc).__name__}: {exc}")
        slot["elapsed_seconds"] = time.monotonic() - began
        checkpoint("request_completed", status=slot["status"], **fields)

    checkpoint("started")
    try:
        report["calibration"] = semigroup.calibration()
    except Exception as exc:
        report["calibration"] = {"pass": False, "reason": f"{type(exc).__name__}: {exc}"}
    if not report["calibration"]["pass"]:
        report["state"] = "instrument_failure"
        checkpoint("calibration_failed")
        return 1
    for cell in report["cells"]:
        cell["status"] = "running"
        g = cell["g"]
        chars = [r for r in cell["rungs"] if r["method"] == "character"]
        angles = [r for r in cell["rungs"] if r["method"] == "angle_fourth"]
        records = {}
        for rung in chars:
            def character_solve():
                record = baseline.character(g, 1, rung["rung"])
                refinement.validate_record(record)
                records[rung["rung"]] = record
                return baseline.compact(record)
            execute(rung, character_solve, g=g, method="character", rung=rung["rung"])
        if chars[-1]["status"] != "completed":
            for rung in angles:
                for slot in (rung, *rung["evolutions"]):
                    slot.update(status="failure", reason="finest character time reference unavailable")
            cell["status"] = "failure"
            checkpoint("cell_failed", g=g)
            continue
        reference = records[baseline.CHARACTER_J[-1]]
        times = np.asarray(semigroup.TAU) / reference["first_three_gaps"][0]
        covariance = np.asarray(reference["covariance"])
        cell["times"] = times.tolist()
        cell["reference_covariance"] = covariance.tolist()
        reference_correlations = semigroup.spectral_correlations(reference, times)
        previous = None
        for rung in chars:
            if rung["status"] == "completed":
                corr = semigroup.spectral_correlations(records[rung["rung"]], times)
                rung["result"]["correlations"] = corr.tolist()
                if previous is not None:
                    rung["adjacent_rung_difference"] = semigroup.comparison(corr, previous, covariance)
                previous = corr
            else:
                previous = None
        previous = None
        for rung in angles:
            prepared = {}
            def prepare():
                record = semigroup.angle_refined(g, 1, rung["rung"])
                refinement.validate_record(record)
                matrix, observables = semigroup.angle_matrix(g, 1, rung["rung"])
                vectors = semigroup.centered_vectors(record["ground"], observables)
                prepared.update(matrix=matrix, vectors=vectors, e0=record["E0"])
                result = baseline.compact(record)
                result.update(low_state_correlations=semigroup.spectral_correlations(record, times).tolist(),
                              centered_covariance=(vectors.T @ vectors).tolist(),
                              independently_assembled_ground_residual=float(np.linalg.norm(
                                  matrix @ np.asarray(record["ground"]) - record["E0"] * np.asarray(record["ground"]))),
                              centering_residual=(np.asarray(record["ground"]) @ vectors).tolist())
                return result
            execute(rung, prepare, g=g, method="angle_ground", rung=rung["rung"])
            if rung["status"] == "failure":
                for slot in rung["evolutions"]:
                    slot.update(status="failure", reason="angle preparation failed")
                previous = None
                checkpoint("angle_preparation_failed", g=g, rung=rung["rung"])
                continue
            for evolution in rung["evolutions"]:
                execute(evolution, lambda: semigroup.propagate(
                    prepared["matrix"], prepared["e0"], prepared["vectors"], times,
                    evolution["rtol"], evolution["atol"]),
                    g=g, method="BDF", rung=rung["rung"], rtol=evolution["rtol"])
            if any(e["status"] != "completed" for e in rung["evolutions"]):
                rung.update(status="failure", reason="one or more evolutions failed")
                previous = None
                continue
            coarse, fine = [e["result"]["correlations"] for e in rung["evolutions"]]
            rung["tolerance_difference"] = semigroup.comparison(coarse, fine, covariance)
            rung["character_difference"] = semigroup.comparison(fine, reference_correlations, covariance)
            rung["low_state_difference"] = semigroup.comparison(fine, rung["result"]["low_state_correlations"], covariance)
            if previous is not None:
                rung["adjacent_rung_difference"] = semigroup.comparison(fine, previous, covariance)
            previous = fine
            checkpoint("rung_analyzed", g=g, rung=rung["rung"])
        cell["status"] = "failure" if any(r["status"] == "failure" for r in cell["rungs"]) else "unresolved"
        cell["usable_time_window"] = None
        cell["thresholds"] = [None, None]
        checkpoint("cell_completed", g=g, status=cell["status"])
    report["accounting_pass"] = accounting(report)
    report["source_unchanged_during_run"] = source_hashes() == report["source_sha256"]
    passed = report["accounting_pass"] and report["source_unchanged_during_run"] and all(
        c["status"] == "unresolved" for c in report["cells"])
    report["state"] = "completed" if passed else "instrument_failure"
    report["elapsed_seconds"] = time.monotonic() - start
    checkpoint("completed", state=report["state"])
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protected = {baseline.ROOT / "research/vacuum-spectrum" / name for name in
                 ("refinement.json", "development.json", "preflight.json", "evidence-audit.json",
                  "refinement-audit.json")}
    if args.output.resolve() in protected:
        parser.error("output must not overwrite prior evidence")
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
