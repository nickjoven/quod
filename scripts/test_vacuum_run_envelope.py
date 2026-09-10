"""Development integration and rejection of targets before any solver call."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import vacuum_run_envelope as runner


def manifest(theories=('SU2',)):
    return {'schema_version':1,'purpose':'calibration','registered':False,
            'target_execution_authorized':False,'source_sha256':runner.source_hashes(),
            'tau':['0','1/2','1'],'tolerances':[[1e-10,1e-14]],
            'cells':[{'id':theory+'-free-calibration','theory':theory,'g':'1','eta':'0',
                      'cutoffs':[4,8],'grids':[32,64]} for theory in theories]}


class RunEnvelopeTests(unittest.TestCase):
    def test_whole_result_gate_rejects_post_aggregation_corruption(self):
        original=runner.process_cell
        def corrupted(spec,cell,manifest,emit):
            original(spec,cell,manifest,emit)
            cell['scalar_accuracy']={}
        with patch.object(runner,'process_cell',side_effect=corrupted):
            result=runner.run(manifest())
        self.assertEqual(result['state'],'instrument_failure')
        self.assertEqual(result['whole_result_replay']['status'],'invalid')
        self.assertEqual(result['cells'][0]['status'],'failure')
        self.assertIsNotNone(result['cells'][0]['stages']['scalar']['result']['final'])

    def test_corrupted_scalar_comparison_fails_without_losing_later_stages(self):
        original=runner.scalar.run
        def corrupted(*args,**kwargs):
            result=original(*args,**kwargs)
            result['result']['cross_representation_difference']={}
            return result
        with patch.object(runner.scalar,'run',side_effect=corrupted):
            result=runner.run(manifest())
        cell=result['cells'][0]
        self.assertEqual(cell['status'],'failure')
        self.assertEqual(cell['scalar_replay']['status'],'invalid')
        self.assertEqual(cell['stages']['temporal']['status'],'completed')
        self.assertIsNotNone(cell['stages']['scalar']['result']['final'])

    def test_corrupted_temporal_assessment_invalidates_cell_and_keeps_evidence(self):
        original=runner.temporal.run
        for missing_digest in (False,True):
            def corrupted(*args,**kwargs):
                result=original(*args,**kwargs)
                if missing_digest:
                    del result['result']['certificate_sha256']
                else:
                    result['result']['rungs'][-1]['evolutions'][-1]['angle_error_bounds']={}
                return result
            with patch.object(runner.temporal,'run',side_effect=corrupted):
                result=runner.run(manifest())
            cell=result['cells'][0]
            self.assertEqual(cell['status'],'failure')
            self.assertEqual(cell['temporal_replay']['status'],'invalid')
            self.assertEqual(cell['qualifying_common_sample_pairs'],[])
            self.assertIn('result',cell['stages']['temporal']['result']['rungs'][-1]['evolutions'][-1])

    def test_failed_or_exceptional_control_prevents_requested_cell_work(self):
        for effect in (lambda: {'pass':True,'checks':{'identity':False},'mutants_rejected':{'mutant':True}},
                       lambda: (_ for _ in ()).throw(RuntimeError('control failure'))):
            with patch.object(runner.design_nulls,'evaluate',side_effect=effect), patch.object(
                    runner.scalar,'run',side_effect=AssertionError('requested solver reached')) as solver:
                result=runner.run(manifest(('SU2','U1')))
            solver.assert_not_called()
            self.assertEqual(result['state'],'instrument_failure')
            self.assertEqual(result['control_preflight']['suites']['design_nulls']['status'],'failed')
            self.assertEqual(len(result['control_preflight']['suites']),4)
            self.assertTrue(result['accounting_verified'])
            self.assertTrue(all(c['status']=='failure' for c in result['cells']))

    def test_full_integration_and_checkpoint_snapshots(self):
        snapshots=[]
        result=runner.run(manifest(('SU2','U1')),snapshots.append)
        self.assertEqual(result['state'],'completed')
        self.assertEqual(result['control_preflight']['status'],'passed')
        self.assertEqual(len(result['cells']),2)
        self.assertEqual(len(result['targets']),42)
        self.assertTrue(all(t['status']=='unrun' for t in result['targets']))
        self.assertTrue(all(c['status']=='pending' for c in snapshots[0]['cells']))
        for cell in result['cells']:
            stages=cell['stages']
            self.assertEqual(len(stages['scalar']['result']['rungs']),4)
            self.assertEqual(len(stages['certificates']['rungs']),2)
            self.assertEqual(len(stages['temporal']['result']['rungs']),2)
            self.assertEqual([c['threshold']['leading_level'] for c in cell['adaptation']['channels']],[1,2])
            self.assertEqual(stages['certificates']['times'],stages['temporal']['result']['times'])
        self.assertFalse(result['target_execution_authorized'])
        self.assertTrue(result['accounting_verified'])

    def test_target_coordinates_rejected_before_solver(self):
        candidate=manifest()
        candidate['cells'][0]['g']='0.125'
        with patch.object(runner.scalar,'run',side_effect=AssertionError('target solver reached')):
            with self.assertRaises(PermissionError):
                runner.run(candidate)

    def test_source_drift_duplicate_and_false_registration_rejected(self):
        candidate=manifest()
        candidate['source_sha256'][next(iter(candidate['source_sha256']))]='0'*64
        with self.assertRaisesRegex(ValueError,'source'):
            runner.run(candidate)
        candidate=manifest()
        candidate['cells'].append(deepcopy(candidate['cells'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):
            runner.validate(candidate)
        from jsonschema.exceptions import ValidationError
        candidate=manifest()
        candidate['registered']=True
        with self.assertRaises(ValidationError):
            runner.validate(candidate)

    def test_failed_finest_certificate_preserves_later_cell(self):
        original=runner.certificates.calculate
        def injected(theory,g,eta,cutoff,times):
            if theory=='SU2' and cutoff==8:
                raise RuntimeError('injected finest failure')
            return original(theory,g,eta,cutoff,times)
        with patch.object(runner.certificates,'calculate',side_effect=injected):
            result=runner.run(manifest(('SU2','U1')))
        self.assertEqual(result['state'],'completed_with_failures')
        self.assertEqual(result['cells'][0]['status'],'failure')
        self.assertEqual(result['cells'][0]['stages']['certificates']['rungs'][0]['status'],'completed')
        self.assertEqual(result['cells'][1]['stages']['temporal']['status'],'completed')

    def test_retime_preserves_operator_and_changes_only_clock_evidence(self):
        record=runner.certificates.calculate('SU2','1','0',4,[0])
        changed=runner.retime(record,[0,0.125])
        self.assertTrue(runner.certificates.verify(changed))
        for key in ('enclosures','vector_bounds','overlaps','vacuum'):
            self.assertEqual(record['result'][key],changed['result'][key])
        self.assertEqual(record['times'],['0'])

    def test_unexpected_stage_exception_preserves_later_cells(self):
        original=runner.scalar.run
        def injected(theory,*args):
            if theory=='SU2':
                raise RuntimeError('unexpected stage failure')
            return original(theory,*args)
        with patch.object(runner.scalar,'run',side_effect=injected):
            result=runner.run(manifest(('SU2','U1')))
        self.assertEqual(result['cells'][0]['status'],'failure')
        self.assertEqual(result['cells'][1]['stages']['temporal']['status'],'completed')
        self.assertTrue(result['accounting_verified'])

    def test_retime_failure_retains_original_and_continues(self):
        original=runner.retime
        def injected(record,times):
            if record['cutoff']==4:
                raise RuntimeError('injected coarse retime failure')
            return original(record,times)
        with patch.object(runner,'retime',side_effect=injected):
            result=runner.run(manifest())
        stages=result['cells'][0]['stages']
        self.assertEqual(stages['certificates']['rungs'][0]['retime_status'],'failed')
        self.assertEqual(stages['certificates']['rungs'][0]['initial_record']['times'],['0'])
        self.assertEqual(stages['certificates']['rungs'][1]['retime_status'],'completed')
        self.assertEqual(stages['temporal']['status'],'completed')
        self.assertTrue(result['accounting_verified'])

    def test_final_drift_cannot_report_success(self):
        spec=manifest()
        with patch.object(runner,'source_hashes',side_effect=[spec['source_sha256'],{}]):
            result=runner.run(spec)
        self.assertEqual(result['state'],'instrument_failure')
        self.assertTrue(all(c['status']=='failure' for c in result['cells']))

    def test_checkpoint_failure_stops_before_solver(self):
        spec=manifest()
        with patch.object(runner.scalar,'run',side_effect=AssertionError('unexpected solver')):
            with self.assertRaises(runner.CheckpointFailure):
                runner.run(spec,lambda _: (_ for _ in ()).throw(OSError('disk full')))

    def test_scalar_agreement_cannot_replace_exact_accuracy(self):
        spec=manifest()
        spec['cells'][0]['cutoffs']=[8]
        spec['cells'][0]['grids']=[512]
        result=runner.run(spec)
        cell=result['cells'][0]
        self.assertTrue(cell['scalar_accuracy']['qualifies'])
        self.assertEqual(cell['status'],'development_qualified')
        stages=deepcopy(cell['stages'])
        for record in stages['scalar']['result']['final'].values():
            record['moments'][0]+=0.01
        self.assertFalse(runner.scalar_accuracy(stages,'SU2')['qualifies'])


if __name__=='__main__':
    unittest.main()
