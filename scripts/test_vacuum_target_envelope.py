"""Frozen unselected target inventory and unconditional draft denial gate."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

import vacuum_target_envelope as target


class TargetEnvelopeTests(unittest.TestCase):
    def test_saved_envelope_and_full_request_counts(self):
        value=json.loads(target.OUTPUT.read_text())
        self.assertTrue(target.validate(value))
        self.assertEqual(value,target.draft())
        for key,count in [('scalar',378),('certificates',210),('temporal',336)]:
            self.assertEqual(sum(len(r['requests'][key]) for r in value['rows']),count)
        self.assertTrue(all(not r['selected'] and r['result'] is None for r in value['rows']))

    def test_inventory_precision_results_and_authority_mutations_rejected(self):
        mutations=[lambda r:r['rows'].pop(),
                   lambda r:r['rows'].__setitem__(1,deepcopy(r['rows'][0])),
                   lambda r:r['rows'][0]['requests']['scalar'].pop(),
                   lambda r:r['rows'][0]['requests']['temporal'][0].update(atol=1e-2),
                   lambda r:r['rows'][0].update(result={'invented':True}),
                   lambda r:r.update(selected_target_ids=['synthetic-unapproved-id']),
                   lambda r:r.update(target_execution_authorized=True),
                   lambda r:r.update(contract_sha256='0'*64)]
        for mutate in mutations:
            value=target.draft(); mutate(value)
            with self.assertRaises(Exception):target.validate(value)

    def test_valid_draft_never_authorizes_execution(self):
        with patch.object(target.contract.development,'run',side_effect=AssertionError('execution reached')):
            with self.assertRaisesRegex(PermissionError,'disabled'):
                target.require_execution_authority(target.draft())


if __name__=='__main__':
    unittest.main()
