"""Extend development time samples, retaining the fixed coupling/grid ladders."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy

import vacuum_certificate_run as certificates
import vacuum_certified as certified
import vacuum_development as baseline
import vacuum_refinement as refinement
import vacuum_semigroup as semigroup
import vacuum_time_windows as windows

TAU = (*semigroup.TAU, 12., 16., 20., 24.)
TOLERANCES = ((1e-8, 1e-18), (1e-10, 1e-20))
SOURCES = (*windows.SOURCES, "scripts/vacuum_late_time_run.py")


def source_hashes():
    return {p: hashlib.sha256((baseline.ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def load_inputs():
    reports, hashes = {}, {}
    for name in ("semigroup.json", "refinement.json", "certificates.json"):
        raw = (baseline.ROOT / "research/vacuum-spectrum" / name).read_bytes()
        report = json.loads(raw)
        if report["state"] != "completed" or report["targets_run"] != 0:
            raise ValueError("incomplete input " + name)
        if [c["g"] for c in report["cells"]] != list(baseline.G_VALUES):
            raise ValueError("input coordinate mismatch " + name)
        for path, expected in report["source_sha256"].items():
            if hashlib.sha256((baseline.ROOT / path).read_bytes()).hexdigest() != expected:
                raise ValueError("input source drift " + path)
        reports[name], hashes[name] = report, hashlib.sha256(raw).hexdigest()
    if reports["certificates.json"]["input_sha256"] != hashes["semigroup.json"]:
        raise ValueError("certificate/semigroup input mismatch")
    return reports, hashes


def extended_certificate(source_cell, times):
    final = source_cell["rungs"][-1]["result"]
    eigen = [{key: F(value) if key in ("lower", "upper", "finite_lower", "tail_floor") else value
              for key, value in row.items()} for row in final["enclosures"]]
    if not certified.verify_enclosures(source_cell["g"], 1, final["size"], eigen):
        raise ValueError("cached certificate endpoints failed")
    correlations = certified.correlation_intervals(eigen, windows.numeric(final["overlaps"]),
        windows.numeric(final["vacuum"]), [F(float(t)) for t in times])
    if correlations is None:
        raise ValueError("extended correlation certificate unavailable")
    return {"g": source_cell["g"], "times": [F(float(t)) for t in times],
            "rungs": [{"result": {**final, "correlations": correlations}}]}


def accounting(report):
    if (report["targets_run"] != 0 or not baseline.coverage(report["targets"])
            or any(t["status"] != "unrun" for t in report["targets"])
            or [c["g"] for c in report["cells"]] != list(baseline.G_VALUES)):
        return False
    for cell in report["cells"]:
        if cell["eta"] != 1 or cell["partition"] != "development":
            return False
        if [r["rung"] for r in cell["rungs"]] != list(baseline.ANGLE_INTERIORS):
            return False
        for rung in cell["rungs"]:
            if rung["status"] not in ("completed", "failure"):
                return False
            if [(e["rtol"], e["atol"]) for e in rung["evolutions"]] != list(TOLERANCES):
                return False
            if any(e["status"] not in ("completed", "failure") for e in rung["evolutions"]):
                return False
    return True


def run(output):
    inputs, hashes = load_inputs()
    began = time.monotonic()
    report = {"schema_version": 1, "state": "running", "registered": False, "targets_run": 0,
              "targets": inputs["semigroup.json"]["targets"], "source_sha256": source_hashes(),
              "input_sha256": hashes, "dimensionless_times": list(TAU),
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "extension_reason": "original samples do not support both observable gap estimators in nine development cells",
              "ground_policy": "reuse archived finest refinement ground; recompute other fixed rungs",
              "cells": [{"g": g, "eta": 1, "partition": "development", "status": "pending",
                         "rungs": [{"method": "angle_fourth", "rung": n, "status": "pending",
                                    "evolutions": [{"rtol": r, "atol": a, "status": "pending"} for r, a in TOLERANCES]}
                                   for n in baseline.ANGLE_INTERIORS]} for g in baseline.G_VALUES],
              "limitations": ["Qualification concerns sampled development pairs only",
                              "No registered windows, target selection or target execution",
                              "Certificate analytic/arithmetic trusted base is unchanged",
                              "Cached ground reuse is explicit; it is not an independent ground solve"]}

    def checkpoint(event, **fields):
        baseline.write_report(output, certificates.encode(report))
        print(json.dumps({"event": event, "elapsed_seconds": time.monotonic() - began, **fields}), flush=True)

    checkpoint("started")
    for index, cell in enumerate(report["cells"]):
        cell["status"] = "running"
        prior = inputs["semigroup.json"]["cells"][index]
        reference = [r for r in prior["rungs"] if r["method"] == "character"][-1]["result"]
        times = np.asarray(TAU) / reference["first_three_gaps"][0]
        if times[:len(semigroup.TAU)].tolist() != prior["times"]:
            raise ValueError("old time samples changed")
        cell["times"] = times.tolist()
        certificate_cell = extended_certificate(inputs["certificates.json"]["cells"][index], times)
        cell["certified_correlations"] = certificate_cell["rungs"][-1]["result"]["correlations"]
        for rung in cell["rungs"]:
            rung["status"] = "running"
            checkpoint("ground_started", g=cell["g"], interiors=rung["rung"])
            start = time.monotonic()
            try:
                cached = rung["rung"] == baseline.ANGLE_INTERIORS[-1]
                ground_record = inputs["refinement.json"]["cells"][index]["final"]["angle_fourth"] if cached else \
                    semigroup.angle_refined(cell["g"], 1, rung["rung"])
                refinement.validate_record(ground_record)
                if ground_record["interiors"] != rung["rung"]:
                    raise ValueError("cached ground grid mismatch")
                matrix, observables = semigroup.angle_matrix(cell["g"], 1, rung["rung"])
                vectors = semigroup.centered_vectors(ground_record["ground"], observables)
                rung["ground_origin"] = "archived_refinement" if cached else "fresh_banded_solve"
                rung["ground_residual"] = float(np.linalg.norm(matrix @ np.asarray(ground_record["ground"])
                    - ground_record["E0"] * np.asarray(ground_record["ground"])))
                rung["ground_elapsed_seconds"] = time.monotonic() - start
            except Exception as exc:
                rung.update(status="failure", reason=f"{type(exc).__name__}: {exc}")
                for evolution in rung["evolutions"]:
                    evolution.update(status="failure", reason="ground preparation failed")
                checkpoint("ground_failed", g=cell["g"], interiors=rung["rung"])
                continue
            for evolution in rung["evolutions"]:
                evolution["status"] = "running"
                checkpoint("evolution_started", g=cell["g"], interiors=rung["rung"], rtol=evolution["rtol"])
                start = time.monotonic()
                try:
                    result = semigroup.propagate(matrix, ground_record["E0"], vectors, times,
                        evolution["rtol"], evolution["atol"])
                    json.dumps(result, allow_nan=False)
                    evolution.update(status="completed", result=result)
                except Exception as exc:
                    evolution.update(status="failure", reason=f"{type(exc).__name__}: {exc}")
                evolution["elapsed_seconds"] = time.monotonic() - start
                checkpoint("evolution_completed", g=cell["g"], interiors=rung["rung"], status=evolution["status"])
            rung["status"] = "completed" if all(e["status"] == "completed" for e in rung["evolutions"]) else "failure"
        complete = {**cell, "rungs": [r for r in cell["rungs"] if r["status"] == "completed"]}
        cell["window_assessment"] = windows.assess_cell(certificate_cell, complete)
        final = certificate_cell["rungs"][-1]["result"]
        cell["angle_error_bounds"] = certificates.angle_error_bounds(final["correlations"],
            windows.numeric(final["vacuum"]), complete["rungs"])
        cell["status"] = "unresolved" if all(r["status"] == "completed" for r in cell["rungs"]) else "failure"
        checkpoint("cell_completed", g=cell["g"], status=cell["status"])
    report["accounting_pass"] = accounting(report)
    report["source_unchanged_during_run"] = source_hashes() == report["source_sha256"]
    passed = report["accounting_pass"] and report["source_unchanged_during_run"] and all(c["status"] != "failure" for c in report["cells"])
    report["state"] = "completed" if passed else "instrument_failure"
    report["elapsed_seconds"] = time.monotonic() - began
    checkpoint("completed", state=report["state"])
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.name in ("certificates.json", "semigroup.json", "refinement.json", "development.json", "preflight.json",
                           "evidence-audit.json", "refinement-audit.json", "time-windows.json"):
        parser.error("output must not overwrite earlier evidence")
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
