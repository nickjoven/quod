"""Independent identities and report failure-path tests; no target solves."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import vacuum_development as study


class DevelopmentTests(unittest.TestCase):
    def test_archived_report_drift_and_coverage(self):
        report = json.loads((study.ROOT / "research/vacuum-spectrum/development.json").read_text())
        for path, expected in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((study.ROOT / path).read_bytes()).hexdigest(), expected)
        self.assertEqual([c["g"] for c in report["cells"]], list(study.G_VALUES))
        self.assertTrue(study.coverage(report["targets"]))
        self.assertTrue(all(r["status"] == "unrun" for r in report["targets"]))
        self.assertEqual(report["targets_run"], 0)
        for cell in report["cells"]:
            self.assertEqual(len(cell["rungs"]), len(study.CHARACTER_J) + len(study.ANGLE_INTERIORS))
            self.assertEqual(cell["status"], "unresolved")

    def test_calibration_and_named_mutants(self):
        result = study.calibration()
        self.assertTrue(result["pass"], result)
        self.assertEqual(len(result["mutants"]), 4)

    def test_projection_before_multiplication(self):
        edge = np.array([0., 0., 1.])
        exact = study.multiply_p(study.multiply_p(edge))[:3]
        wrongly_projected = study.multiply_p(study.multiply_p(edge)[:3])[:3]
        self.assertEqual(exact[-1], .5)
        self.assertEqual(wrongly_projected[-1], .25)

    def test_free_spectral_selection_and_sum_rule(self):
        record = study.character(.7, 0, 20)
        weights = np.array(record["weights"])
        np.testing.assert_allclose(weights[:2], [[.25, 0], [0, .0625]], atol=1e-14)
        np.testing.assert_allclose(weights.sum(axis=0), [.25, .0625], atol=1e-14)

    def test_interacting_discretizations(self):
        basis = study.character(.5, 1, 40)
        mesh = study.angle(.5, 1, 1200)
        diff = study.differences(basis, mesh)
        self.assertLess(max(diff["gap_relative"]), 1e-4)
        self.assertLess(max(diff["moment_absolute"]), 1e-5)
        self.assertLess(basis["finite_basis_sum_rule_defect"], 1e-12)
        omitted = np.array(mesh["unrepresented_covariance"])
        self.assertGreaterEqual(np.linalg.eigvalsh(omitted).min(), -1e-12)

    def test_duplicate_row_rejected(self):
        rows = [{"id": r} for r in study.target_ids()]
        rows[-1] = rows[0]
        self.assertFalse(study.coverage(rows))

    def test_failure_counted_and_later_cells_continue(self):
        real_character = study.character

        def injected(g, eta, j):
            if g == .1:
                raise RuntimeError("injected solver failure")
            return real_character(g, eta, j)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch("sys.argv", ["study", "--output", str(output)]), \
                    patch.object(study, "G_VALUES", (.1, .5)), \
                    patch.object(study, "CHARACTER_J", (20, 40)), \
                    patch.object(study, "ANGLE_INTERIORS", (600, 1200)), \
                    patch.object(study, "calibration", return_value={"pass": True}), \
                    patch.object(study, "character", side_effect=injected), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(study.main(), 1)
            report = json.loads(output.read_text())
            self.assertEqual([c["status"] for c in report["cells"]], ["failure", "unresolved"])
            self.assertIn("injected solver failure", report["cells"][0]["reason"])
            self.assertEqual(len(report["targets"]), 42)
            self.assertEqual(report["targets_run"], 0)
            self.assertTrue(all(r["status"] == "unrun" for r in report["targets"]))


if __name__ == "__main__":
    unittest.main()
