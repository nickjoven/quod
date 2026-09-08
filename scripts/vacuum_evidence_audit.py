"""Read-only audit of refinement provenance and scalar agreement, not certification."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import vacuum_development as baseline
import vacuum_refinement as refinement


def audit(report):
    if report["source_sha256"] != refinement.source_hashes():
        raise ValueError("archived solver source drift")
    if report["state"] != "completed" or not refinement.accounting(report):
        raise ValueError("incomplete refinement accounting")
    if report["registered"] is not False:
        raise ValueError("expected unregistered development evidence")
    cells = []
    for cell in report["cells"]:
        if any(r["status"] != "completed" for r in cell["rungs"]):
            raise ValueError("failed solve in completed evidence")
        final = cell["final"]
        for record in final.values():
            refinement.validate_record(record)
        # Recompute differences from observables rather than trusting success flags.
        cross = baseline.differences(final["character"], final["angle_fourth"])
        adjacent = {}
        for method in ("character", "angle_fourth"):
            rungs = [r["result"] for r in cell["rungs"] if r["method"] == method]
            for key in ("moments", "first_three_gaps"):
                if rungs[-1][key] != final[method][key]:
                    raise ValueError("final observables differ from last rung")
            adjacent[method] = baseline.differences(rungs[-2], rungs[-1])
        passed = refinement.finite_goal(cross) and all(
            refinement.finite_goal(d) for d in adjacent.values())
        if passed != cell["numerical_goal_met"]:
            raise ValueError("scalar agreement flag differs from recomputation")
        angle = final["angle_fourth"]
        residual = np.asarray(angle["solver_residual_first_four"])
        gaps = np.asarray(final["character"]["first_three_gaps"])
        cells.append({
            "g": cell["g"], "eta": cell["eta"], "scalar_agreement": passed,
            "cross_method_difference": cross, "adjacent_rung_difference": adjacent,
            "finite_matrix_gap_residual_scale_relative": ((residual[0] + residual[1:]) / gaps).tolist(),
            "angle_unrepresented_covariance": angle["unrepresented_covariance"],
            "angle_mesh_error_bound": angle["mesh_error_bound"],
            "angle_quadrature_error_bound": angle["quadrature_error_bound"],
            "archived_thresholds": angle["thresholds"],
            "channel_status": "unresolved",
        })
    return {"schema_version": 1, "state": "audited", "registered": False,
            "targets_run": 0, "completed_solves": sum(len(c["rungs"]) for c in report["cells"]),
            "source_sha256": report["source_sha256"], "cells": cells,
            "limitations": [
                "Residual scales are finite-matrix diagnostics, not continuum bounds",
                "Unrepresented covariance is not an overlap uncertainty bound",
                "No validated combined error budget or independent angle time-window evidence",
                "This audit does not verify ket artifacts or provide a sieve verdict"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = baseline.ROOT / "research/vacuum-spectrum/refinement.json"
    if args.output.resolve() == source.resolve():
        parser.error("output must not overwrite the archived refinement")
    raw = source.read_bytes()
    result = audit(json.loads(raw))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    result["audit_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    baseline.write_report(args.output, result)
    print(json.dumps({"state": result["state"], "completed_solves": result["completed_solves"],
                      "scalar_agreement_cells": sum(c["scalar_agreement"] for c in result["cells"]),
                      "unresolved_cells": len(result["cells"])}))


if __name__ == "__main__":
    main()
