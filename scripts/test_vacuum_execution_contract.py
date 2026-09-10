"""Nonexecuting contract checks; no target selection or solver evaluations."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import vacuum_execution_contract as contract


class ExecutionContractTests(unittest.TestCase):
    def test_checked_in_draft_has_current_pins(self):
        import json
        self.assertTrue(contract.validate(json.loads(contract.OUTPUT.read_text())))

    def test_draft_replays_without_numerical_calls(self):
        with patch.object(contract.development,'run',side_effect=AssertionError('execution reached')):
            value=contract.draft()
            self.assertTrue(contract.validate(value))
        self.assertEqual(len(value['targets']),42)
        self.assertEqual(value['selected_target_ids'],[])

    def test_mutated_inventory_authorization_budget_and_environment_rejected(self):
        mutations=[lambda d:d['targets'].pop(),
                   lambda d:d['targets'].__setitem__(1,deepcopy(d['targets'][0])),
                   lambda d:d.update(target_execution_authorized=True),
                   lambda d:d.update(selected_target_ids=['synthetic-unapproved-id']),
                   lambda d:d['protocol'].update(moment_absolute_budget='1/1000'),
                   lambda d:d['environment']['packages'].update(numpy='0.0.0'),
                   lambda d:d['source_sha256'].pop(next(iter(d['source_sha256'])))]
        for mutate in mutations:
            value=contract.draft(); mutate(value)
            with self.subTest(mutation=mutate), self.assertRaises(Exception):
                contract.validate(value)

    def test_terminal_structure_keeps_partial_evidence_and_rejects_false_agreement(self):
        value={'id':'synthetic-structure-fixture','status':'failure','reason':'injected propagation failure',
               'assessment':{'channels':'retained fixture'},
               'stages':{name:{'status':'completed','result':{}} for name in ('scalar','certificates','temporal')}}
        value['stages']['temporal']={'status':'failed','reason':'injected failure','result':{'partial':'retained'}}
        self.assertTrue(contract.validate_terminal_structure(value))
        value['status']='instrument_agreement'
        with self.assertRaises(Exception):
            contract.validate_terminal_structure(value)
        value['status']='failure'; value['stages']['temporal']['reason']='  '
        with self.assertRaises(Exception):
            contract.validate_terminal_structure(value)


if __name__=='__main__':
    unittest.main()
