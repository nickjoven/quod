"""Development-only scalar calibration and exact request/failure retention."""
import unittest
from unittest.mock import patch

import vacuum_parameterized_scalar as scalar


class ParameterizedScalarTests(unittest.TestCase):
    def test_finite_inputs_cannot_hide_nonfinite_computed_defects(self):
        record={'weights':[[1e200,1e200]],'cross_weights':[1e200],
                'covariance':[[1e200,1e200],[1e200,1e200]],
                'unrepresented_covariance':[[0,0],[0,0]],
                'moments':[0,1e200,1e200,1e200,1e200]}
        with scalar.np.errstate(over='ignore',invalid='ignore'):
            with self.assertRaisesRegex(ValueError,'spectral consistency failed'):
                scalar.spectral_consistency(record)

    def test_changed_weights_and_cross_weights_fail_without_lost_record(self):
        from copy import deepcopy
        original=scalar.su2.character(1,0,8)
        for key in ('weights','cross_weights'):
            record=deepcopy(original)
            if key=='weights':
                record[key][0][0]+=.01
            else:
                record[key][0]+=.01
            with patch.object(scalar.su2,'character',return_value=record):
                result=scalar.run('SU2',1,0,[8],[32])
            self.assertEqual(result['status'],'failed')
            slot=result['result']['rungs'][0]
            self.assertEqual(slot['result'],record)
            self.assertIn('spectral consistency failed',slot['reason'])

    def test_archived_finest_records_meet_sum_rules(self):
        import json
        for name in ('refinement.json','u1-design-development.json'):
            archive=json.loads((scalar.su2.ROOT/'research/vacuum-spectrum'/name).read_text())
            for cell in archive['cells']:
                for method,record in cell['final'].items():
                    with self.subTest(archive=name,g=cell['g'],method=method):
                        self.assertEqual(scalar.spectral_consistency(record)['status'],'passed')

    def test_free_models_retain_all_requests_and_observables(self):
        for theory in ('SU2','U1'):
            with self.subTest(theory=theory):
                result = scalar.run(theory,1,0,[8,16],[64,128])
                self.assertEqual(result['status'],'completed')
                self.assertEqual(len(result['result']['rungs']),4)
                self.assertEqual(result['precision_status'],'not_assessed')
                basis=result['result']['final']['character' if theory=='SU2' else 'fourier']
                self.assertEqual(len(basis['moments']),5)
                self.assertAlmostEqual(basis['first_three_gaps'][0],3 if theory=='SU2' else 4)
                if theory=='U1':
                    self.assertIn('odd_energies',basis)
                    self.assertAlmostEqual(basis['full_gap'],4)

    def test_interacting_deformation(self):
        result=scalar.run('SU2',1,'0.5',[8],[32])
        self.assertEqual(result['status'],'completed')
        self.assertEqual(result['result']['eta'],'1/2')
        self.assertIsNotNone(result['result']['cross_representation_difference'])

    def test_final_failure_does_not_fall_back_or_cancel_other_method(self):
        original=scalar.su2.character
        def injected(g,eta,j):
            if j==16:
                raise RuntimeError('injected final cutoff failure')
            return original(g,eta,j)
        with patch.object(scalar.su2,'character',side_effect=injected):
            result=scalar.run('SU2',1,0,[8,16],[32,64])
        self.assertEqual(result['status'],'failed')
        self.assertEqual([s['status'] for s in result['result']['rungs']],
                         ['completed','failed','completed','completed'])
        self.assertIsNone(result['result']['final'])
        self.assertIsNone(result['result']['cross_representation_agreement'])

    def test_nonfinite_record_does_not_poison_serialization(self):
        import json
        with patch.object(scalar.su2,'character',return_value={'E0':float('nan')}):
            result=scalar.run('SU2',1,0,[8],[32])
        json.dumps(result,allow_nan=False)
        self.assertEqual(result['result']['rungs'][0]['status'],'failed')
        self.assertEqual(result['result']['rungs'][1]['status'],'completed')

    def test_invalid_ladder_rejected_before_solver(self):
        with patch.object(scalar.su2,'character',side_effect=AssertionError('unexpected solver')):
            with self.assertRaises(ValueError):
                scalar.run('SU2',1,0,[8,8],[32])

    def test_comparison_failure_preserves_completed_solvers(self):
        with patch.object(scalar.su2,'differences',side_effect=RuntimeError('injected comparison failure')):
            result=scalar.run('SU2',1,0,[8],[32])
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['result']['comparison_status'],'failed')
        self.assertTrue(all(s['status']=='completed' for s in result['result']['rungs']))
        self.assertEqual(set(result['result']['final']),{'character','angle_fourth'})

    def test_nonfinite_comparison_is_not_serialized(self):
        import json
        with patch.object(scalar.su2,'differences',return_value={'moment_absolute':[float('inf')]}):
            result=scalar.run('SU2',1,0,[8],[32])
        json.dumps(result,allow_nan=False)
        self.assertEqual(result['result']['comparison_status'],'failed')
        self.assertIsNone(result['result']['cross_representation_difference'])
        self.assertIsNotNone(result['result']['final'])


if __name__ == '__main__':
    unittest.main()
