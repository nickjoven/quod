"""Reproduce semigroup report diagnostics and detect source/manifest drift."""
import hashlib
import json
import unittest

import numpy as np

import vacuum_development as baseline
import vacuum_semigroup as semigroup
import vacuum_semigroup_run as runner


class SemigroupArchiveTests(unittest.TestCase):
    def test_archived_sources_accounting_and_comparisons(self):
        raw = (baseline.ROOT / "research/vacuum-spectrum/semigroup.json").read_bytes()
        report = json.loads(raw)
        run_document = (baseline.ROOT / "research/vacuum-spectrum/SEMIGROUP-RUN.md").read_text()
        self.assertIn(hashlib.sha256(raw).hexdigest(), run_document)
        self.assertEqual(report["state"], "completed")
        self.assertEqual(report["source_sha256"], runner.source_hashes())
        self.assertTrue(report["source_unchanged_during_run"])
        self.assertTrue(report["accounting_pass"])
        self.assertTrue(runner.accounting(report))
        self.assertTrue(report["calibration"]["pass"])
        self.assertFalse(report["registered"])
        self.assertEqual(report["dimensionless_times"], list(semigroup.TAU))
        self.assertEqual(sum(len(c["rungs"]) for c in report["cells"]), 90)
        self.assertEqual(sum(len(r.get("evolutions", [])) for c in report["cells"] for r in c["rungs"]), 80)
        for cell in report["cells"]:
            self.assertEqual(cell["status"], "unresolved")
            self.assertIsNone(cell["usable_time_window"])
            self.assertEqual(cell["thresholds"], [None, None])
            chars = [r for r in cell["rungs"] if r["method"] == "character"]
            angles = [r for r in cell["rungs"] if r["method"] == "angle_fourth"]
            np.testing.assert_array_equal(cell["times"], np.asarray(semigroup.TAU)
                                          / chars[-1]["result"]["first_three_gaps"][0])
            covariance = cell["reference_covariance"]
            previous = None
            for rung in chars:
                self.assertEqual(rung["status"], "completed")
                corr = rung["result"]["correlations"]
                if previous is not None:
                    self.assertEqual(rung["adjacent_rung_difference"], semigroup.comparison(corr, previous, covariance))
                previous = corr
            reference = chars[-1]["result"]["correlations"]
            previous = None
            for rung in angles:
                self.assertEqual(rung["status"], "completed")
                for evolution in rung["evolutions"]:
                    self.assertEqual(evolution["status"], "completed")
                    corr = np.asarray(evolution["result"]["correlations"])
                    self.assertEqual(corr.shape, (len(semigroup.TAU), 2, 2))
                    self.assertTrue(np.isfinite(corr).all())
                    self.assertIsNone(evolution["result"]["integration_error_bound"])
                coarse, fine = [e["result"]["correlations"] for e in rung["evolutions"]]
                self.assertEqual(rung["tolerance_difference"], semigroup.comparison(coarse, fine, covariance))
                self.assertEqual(rung["character_difference"], semigroup.comparison(fine, reference, covariance))
                self.assertEqual(rung["low_state_difference"], semigroup.comparison(
                    fine, rung["result"]["low_state_correlations"], covariance))
                if previous is not None:
                    self.assertEqual(rung["adjacent_rung_difference"], semigroup.comparison(fine, previous, covariance))
                previous = fine


if __name__ == "__main__":
    unittest.main()
