#!/usr/bin/env python3
"""Development-only SU(2) convergence study. No target execution interface."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.linalg import eigh_tridiagonal

from vacuum_preflight import target_ids

ROOT = Path(__file__).resolve().parents[1]
G_VALUES = (0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 1.00, 1.50, 2.00, 3.00)
CHARACTER_J = (20, 40, 80, 160, 320)
ANGLE_INTERIORS = (600, 1200, 2400, 4800)
MOMENT_GOAL = GAP_GOAL = 1e-6


def multiply_p(v):
    """Infinite character multiplication with one new coefficient of padding."""
    out = np.zeros(len(v) + 1)
    out[1:] += v / 2
    out[:len(v) - 1] += v[1:] / 2
    return out


def observable_data(e, vectors, applied, exact_gram, center=True):
    ground = vectors[:, 0]
    means = ground @ applied
    centered = applied - np.outer(ground, means) if center else applied.copy()
    amplitudes = vectors.T @ centered
    covariance = exact_gram - np.outer(means, means)
    spectral_covariance = amplitudes[1:].T @ amplitudes[1:]
    return {
        "E0": float(e[0]), "first_three_gaps": (e[1:4] - e[0]).tolist(),
        "moments": [float(means[0]), float(means[1]), float(covariance[0, 0]),
                    float(covariance[1, 1]), float(covariance[0, 1])],
        "ground": ground.tolist(), "energies": e.tolist(),
        "weights": (amplitudes[1:] ** 2).tolist(),
        "cross_weights": (amplitudes[1:, 0] * amplitudes[1:, 1]).tolist(),
        "vacuum_amplitudes": amplitudes[0].tolist(),
        "covariance": covariance.tolist(),
        "unrepresented_covariance": (covariance - spectral_covariance).tolist(),
        "thresholds": [None, None],
        "threshold_status": "unresolved: no overlap error bounds or temporal windows",
    }


def residuals(d, off, e, v):
    hv = d[:, None] * v
    hv[:-1] += off[:, None] * v[1:]
    hv[1:] += off[:, None] * v[:-1]
    return np.linalg.norm(hv - v * e, axis=0)


def character(g, eta, j, shift=0.0, center=True):
    n = np.arange(2 * j + 1, dtype=float)
    d = g * g * n * (n + 2) + shift
    off = np.full(len(n) - 1, -eta / (g * g))
    e, v = eigh_tridiagonal(d, off)
    # Canonicalize only the ground sign; cross weights are eigenvector-sign invariant.
    if v[np.argmax(abs(v[:, 0])), 0] < 0:
        v[:, 0] *= -1
    ground = v[:, 0]
    p = multiply_p(ground)
    p2 = multiply_p(p)
    padded = np.column_stack((np.pad(p, (0, 1)), p2))
    record = observable_data(e, v, padded[:len(n)], padded.T @ padded, center)
    record.update({"method": "character", "J": j,
                   "solver_residual_first_four": residuals(d, off, e[:4], v[:, :4]).tolist(),
                   "outside_basis_residual_first_four": (abs(off[-1] * v[-1, :4])).tolist(),
                   "observable_projection_tail_gram": (padded[len(n):].T @ padded[len(n):]).tolist(),
                   "finite_basis_sum_rule_defect": float(np.max(abs(
                       np.array(record["unrepresented_covariance"])
                       - padded[len(n):].T @ padded[len(n):])))})
    return record


def angle(g, eta, interiors, wrong_haar=False):
    h = np.pi / (interiors + 1)
    x = np.arange(1, interiors + 1) * h
    d = np.full(interiors, 2 * g * g / h**2 - g * g) - 2 * eta / g**2 * np.cos(x)
    off = np.full(interiors - 1, -g * g / h**2)
    e, v = eigh_tridiagonal(d, off, select="i", select_range=(0, 3))
    if v[np.argmax(abs(v[:, 0])), 0] < 0:
        v[:, 0] *= -1
    obs = np.column_stack((np.cos(x), np.cos(x)**2))
    applied = v[:, :1] * obs
    record = observable_data(e, v, applied, applied.T @ applied)
    if wrong_haar:
        # Actual measure bug: reconstruct psi, then normalize with flat dx.
        wrong_density = (v[:, 0] / np.sin(x))**2
        record["moments"][1] = float(wrong_density @ obs[:, 1] / sum(wrong_density))
    record.update({"method": "angle_dirichlet_second_order", "interiors": interiors,
                   "spacing": float(h),
                   "solver_residual_first_four": residuals(d, off, e, v).tolist(),
                   "omitted_spectrum": "all states above index 3; unrepresented covariance retained",
                   "quadrature_error_bound": None,
                   "mesh_error_bound": None})
    return record


def differences(a, b):
    return {"moment_absolute": abs(np.array(a["moments"]) - b["moments"]).tolist(),
            "gap_relative": (abs(np.array(a["first_three_gaps"]) - b["first_three_gaps"])
                             / np.array(b["first_three_gaps"])).tolist()}


def mesh_estimate(coarse, fine):
    """Leading h^2 Richardson estimate only; not an error enclosure."""
    divisor = (coarse["spacing"] / fine["spacing"])**2 - 1
    return {key: (np.array(value) / divisor).tolist()
            for key, value in differences(coarse, fine).items()}


def within_goal(diff):
    return max(diff["moment_absolute"]) <= MOMENT_GOAL and max(diff["gap_relative"]) <= GAP_GOAL


def compact(record):
    return {k: v for k, v in record.items()
            if k not in ("ground", "energies", "weights", "cross_weights")}


def coverage(rows):
    return len(rows) == len(target_ids()) and {r["id"] for r in rows} == set(target_ids())


def calibration():
    free = character(0.5, 0, 20)
    mesh = angle(0.5, 0, 600)
    expected = np.array([3, 8, 15]) * 0.5**2
    h = mesh["spacing"]
    discrete = 4 * 0.5**2 / h**2 * (
        np.sin(np.arange(2, 5) * h / 2)**2 - np.sin(h / 2)**2)
    baseline = character(0.5, 1, 20)
    shifted = character(0.5, 1, 20, shift=7)
    uncentered = character(0.5, 1, 20, center=False)
    haar_bug = angle(0.5, 0, 600, wrong_haar=True)
    rows = [{"id": row, "status": "unrun"} for row in target_ids()]
    tol = 1e-9  # Floating-point calibration tolerance, not a physical threshold.
    checks = {
        "free_character_gaps": bool(np.max(abs(np.array(free["first_three_gaps"]) - expected)) < tol),
        "free_character_moments": bool(np.max(abs(np.array(free["moments"]) - [0, .25, .25, .0625, 0])) < tol),
        "free_angle_discrete_gaps": bool(np.max(abs(np.array(mesh["first_three_gaps"]) - discrete)) < tol),
        "free_angle_haar": abs(mesh["moments"][1] - .25) < tol,
        "centering": bool(max(abs(np.array(baseline["vacuum_amplitudes"]))) < tol),
        "energy_shift": bool(np.max(abs(np.array(baseline["first_three_gaps"]) - shifted["first_three_gaps"])) < tol),
        "weight_sum": baseline["finite_basis_sum_rule_defect"] < tol,
        "coverage": coverage(rows),
    }
    mutants = {
        "wrong_haar": {"named_check": "free_angle_haar", "observed": haar_bug["moments"][1],
                       "rejected": abs(haar_bug["moments"][1] - .25) > tol},
        "omitted_centering": {"named_check": "centering", "observed": uncentered["vacuum_amplitudes"],
                              "rejected": bool(max(abs(np.array(uncentered["vacuum_amplitudes"]))) > tol)},
        "absolute_E1": {"named_check": "energy_shift", "observed": shifted["energies"][1] - baseline["energies"][1],
                        "rejected": abs(shifted["energies"][1] - baseline["energies"][1]) > tol},
        "missing_target": {"named_check": "coverage", "rejected": not coverage(rows[:-1])},
    }
    return {"checks": checks, "mutants": mutants,
            "pass": all(checks.values()) and all(m["rejected"] for m in mutants.values())}


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calibration-only", action="store_true")
    args = parser.parse_args()
    start = time.monotonic()

    def event(**data):
        print(json.dumps({"elapsed_seconds": time.monotonic() - start, **data}), flush=True)

    report = {"schema_version": 1, "state": "running", "registered": False,
              "targets_run": 0, "targets": [{"id": row, "status": "unrun",
              "reason": "registration prerequisites incomplete"} for row in target_ids()],
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                  for p in ("scripts/vacuum_development.py", "scripts/vacuum_preflight.py")},
              "calibration": calibration(), "cells": [
                  {"g": g, "eta": 1, "partition": "development", "status": "pending", "rungs": []}
                  for g in (() if args.calibration_only else G_VALUES)],
              "limitations": ["No rigorous mesh, quadrature, or truncation enclosures",
                               "No overlap uncertainty budget, resolved thresholds, or temporal windows",
                               "No independent angle semigroup or U(1) implementation",
                               "Pilot archive and lessons workflow unavailable; not verified replication"]}
    event(event="started", calibration_pass=report["calibration"]["pass"])
    if not report["calibration"]["pass"]:
        report["state"] = "instrument_failure"
        write_report(args.output, report)
        return 1
    write_report(args.output, report)
    for cell in report["cells"]:
        g = cell["g"]
        cell["status"] = "running"
        try:
            previous = {}
            final = {}
            for method, ladder, solve in (("character", CHARACTER_J, character),
                                           ("angle", ANGLE_INTERIORS, angle)):
                for rung in ladder:
                    record = solve(g, 1, rung)
                    if method in previous:
                        record["adjacent_rung_difference"] = differences(previous[method], record)
                        if method == "angle":
                            record["leading_h2_mesh_error_estimate"] = mesh_estimate(previous[method], record)
                    previous[method] = record
                    final[method] = record
                    cell["rungs"].append(compact(record))
                    write_report(args.output, report)
                    event(event="rung_completed", g=g, method=method, rung=rung)
            comparison = differences(final["character"], final["angle"])
            cell.update({"final": final, "cross_method_difference": comparison,
                         "numerical_goal_met": within_goal(comparison) and all(
                             within_goal(r["adjacent_rung_difference"]) for r in final.values()),
                         "status": "unresolved", "reason": "Error enclosures and overlap/time budgets not established"})
        except Exception as exc:
            cell.update({"status": "failure", "reason": f"{type(exc).__name__}: {exc}"})
        write_report(args.output, report)
        event(event="cell_completed", g=g, status=cell["status"])
    report["state"] = "completed" if not any(c["status"] == "failure" for c in report["cells"]) else "instrument_failure"
    write_report(args.output, report)
    event(event="completed", state=report["state"], cells=len(report["cells"]), targets_run=0)
    return 0 if report["state"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
