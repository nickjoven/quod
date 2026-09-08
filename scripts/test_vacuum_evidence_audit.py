"""Adversarial checks of the archived-evidence audit."""
import copy
import json
import unittest

from vacuum_development import ROOT
from vacuum_evidence_audit import audit


class EvidenceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / "research/vacuum-spectrum/refinement.json").read_text())

    def test_archive(self):
        result = audit(self.report)
        self.assertEqual(result["completed_solves"], 130)
        self.assertEqual(sum(c["scalar_agreement"] for c in result["cells"]), 10)
        self.assertTrue(all(c["channel_status"] == "unresolved" for c in result["cells"]))

    def test_source_drift(self):
        report = copy.deepcopy(self.report)
        report["source_sha256"]["scripts/vacuum_refinement.py"] = "changed"
        with self.assertRaisesRegex(ValueError, "source drift"):
            audit(report)

    def test_false_agreement(self):
        report = copy.deepcopy(self.report)
        report["cells"][0]["rungs"][-2]["result"]["moments"][0] += .01
        with self.assertRaisesRegex(ValueError, "flag differs"):
            audit(report)

    def test_target_execution(self):
        report = copy.deepcopy(self.report)
        report["targets"][0]["status"] = "completed"
        with self.assertRaisesRegex(ValueError, "accounting"):
            audit(report)


if __name__ == "__main__":
    unittest.main()
