"""Verify the lost-pilot disposition without claiming historical replication."""
import hashlib
import json
from pathlib import Path
import unittest

import vacuum_result_contract as contract


DIRECTORY = Path(__file__).resolve().parents[1] / 'research/vacuum-spectrum'


class PilotDispositionTests(unittest.TestCase):
    def test_provenance_and_scope(self):
        report = json.loads((DIRECTORY / 'pilot-disposition.json').read_text())
        self.assertEqual(report['original_pilot_replication'], 'unverifiable_source_lost')
        self.assertFalse(report['recovery_required'])
        self.assertFalse(report['historical_replication_verified'])
        self.assertFalse(report['registered'])
        self.assertFalse(report['target_execution_authorized'])
        self.assertEqual(report['remaining_prerequisites'], [
            'owner_assigned_identifiers', 'independent_review', 'future_registration'])
        required = {
            'PILOT-DISPOSITION.md', 'design-bundle/notes/ym_vacuum_gap_handoff.md',
            'design-bundle/notes/ym_vacuum_gap_registration_draft.md',
            'design-readiness.json', 'result-contract.json'}
        self.assertEqual(set(report['sha256']), required)
        for name, expected in report['sha256'].items():
            with self.subTest(source=name):
                self.assertEqual(hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest(), expected)

    def test_baseline_and_target_boundary(self):
        audit = json.loads((DIRECTORY / 'design-readiness.json').read_text())
        self.assertEqual(audit['external_prerequisites']['original_pilot_replication'], 'unresolved')
        self.assertEqual(len(audit['cells']), 20)
        self.assertTrue(all(c['status'] == 'development_qualified' for c in audit['cells']))
        result = json.loads((DIRECTORY / 'result-contract.json').read_text())
        contract.validate(result)
        self.assertEqual(len(result['development_examples']), 20)
        self.assertEqual(len(result['targets']), 42)
        self.assertTrue(all(t['status'] == 'unrun' and t['result'] is None
                            for t in result['targets']))


if __name__ == '__main__':
    unittest.main()
