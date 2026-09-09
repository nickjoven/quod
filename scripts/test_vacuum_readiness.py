"""Consolidated evidence replay and rejection of false readiness claims."""
import copy
import json
import unittest

from jsonschema.exceptions import ValidationError

import vacuum_readiness as runner


class ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs, cls.hashes = runner.load_inputs()

    def test_archive_replay(self):
        result = runner.audit(self.inputs, self.hashes)
        archive = json.loads((runner.DIRECTORY / 'readiness.json').read_text())
        self.assertEqual(result, archive)
        self.assertEqual(len(result['cells']), 20)
        self.assertTrue(all(c['status'] == 'development_qualified' for c in result['cells']))
        for cell in result['cells']:
            if cell['theory'] == 'U1':
                self.assertNotEqual(cell['full_gap_interval'], cell['observable_gap_interval'])
        self.assertFalse(result['target_execution_authorized'])

    def test_target_execution_rejected(self):
        reports = copy.deepcopy(self.inputs)
        reports['refinement.json']['targets'][0]['status'] = 'completed'
        with self.assertRaisesRegex(ValueError, 'target manifest'):
            runner.audit(reports, self.hashes)

    def test_source_and_input_drift_rejected(self):
        reports = copy.deepcopy(self.inputs)
        path = next(iter(reports['refinement.json']['source_sha256']))
        reports['refinement.json']['source_sha256'][path] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source drift'):
            runner.audit(reports, self.hashes)
        with self.assertRaisesRegex(ValueError, 'input hash'):
            runner.audit(self.inputs, {**self.hashes, 'refinement.json': '0' * 64})

    def test_missing_requests_rejected(self):
        reports = copy.deepcopy(self.inputs)
        reports['refinement.json']['cells'].pop()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            runner.audit(reports, self.hashes)

    def test_schema_rejects_authorization_and_false_external_completion(self):
        result = json.loads((runner.DIRECTORY / 'readiness.json').read_text())
        for key, value in [('registered', True), ('targets_run', 1), ('target_execution_authorized', True)]:
            with self.subTest(key=key), self.assertRaises(ValidationError):
                runner.validate_schema({**result, key: value})
        result['external_prerequisites']['independent_review'] = 'passed'
        with self.assertRaises(ValidationError):
            runner.validate_schema(result)


if __name__ == '__main__':
    unittest.main()
