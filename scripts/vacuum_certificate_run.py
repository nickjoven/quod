"""Fixed-ladder rational certificates and end-to-end angle error bounds."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.linalg import eigh_tridiagonal

import vacuum_certified as certified
import vacuum_development as baseline
import vacuum_semigroup_run as semigroup_run

SOURCES = (*semigroup_run.SOURCES, "scripts/vacuum_certified.py", "scripts/vacuum_intervals.py",
           "scripts/vacuum_certificate_run.py")


def encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {key: encode(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(child) for child in value]
    return value


def source_hashes():
    return {p: hashlib.sha256((baseline.ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def angle_error_bounds(correlations, vacuum, angle_rungs):
    if correlations is None or vacuum is None:
        return None
    scales = [[certified.sqrt_interval(vacuum["covariance"][a][a][0]
                                      * vacuum["covariance"][b][b][0])[0]
               for b in range(2)] for a in range(2)]
    output = []
    for rung in angle_rungs:
        records = []
        approximations = rung["evolutions"][-1]["result"]["correlations"]
        if len(approximations) != len(correlations):
            raise ValueError("angle time sample count mismatch")
        for sample, approximation in zip(correlations, approximations):
            if len(approximation) != 2 or any(len(row) != 2 for row in approximation):
                raise ValueError("angle correlation shape mismatch")
            errors = [[max(abs(F(float(approximation[a][b])) - endpoint)
                           for endpoint in sample["correlation"][a][b]) for b in range(2)] for a in range(2)]
            normalized = [[errors[a][b] / scales[a][b] if scales[a][b] > 0 else None
                           for b in range(2)] for a in range(2)]
            records.append({"time": sample["time"], "absolute_error_upper": errors,
                            "initial_variance_normalized_error_upper": normalized})
        output.append({"interiors": rung["rung"], "samples": records})
    return output


def calculate(g, j, times):
    size = 2 * j + 1
    diagonal, hopping, _ = certified.parameters(g, 1, size)
    _, vectors = eigh_tridiagonal(np.array(diagonal, dtype=float), np.full(size - 1, float(hopping)),
                                 select="i", select_range=(0, 3))
    vectors = vectors.T
    enclosures = certified.eigenvalue_enclosures(g, 1, size)
    if not certified.verify_enclosures(g, 1, size, enclosures):
        raise ValueError("exact endpoint verification failed")
    bounds = [certified.eigenvector_bound(g, 1, vector, k, enclosures)
              for k, vector in enumerate(vectors)]
    overlaps = certified.overlap_intervals(vectors, bounds)
    vacuum = certified.vacuum_intervals(vectors[0], bounds[0])
    correlations = certified.correlation_intervals(enclosures, overlaps, vacuum, times)
    gaps = [(e["lower"] - enclosures[0]["upper"], e["upper"] - enclosures[0]["lower"])
            for e in enclosures[1:4]]
    moment_intervals = None if vacuum is None else [
        *vacuum["raw_moments"][:2], vacuum["covariance"][0][0],
        vacuum["covariance"][1][1], vacuum["covariance"][0][1]]
    gap_budget = all(low > 0 and (high - low) / (2 * low) <= F(1, 10**6) for low, high in gaps)
    moment_budget = moment_intervals is not None and all(
        (high - low) / 2 <= F(1, 10**6) for low, high in moment_intervals)
    return {"size": size, "enclosures": enclosures, "endpoint_verification": True,
            "candidate_vectors_hex": [[float(value).hex() for value in vector] for vector in vectors],
            "vector_bounds": bounds, "overlaps": overlaps, "vacuum": vacuum,
            "first_three_gap_intervals": gaps, "correlations": correlations,
            "scalar_budget_met": gap_budget and moment_budget,
            "first_gap_overlap_certified": None if overlaps is None else [
                entry["nonzero_certified"] for entry in overlaps[0]],
            "bound_status": "bounded" if correlations is not None else "unresolved"}


def verify_result(g, result, times):
    """Read-only exact replay from stored dyadic candidates and endpoints."""
    enclosures = [{key: F(value) if key in ("lower", "upper", "finite_lower", "tail_floor") else value
                   for key, value in row.items()} for row in result["enclosures"]]
    if not certified.verify_enclosures(g, 1, result["size"], enclosures):
        return False
    vectors = [[float.fromhex(value) for value in vector] for vector in result["candidate_vectors_hex"]]
    if len(vectors) != 4 or any(len(v) != result["size"] for v in vectors):
        return False
    bounds = [certified.eigenvector_bound(g, 1, vector, k, enclosures) for k, vector in enumerate(vectors)]
    overlaps = certified.overlap_intervals(vectors, bounds)
    vacuum = certified.vacuum_intervals(vectors[0], bounds[0])
    correlations = certified.correlation_intervals(enclosures, overlaps, vacuum, times)
    return all(result[key] == encode(value) for key, value in (
        ("vector_bounds", bounds), ("overlaps", overlaps), ("vacuum", vacuum), ("correlations", correlations)))


def accounting(report):
    return (report["targets_run"] == 0 and baseline.coverage(report["targets"])
            and all(t["status"] == "unrun" for t in report["targets"])
            and [c["g"] for c in report["cells"]] == list(baseline.G_VALUES)
            and all(c["eta"] == 1 and c["partition"] == "development"
                    and [r["J"] for r in c["rungs"]] == list(baseline.CHARACTER_J)
                    and all(r["status"] in ("completed", "failure") for r in c["rungs"])
                    for c in report["cells"]))


def run(output):
    began = time.monotonic()
    source = baseline.ROOT / "research/vacuum-spectrum/semigroup.json"
    raw = source.read_bytes()
    semigroup = json.loads(raw)
    if (semigroup["state"] != "completed" or not semigroup_run.accounting(semigroup)
            or any(hashlib.sha256((baseline.ROOT / path).read_bytes()).hexdigest() != expected
                   for path, expected in semigroup["source_sha256"].items())):
        raise ValueError("invalid or drifted source semigroup evidence")
    report = {"schema_version": 1, "state": "running", "registered": False,
              "targets_run": 0, "targets": semigroup["targets"], "source_sha256": source_hashes(),
              "input_sha256": hashlib.sha256(raw).hexdigest(), "input": str(source.relative_to(baseline.ROOT)),
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "arithmetic": "integer Sturm signs; Fraction residuals; dyadic square roots; outward Decimal exponential",
              "coordinate_convention": "exact decimal g and eta=1 in the infinite character operator",
              "time_convention": "stored semigroup binary64 times interpreted as exact dyadic rationals",
              "cells": [{"g": g, "eta": 1, "partition": "development", "status": "pending",
                         "rungs": [{"J": j, "status": "pending"} for j in baseline.CHARACTER_J]}
                        for g in baseline.G_VALUES],
              "limitations": ["Certificates concern the stated single-angle infinite character model, not Yang-Mills field theory",
                              "Python integer/Decimal correctness and the documented analytic tail/residual arguments are trusted",
                              "No Lean theorem registration or independent formal verification is claimed",
                              "Angle errors are bounded end-to-end at sampled times, not decomposed by numerical source",
                              "No channel window selection, target selection/execution, U1 or registration"]}

    def checkpoint(event, **fields):
        baseline.write_report(output, encode(report))
        print(json.dumps({"event": event, "elapsed_seconds": time.monotonic() - began, **fields}), flush=True)

    checkpoint("started")
    for cell, source_cell in zip(report["cells"], semigroup["cells"]):
        cell["status"] = "running"
        times = [F(float(value)) for value in source_cell["times"]]
        cell["times"] = times
        for rung in cell["rungs"]:
            rung["status"] = "running"
            checkpoint("rung_started", g=cell["g"], J=rung["J"])
            start = time.monotonic()
            try:
                result = calculate(cell["g"], rung["J"], times)
                json.dumps(encode(result), allow_nan=False)
                rung.update(status="completed", result=result)
            except Exception as exc:
                rung.update(status="failure", reason=f"{type(exc).__name__}: {exc}")
            rung["elapsed_seconds"] = time.monotonic() - start
            checkpoint("rung_completed", g=cell["g"], J=rung["J"], status=rung["status"])
        if cell["rungs"][-1]["status"] == "completed":
            final = cell["rungs"][-1]["result"]
            try:
                cell["angle_error_bounds"] = angle_error_bounds(final["correlations"], final["vacuum"],
                    [r for r in source_cell["rungs"] if r["method"] == "angle_fourth"])
            except Exception as exc:
                cell["analysis_failure"] = f"{type(exc).__name__}: {exc}"
        cell["status"] = "failure" if "analysis_failure" in cell or any(
            r["status"] == "failure" for r in cell["rungs"]) else "unresolved"
        cell["usable_time_window"] = None
        checkpoint("cell_completed", g=cell["g"], status=cell["status"])
    report["accounting_pass"] = accounting(report)
    report["source_unchanged_during_run"] = source_hashes() == report["source_sha256"]
    report["state"] = "completed" if report["accounting_pass"] and report["source_unchanged_during_run"] and all(
        c["status"] != "failure" for c in report["cells"]) else "instrument_failure"
    report["elapsed_seconds"] = time.monotonic() - began
    checkpoint("completed", state=report["state"])
    return 0 if report["state"] == "completed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.name in ("semigroup.json", "refinement.json", "development.json", "preflight.json",
                            "evidence-audit.json", "refinement-audit.json"):
        parser.error("output must not replace earlier evidence")
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
