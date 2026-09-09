"""Read-only interval assessment of sampled effective-gap windows."""
import argparse
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import vacuum_certificate_run as certificates
import vacuum_development as baseline

GAP_GOAL = F(1, 10**6)
SOURCES = (*certificates.SOURCES, "scripts/vacuum_time_windows.py")


def numeric(value):
    """Decode a subtree containing rational numbers only."""
    if isinstance(value, str):
        return F(value)
    if isinstance(value, list):
        return [numeric(v) for v in value]
    if isinstance(value, dict):
        return {k: numeric(v) for k, v in value.items()}
    return value


def log_point(x, precision=70):
    x = F(x)
    if x <= 0 or precision < 10:
        raise ValueError("positive logarithm input and precision >=10 required")
    if x == 1:
        return F(0), F(0)
    with localcontext() as ctx:
        ctx.prec = precision
        ctx.rounding = ROUND_FLOOR
        low = Decimal(x.numerator) / Decimal(x.denominator)
        ctx.rounding = ROUND_CEILING
        high = Decimal(x.numerator) / Decimal(x.denominator)
        return F(low.ln().next_minus()), F(high.ln().next_plus())


def slope_interval(left, right, duration):
    if (duration <= 0 or left[0] <= 0 or right[0] <= 0
            or left[1] < left[0] or right[1] < right[0]):
        raise ValueError("positive correlation intervals and duration required")
    return (log_point(left[0] / right[1])[0] / duration,
            log_point(left[1] / right[0])[1] / duration)


def assess_pair(left, right, observed_left, observed_right, duration, gap, nonzero_overlap):
    """Separate spectral-mixture bias and numerical slope uncertainty.

    A pair qualifies only if their conservative sum is <=1e-6 of the first
    gap's lower bound and its observable has a certified nonzero first overlap.
    """
    if gap[0] <= 0 or gap[1] < gap[0]:
        raise ValueError("isolated positive gap required")
    observed_left, observed_right = F(observed_left), F(observed_right)
    try:
        model = slope_interval(left, right, duration)
        observed = slope_interval((observed_left, observed_left), (observed_right, observed_right), duration)
    except ValueError as exc:
        return {"status": "unresolved", "reason": str(exc), "qualifies": False}
    mixture = max(F(0), model[1] - gap[0]) / gap[0]
    numerical = max(abs(x - y) for x in model for y in observed) / gap[0]
    total = mixture + numerical
    qualified = bool(nonzero_overlap and total <= GAP_GOAL)
    return {"status": "qualified_development_pair" if qualified else "unresolved",
            "qualifies": qualified, "nonzero_first_overlap": nonzero_overlap,
            "model_slope_interval": model, "observed_slope_interval": observed,
            "relative_mixture_bias_upper": mixture,
            "relative_numerical_slope_error_upper": numerical,
            "relative_combined_error_upper": total,
            "reason": "development precision criterion met" if qualified else (
                "first overlap not certified nonzero" if not nonzero_overlap else
                "mixture plus numerical error exceeds gap goal")}


def assess_cell(certificate_cell, semigroup_cell):
    final = certificate_cell["rungs"][-1]["result"]
    correlations = numeric(final["correlations"])
    gap = numeric(final["first_three_gap_intervals"])[0]
    if correlations is None or final["first_gap_overlap_certified"] is None:
        return {"g": certificate_cell["g"], "status": "unresolved", "reason": "correlation or overlap certificate unavailable",
                "rungs": []}
    times = [F(t) for t in certificate_cell["times"]]
    if times != [F(float(t)) for t in semigroup_cell["times"]]:
        raise ValueError("certificate and angle clocks differ")
    rungs = []
    for rung in semigroup_cell["rungs"]:
        if rung["method"] != "angle_fourth":
            continue
        observed = rung["evolutions"][-1]["result"]["correlations"]
        if len(observed) != len(times):
            raise ValueError("incomplete angle time samples")
        pairs = []
        for i in range(len(times) - 1):
            results = [assess_pair(correlations[i]["correlation"][a][a], correlations[i + 1]["correlation"][a][a],
                                   observed[i][a][a], observed[i + 1][a][a], times[i + 1] - times[i], gap,
                                   final["first_gap_overlap_certified"][a]) for a in range(2)]
            pairs.append({"sample_indices": [i, i + 1], "times": times[i:i + 2], "observables": results})
        rungs.append({"interiors": rung["rung"], "pairs": pairs,
                      "qualified_pairs_by_observable": [[p["sample_indices"] for p in pairs if p["observables"][a]["qualifies"]]
                                                        for a in range(2)]})
    return {"g": certificate_cell["g"], "status": "unresolved", "rungs": rungs,
            "registered_window": None}


def source_hashes():
    return {p: hashlib.sha256((baseline.ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def analyze():
    paths = [baseline.ROOT / "research/vacuum-spectrum" / name for name in ("certificates.json", "semigroup.json")]
    inputs = [p.read_bytes() for p in paths]
    cert, semigroup = [json.loads(raw) for raw in inputs]
    if cert["state"] != "completed" or not certificates.accounting(cert):
        raise ValueError("incomplete certificate evidence")
    for report in (cert, semigroup):
        if any(hashlib.sha256((baseline.ROOT / p).read_bytes()).hexdigest() != h for p, h in report["source_sha256"].items()):
            raise ValueError("source evidence drift")
    if cert["input_sha256"] != hashlib.sha256(inputs[1]).hexdigest():
        raise ValueError("semigroup evidence differs from certified input")
    if [c["g"] for c in cert["cells"]] != [c["g"] for c in semigroup["cells"]]:
        raise ValueError("cell manifest mismatch")
    return {"schema_version": 1, "state": "completed", "registered": False, "targets_run": 0,
            "targets": cert["targets"], "source_sha256": source_hashes(),
            "input_sha256": {p.name: hashlib.sha256(raw).hexdigest() for p, raw in zip(paths, inputs)},
            "gap_goal": GAP_GOAL,
            "criterion": "certified first overlap; mixture bias plus numerical slope error <=1e-6 of first gap lower bound",
            "scope": "adjacent sampled development pairs; no interpolation, target or registration decision",
            "cells": [assess_cell(c, s) for c, s in zip(cert["cells"], semigroup["cells"])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.name in ("certificates.json", "semigroup.json", "refinement.json", "development.json", "preflight.json",
                            "evidence-audit.json", "refinement-audit.json"):
        parser.error("output must not overwrite earlier evidence")
    report = analyze()
    baseline.write_report(args.output, certificates.encode(report))
    print(json.dumps({"state": "completed", "finest_pairs": [
        {"g": c["g"], "qualified": c["rungs"][-1]["qualified_pairs_by_observable"]} for c in report["cells"]]}))


if __name__ == "__main__":
    main()
