#!/usr/bin/env python3
"""Refine the same SU(2) development cells; target execution is unavailable."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy

import vacuum_development as baseline
from vacuum_angle_refined import angle_refined
from vacuum_convergence import convergence_diagnostics

ROOT = baseline.ROOT
SOURCES = ("scripts/vacuum_refinement.py", "scripts/vacuum_angle_refined.py",
           "scripts/vacuum_development.py", "scripts/vacuum_preflight.py", "scripts/vacuum_convergence.py")


def source_hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def methods():
    return (("character", baseline.CHARACTER_J, baseline.character),
            ("angle_second", baseline.ANGLE_INTERIORS, baseline.angle),
            ("angle_fourth", baseline.ANGLE_INTERIORS, angle_refined))


def finite_goal(diff):
    moments = np.asarray(diff["moment_absolute"])
    gaps = np.asarray(diff["gap_relative"])
    return bool(moments.shape == (5,) and gaps.shape == (3,)
                and np.isfinite(moments).all() and np.isfinite(gaps).all()
                and (moments >= 0).all() and (gaps >= 0).all()
                and (moments <= baseline.MOMENT_GOAL).all()
                and (gaps <= baseline.GAP_GOAL).all())


def validate_record(record):
    # Reject nonfinite numbers before mutating the checkpointed report.
    def walk(value):
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)
        elif isinstance(value, (float, np.floating)) and not np.isfinite(value):
            raise ValueError("nonfinite solver record")
    walk(record)
    energies = np.asarray(record["energies"])
    gaps = np.asarray(record["first_three_gaps"])
    ground = np.asarray(record["ground"])
    if energies.ndim != 1 or len(energies) < 4 or not (np.diff(energies) >= 0).all():
        raise ValueError("unordered or missing eigenvalues")
    if gaps.shape != (3,) or not (gaps > 0).all():
        raise ValueError("missing or nonpositive development gaps")
    if not np.allclose(gaps, energies[1:4] - energies[0], rtol=1e-12, atol=1e-12):
        raise ValueError("gaps do not match ordered eigenvalues")
    if len(record["moments"]) != 5 or ground.ndim != 1 or abs(ground @ ground - 1) > 1e-9:
        raise ValueError("moment shape or ground normalization")
    if np.asarray(record["weights"]).shape != (len(energies) - 1, 2):
        raise ValueError("spectral weight coverage")


def accounting(report):
    if report["targets_run"] != 0 or not baseline.coverage(report["targets"]):
        return False
    if not all(row["status"] == "unrun" for row in report["targets"]):
        return False
    if [c["g"] for c in report["cells"]] != list(baseline.G_VALUES):
        return False
    expected = [(name, rung) for name, ladder, _ in methods() for rung in ladder]
    for cell in report["cells"]:
        if cell["eta"] != 1 or cell["partition"] != "development":
            return False
        if [(r["method"], r["rung"]) for r in cell["rungs"]] != expected:
            return False
        if not all(r["status"] in ("completed", "failure") for r in cell["rungs"]):
            return False
    return True


def calibration():
    checks = baseline.calibration()
    free = angle_refined(.5, 0, 600)
    validate_record(free)
    h = free["spacing"]
    lam = 4 / h**2 * np.sin(np.arange(1, 5) * h / 2)**2
    exact = .25 * (lam + h**2 * lam**2 / 12 - 1)
    checks["checks"]["fourth_order_free_dispersion"] = bool(
        np.max(abs(np.asarray(free["energies"]) - exact)) < 1e-9)
    checks["checks"]["fourth_order_free_haar_moments"] = bool(
        np.max(abs(np.asarray(free["moments"]) - [0, .25, .25, .0625, 0])) < 1e-9)
    checks["pass"] = checks["pass"] and all(checks["checks"].values())
    return checks


def run(output):
    start = time.monotonic()

    def emit(event, **data):
        print(json.dumps({"event": event, "elapsed_seconds": time.monotonic() - start, **data}), flush=True)

    emit("started", targets_run=0)
    report = {"schema_version": 1, "state": "running", "registered": False,
              "source_sha256": source_hashes(),
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "targets_run": 0,
              "targets": [{"id": row, "status": "unrun", "reason": "registration prerequisites incomplete"}
                          for row in baseline.target_ids()],
              "cells": [{"g": g, "eta": 1, "partition": "development", "status": "pending",
                         "rungs": [{"method": name, "rung": rung, "status": "pending"}
                                   for name, ladder, _ in methods() for rung in ladder]}
                        for g in baseline.G_VALUES],
              "limitations": ["Numerical agreement is not a certified error enclosure",
                               "Overlap uncertainty and temporal windows remain unresolved",
                               "No new independent semigroup, U1, pilot replication, or registration"]}
    baseline.write_report(output, report)
    try:
        report["calibration"] = calibration()
    except Exception as exc:
        report["calibration"] = {"pass": False, "reason": f"{type(exc).__name__}: {exc}"}
    if not report["calibration"]["pass"]:
        report["state"] = "instrument_failure"
        report["failure_reason"] = "calibration failed; all development rungs remain pending"
        baseline.write_report(output, report)
        emit("completed", state=report["state"], targets_run=0)
        return 1
    for cell in report["cells"]:
        cell["status"] = "running"
        previous, final, histories = {}, {}, {}
        solvers = {name: solve for name, _, solve in methods()}
        for slot in cell["rungs"]:
            method, rung = slot["method"], slot["rung"]
            slot["status"] = "running"
            baseline.write_report(output, report)
            emit("rung_started", g=cell["g"], method=method, rung=rung)
            rung_start = time.monotonic()
            try:
                record = solvers[method](cell["g"], 1, rung)
                validate_record(record)
                if method in previous:
                    record["adjacent_rung_difference"] = baseline.differences(previous[method], record)
                previous[method] = record
                final[method] = record
                histories.setdefault(method, []).append(baseline.compact(record))
                slot.update({"status": "completed", "result": baseline.compact(record)})
            except Exception as exc:
                slot.update({"status": "failure", "reason": f"{type(exc).__name__}: {exc}"})
            slot["elapsed_seconds"] = time.monotonic() - rung_start
            baseline.write_report(output, report)
            emit("rung_completed", g=cell["g"], method=method, rung=rung, status=slot["status"])
        cell["final"] = final
        if any(r["status"] == "failure" for r in cell["rungs"]):
            cell.update({"status": "failure", "reason": "one or more requested rungs failed"})
        else:
            second = baseline.differences(final["character"], final["angle_second"])
            fourth = baseline.differences(final["character"], final["angle_fourth"])
            cell.update({"status": "unresolved", "reason": "No certified enclosure or overlap/time budget",
                         "cross_method_difference_second": second,
                         "cross_method_difference_fourth": fourth,
                         "convergence_diagnostics": {
                             "angle_second": convergence_diagnostics(histories["angle_second"], order=2),
                             "angle_fourth": convergence_diagnostics(histories["angle_fourth"], order=4)},
                         "gap_solver_residual_scale_relative": (
                             (np.asarray(final["angle_fourth"]["solver_residual_first_four"])[1:]
                              + final["angle_fourth"]["solver_residual_first_four"][0])
                             / np.asarray(final["character"]["first_three_gaps"])).tolist(),
                         "numerical_goal_met": finite_goal(fourth) and all(
                             finite_goal(final[m]["adjacent_rung_difference"])
                             for m in ("character", "angle_fourth"))})
        baseline.write_report(output, report)
        emit("cell_completed", g=cell["g"], status=cell["status"], numerical_goal_met=cell.get("numerical_goal_met", False))
    report["accounting_pass"] = accounting(report)
    report["source_unchanged_during_run"] = source_hashes() == report["source_sha256"]
    passed = report["accounting_pass"] and report["source_unchanged_during_run"] and all(
        c["status"] != "failure" for c in report["cells"])
    report["state"] = "completed" if passed else "instrument_failure"
    baseline.write_report(output, report)
    emit("completed", state=report["state"], targets_run=0,
         numerical_goal_cells=sum(c.get("numerical_goal_met", False) for c in report["cells"]))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return run(parser.parse_args().output)


if __name__ == "__main__":
    raise SystemExit(main())
