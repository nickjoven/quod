"""Runner rejects invalid data before checkpointing and accounts for each request."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import vacuum_development as baseline
import vacuum_refinement as runner


class RunnerTests(unittest.TestCase):
    def test_nan_cannot_pass_goal(self):
        good = {"moment_absolute": [0.] * 5, "gap_relative": [0.] * 3}
        self.assertTrue(runner.finite_goal(good))
        for key in good:
            for invalid in (float("nan"), float("inf"), -1.):
                bad = copy.deepcopy(good)
                bad[key][-1] = invalid
                self.assertFalse(runner.finite_goal(bad))

    def test_invalid_solver_record_rejected(self):
        good = baseline.character(.5, 1, 20)
        runner.validate_record(good)
        for key in ("moments", "ground", "energies", "solver_residual_first_four"):
            bad = copy.deepcopy(good)
            bad[key][-1] = float("nan")
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                runner.validate_record(bad)
        bad = copy.deepcopy(good)
        bad["first_three_gaps"][0] += 1
        with self.assertRaisesRegex(ValueError, "gaps do not match"):
            runner.validate_record(bad)

    def test_failed_rung_is_recorded_and_all_later_requests_continue(self):
        fixture = baseline.character(.5, 1, 20)
        calls = []

        def solver(g, eta, rung):
            calls.append((g, eta, rung))
            result = copy.deepcopy(fixture)
            result["spacing"] = 1 / rung
            if len(calls) == 2:
                result["moments"][-1] = float("nan")
            return result

        plans = tuple((method, (600, 1200, 2400), solver)
                      for method in ("character", "angle_second", "angle_fourth"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(baseline, "G_VALUES", (.1, .5)), \
                    patch.object(runner, "methods", return_value=plans), \
                    patch.object(runner, "calibration", return_value={"pass": True}), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
                report = json.loads(output.read_text())
                self.assertTrue(runner.accounting(report))
            self.assertEqual(len(calls), 18)
            self.assertEqual([c["status"] for c in report["cells"]], ["failure", "unresolved"])
            failed = report["cells"][0]["rungs"][1]
            self.assertEqual(failed["status"], "failure")
            self.assertIn("nonfinite", failed["reason"])
            self.assertNotIn("result", failed)
            self.assertTrue(all(row["status"] == "unrun" for row in report["targets"]))

    def test_calibration_exception_has_explicit_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(runner, "calibration", side_effect=RuntimeError("injected")), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
            report = json.loads(output.read_text())
            self.assertEqual(report["state"], "instrument_failure")
            self.assertIn("injected", report["calibration"]["reason"])
            self.assertEqual(len(report["cells"]), 10)

    def test_archived_refinement_sources_and_accounting(self):
        report = json.loads((runner.ROOT / "research/vacuum-spectrum/refinement.json").read_text())
        self.assertEqual(report["state"], "completed")
        self.assertTrue(runner.accounting(report))
        self.assertTrue(report["source_unchanged_during_run"])
        for path, expected in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((runner.ROOT / path).read_bytes()).hexdigest(), expected)
        for cell in report["cells"]:
            self.assertEqual(cell["status"], "unresolved")
            self.assertTrue(cell["numerical_goal_met"])


if __name__ == "__main__":
    unittest.main()
