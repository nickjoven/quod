"""Whole-result replay on development calibration and retained failures."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import vacuum_run_replay as replay
from test_vacuum_run_envelope import manifest


class RunReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidate=manifest(('SU2','U1'))
        for cell in candidate['cells']:
            cell.update(cutoffs=[8],grids=[512])
        cls.result=replay.runner.run(candidate)

    def test_replay_both_models_without_numerical_solver(self):
        with patch.object(replay.runner.scalar,'run',side_effect=AssertionError('scalar solver')), patch.object(
                replay.runner.temporal.evolution,'propagate',side_effect=AssertionError('propagation')):
            result=replay.verify(self.result)
        self.assertEqual(result['status'],'verified',result)
        self.assertEqual(result['cell_outcomes'],['development_qualified']*2)

    def test_changed_aggregate_accuracy_clock_and_inventory_rejected(self):
        mutations=[lambda r:r.update(state='completed_with_failures'),
                   lambda r:r['whole_result_replay'].update(cell_outcomes=[]),
                   lambda r:r['cells'][0].update(status='unresolved'),
                   lambda r:r['cells'][0].update(scalar_accuracy={}),
                   lambda r:r['cells'][0]['stages']['certificates'].update(times=['0','1']),
                   lambda r:r['cells'][0].update(qualifying_common_sample_pairs=[]),
                   lambda r:r['targets'].pop(),
                   lambda r:r['control_preflight']['suites']['design_nulls']['result']['checks'].update(fake=False)]
        for mutate in mutations:
            result=deepcopy(self.result); mutate(result)
            self.assertEqual(replay.verify(result)['status'],'invalid')

    def test_missing_control_and_malformed_schema_data_return_invalid(self):
        mutations=[lambda r:r['manifest'].update(target_execution_authorized=True),
                   lambda r:r['cells'][0]['stages']['scalar'].pop('result'),
                   lambda r:r['control_preflight']['suites']['design_nulls'].update(result='bad'),
                   lambda r:r['control_preflight']['suites']['design_nulls']['result']['checks'].pop('specified_tensor_eigenpairs')]
        for mutate in mutations:
            result=deepcopy(self.result); mutate(result)
            self.assertEqual(replay.verify(result)['status'],'invalid')

    def test_coarse_valid_result_remains_unresolved(self):
        candidate=manifest()
        candidate['cells'][0].update(g='0.1',eta='1',cutoffs=[4],grids=[32])
        result=replay.runner.run(candidate)
        checked=replay.verify(result)
        self.assertEqual(checked['status'],'verified',checked)
        self.assertEqual(checked['cell_outcomes'],['unresolved'])

    def test_failed_finest_certificate_retains_partial_result(self):
        original=replay.runner.certificates.calculate
        def failed(theory,g,eta,cutoff,times):
            if cutoff==8:
                raise RuntimeError('injected finest certificate failure')
            return original(theory,g,eta,cutoff,times)
        with patch.object(replay.runner.certificates,'calculate',side_effect=failed):
            result=replay.runner.run(manifest())
        checked=replay.verify(result)
        self.assertEqual(checked['status'],'verified',checked)
        self.assertEqual(checked['cell_outcomes'],['failure'])

    def test_failed_control_blocks_all_cells(self):
        with patch.object(replay.runner.design_nulls,'evaluate',side_effect=RuntimeError('injected control failure')):
            result=replay.runner.run(manifest())
        checked=replay.verify(result)
        self.assertEqual(checked['status'],'verified',checked)
        self.assertEqual(checked['run_state'],'instrument_failure')

    def test_corrupted_scalar_caught_by_runner_remains_explicit_failure(self):
        original=replay.runner.scalar.run
        def corrupted(*args,**kwargs):
            result=original(*args,**kwargs)
            result['result']['cross_representation_difference']={}
            return result
        with patch.object(replay.runner.scalar,'run',side_effect=corrupted):
            result=replay.runner.run(manifest())
        checked=replay.verify(result)
        self.assertEqual(checked['status'],'verified',checked)
        self.assertEqual(checked['cell_outcomes'],['failure'])


if __name__=='__main__':
    unittest.main()
