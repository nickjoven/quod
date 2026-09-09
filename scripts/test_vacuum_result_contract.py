"""Draft result examples preserve provenance, identity, and unresolved states."""
import copy
import json
import unittest
from jsonschema.exceptions import ValidationError
import vacuum_result_contract as runner


class ResultContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((runner.DIRECTORY/'result-contract.json').read_text())

    def test_archive_replay(self):
        self.assertEqual(runner.build(),self.report)
        self.assertEqual(len(self.report['development_examples']),20)
        self.assertTrue(all(c['threshold']['status']=='resolved' for r in self.report['development_examples'] for c in r['channels']))

    def test_target_values_and_missing_rows_rejected(self):
        r=copy.deepcopy(self.report);r['targets'][0]['result']={}
        with self.assertRaises(ValidationError):runner.validate(r)
        r=copy.deepcopy(self.report);r['targets'].pop()
        with self.assertRaises(ValidationError):runner.validate(r)

    def test_threshold_and_payload_swap_rejected(self):
        r=copy.deepcopy(self.report);r['development_examples'][0]['channels'][0]['threshold']['leading_level']=2
        with self.assertRaisesRegex(ValueError,'threshold differs'):runner.validate(r)
        r=copy.deepcopy(self.report);r['development_examples'][0]['payload']['scalar']=r['development_examples'][1]['payload']['scalar']
        with self.assertRaisesRegex(ValueError,'cell identity'):runner.validate(r)

    def test_failure_and_unresolved_records_keep_reasons(self):
        for status in ('failure','unresolved'):
            r=copy.deepcopy(self.report);row=r['development_examples'][0]
            row.update(status=status,channels=[],payload=None,reason='injected unavailable numerical evidence')
            runner.validate(r)
            row['reason']=''
            with self.assertRaises(ValidationError):runner.validate(r)
        r=copy.deepcopy(self.report);r['development_examples'][0]['payload']=None
        with self.assertRaises(ValidationError):runner.validate(r)


if __name__=='__main__':unittest.main()
