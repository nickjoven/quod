"""Calibrate direct propagation; preserve failures and exact sample clocks."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

import vacuum_parameterized_certificate as certificates
import vacuum_parameterized_temporal as temporal


class ParameterizedTemporalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.free = {theory: certificates.calculate(theory,'1','0',8,[0,F(1,8),F(1,4)])
                    for theory in ('SU2','U1')}

    def test_free_direct_assessment_uses_accessible_threshold(self):
        for theory, certificate in self.free.items():
            result = temporal.run(certificate,[128],[(1e-10,1e-14)])
            self.assertEqual(result['status'],'completed')
            slot = result['result']['rungs'][0]['evolutions'][0]
            self.assertEqual([o['threshold']['leading_level'] for o in slot['pairs'][0]['observables']],[1,2])
            self.assertFalse(slot['pairs'][0]['observables'][1]['threshold']['full_gap_claim_supported'])
            self.assertIsNone(slot['result']['integration_error_bound'])
            for pair in slot['pairs']:
                for observable in pair['observables']:
                    self.assertIn('relative_combined_error_upper',observable['window'])

    def test_bad_clock_fails_before_solver_and_preserves_requests(self):
        bad = certificates.calculate('SU2','1','0',8,[0,F(1,3)])
        with patch.object(temporal,'angle_refined',side_effect=AssertionError('unexpected solver')):
            result = temporal.run(bad,[32,64])
        self.assertEqual(result['status'],'failed')
        self.assertEqual([len(r['evolutions']) for r in result['result']['rungs']],[2,2])
        self.assertTrue(all(s['status']=='failed' for r in result['result']['rungs'] for s in r['evolutions']))

    def test_failed_tolerance_does_not_cancel_later_work(self):
        original = temporal.evolution.propagate
        calls = []
        def injected(*args,**kwargs):
            calls.append(1)
            if len(calls)==1:
                raise RuntimeError('injected first evolution failure')
            return original(*args,**kwargs)
        with patch.object(temporal.evolution,'propagate',side_effect=injected):
            result = temporal.run(self.free['SU2'],[32,64],[(1e-8,1e-12),(1e-10,1e-14)])
        self.assertEqual(len(calls),4)
        self.assertEqual(result['status'],'failed')
        slots=[s for r in result['result']['rungs'] for s in r['evolutions']]
        self.assertEqual([s['status'] for s in slots],['failed','completed','completed','completed'])

    def test_wrong_coordinates_rejected_before_propagation(self):
        bad = deepcopy(self.free['U1'])
        bad['eta']='1'
        with patch.object(temporal.u1,'angle',side_effect=AssertionError('unexpected solver')):
            result = temporal.run(bad,[32])
        self.assertEqual(result['status'],'failed')
        self.assertFalse(result['target_execution_authorized'])

    def test_interacting_deformation_preserves_u1_even_threshold(self):
        certificate = certificates.calculate('U1','1','0.5',8,[0,F(1,8),F(1,4)])
        result = temporal.run(certificate,[32],[(1e-10,1e-14)])
        self.assertEqual(result['status'],'completed')
        pair = result['result']['rungs'][0]['evolutions'][0]['pairs'][0]
        self.assertTrue(all(o['threshold']['leading_level']==1 for o in pair['observables']))
        self.assertTrue(all(not o['threshold']['full_gap_claim_supported'] for o in pair['observables']))

    def test_analysis_failure_retains_successful_propagation(self):
        with patch.object(temporal,'angle_error_bounds',side_effect=RuntimeError('injected assessment failure')):
            result = temporal.run(self.free['SU2'],[32],[(1e-10,1e-14)])
        slot = result['result']['rungs'][0]['evolutions'][0]
        self.assertEqual(slot['status'],'failed')
        self.assertEqual(slot['propagation_status'],'completed')
        self.assertEqual(slot['assessment_status'],'failed')
        self.assertEqual(len(slot['result']['correlations']),3)
        self.assertIn('assessment failure',slot['reason'])

    def test_valid_coarse_certificate_stays_unresolved(self):
        certificate = certificates.calculate('SU2','0.1','1',4,[0,F(1,8)])
        self.assertTrue(certificates.verify(certificate))
        self.assertEqual(certificate['result']['bound_status'],'unresolved')
        with patch.object(temporal,'angle_refined',side_effect=AssertionError('unexpected solver')):
            result = temporal.run(certificate,[32])
        self.assertEqual(result['status'],'unresolved')
        self.assertTrue(all(s['status']=='unresolved' for s in result['result']['rungs'][0]['evolutions']))


if __name__ == '__main__':
    unittest.main()
