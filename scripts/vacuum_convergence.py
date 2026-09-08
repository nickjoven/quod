#!/usr/bin/env python3
"""Audit existing development rungs; never execute a Hamiltonian or target cell."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from vacuum_development import G_VALUES, GAP_GOAL, MOMENT_GOAL


def sequence_diagnostics(spacings, values, order=2.0):
    """Signed Richardson estimates and observed orders for actual mesh spacings.

    An estimate is not an enclosure. Observed orders are absent for sign
    reversals, zero differences, or roots outside the diagnostic range.
    """
    h = np.asarray(spacings, dtype=float)
    y = np.asarray(values, dtype=float)
    if len(h) < 3 or y.shape != h.shape or not np.all(np.isfinite(y)):
        raise ValueError("need at least three finite scalar rung values")
    if not np.all(np.isfinite(h)) or not np.all(h > 0) or not np.all(np.diff(h) < 0):
        raise ValueError("spacings must be finite, positive and strictly decreasing")
    differences = y[:-1] - y[1:]
    corrections = (y[1:] - y[:-1]) / ((h[:-1] / h[1:])**order - 1)
    extrapolated = y[1:] + corrections
    observed = []
    for i in range(len(h) - 2):
        d0, d1 = differences[i:i + 2]
        p = None
        if d0 * d1 > 0:
            ratio = d0 / d1
            a, b = h[i] / h[i + 2], h[i + 1] / h[i + 2]
            def equation(p):
                return (a**p - b**p) / (b**p - 1) - ratio
            try:
                p = float(brentq(equation, .1, 8))
            except ValueError:
                pass
        observed.append(p)
    return {"signed_adjacent_differences": differences.tolist(),
            "signed_fine_grid_corrections": corrections.tolist(),
            "extrapolated_values": extrapolated.tolist(),
            "observed_orders": observed,
            "extrapolate_adjacent_differences": np.diff(extrapolated).tolist()}


def convergence_diagnostics(records, order=2.0):
    """Return scalar diagnostics for moments/gaps using each record's spacing.

    Records must be ordered coarse to fine, with at least three rungs.
    This function does not decide acceptance or infer certified precision.
    """
    return {key: [sequence_diagnostics(
        [r["spacing"] for r in records], [r[key][k] for r in records], order)
        for k in range(count)]
        for key, count in (("moments", 5), ("first_three_gaps", 3))}


def audit(report):
    cells = report["cells"]
    if report.get("targets_run") != 0 or len(cells) != len(G_VALUES):
        raise ValueError("expected untouched targets and exactly ten development cells")
    if sorted(c["g"] for c in cells) != sorted(G_VALUES) or any(c["eta"] != 1 for c in cells):
        raise ValueError("unexpected development cell manifest")
    rows = []
    for cell in cells:
        rungs = [r for r in cell["rungs"] if r["method"] == "angle_dirichlet_second_order"]
        h = [r["spacing"] for r in rungs]
        reference = cell["final"]["character"]
        quantities = {}
        for key, count, relative, goal in (("moments", 5, False, MOMENT_GOAL),
                                          ("first_three_gaps", 3, True, GAP_GOAL)):
            entries = []
            for k in range(count):
                values = [r[key][k] for r in rungs]
                diag = sequence_diagnostics(h, values)
                ref = reference[key][k]
                scale = abs(ref) if relative else 1.0
                error = abs(diag["extrapolated_values"][-1] - ref) / scale
                diag.update({"character_reference": ref,
                             "finest_extrapolate_cross_method_difference": error,
                             "difference_units": "relative" if relative else "absolute",
                             "agreement_within_goal": error <= goal})
                if relative:
                    residual = rungs[-1]["solver_residual_first_four"]
                    diag["finest_gap_residual_scale_relative"] = (residual[0] + residual[k + 1]) / scale
                entries.append(diag)
            quantities[key] = entries
        rows.append({"g": cell["g"], "eta": 1, "quantities": quantities})
    return {"state": "development_diagnostics_only", "targets_run": 0,
            "limitations": ["Richardson corrections and residual scales are not rigorous error bounds",
                            "Observed order can be noise dominated when differences are small",
                            "Agreement does not resolve overlap or temporal channel coverage"],
            "cells": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("research/vacuum-spectrum/development.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    result = audit(json.loads(raw))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    result["audit_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"event": "completed", "development_cells": len(result["cells"]), "targets_run": 0}))


if __name__ == "__main__":
    main()
