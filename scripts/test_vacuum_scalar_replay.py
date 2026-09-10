"""Scalar arithmetic replay and failure preservation at development coordinates."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import vacuum_scalar_replay as replay


class ScalarReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs={t:replay.scalar.run(t,'1','0',[8,16],[32,64]) for t in ('SU2','U1')}

    def check(self,output,theory='SU2'):
        return replay.verify(theory,'1','0',[8,16],[32,64],output)

    def test_both_models_replay_without_solver(self):
        with patch.object(replay.scalar.su2,'character',side_effect=AssertionError('solver reached')), patch.object(
                replay.scalar.u1,'fourier',side_effect=AssertionError('solver reached')):
            for theory,output in self.outputs.items():
                result=self.check(output,theory)
                self.assertEqual(result['status'],'verified',result)

    def test_altered_coordinate_flags_difference_final_and_requests_fail(self):
        mutations=[lambda r:r['result'].update(eta='1'),
                   lambda r:r['result']['rungs'].pop(),
                   lambda r:r['result']['final']['character'].update(E0=123),
                   lambda r:r['result'].update(cross_representation_difference={}),
                   lambda r:r['result'].update(cross_representation_agreement=not r['result']['cross_representation_agreement']),
                   lambda r:r['result']['rungs'][0].update(spectral_consistency={}),
                   lambda r:r['result']['rungs'][0]['result'].update(J=4)]
        for mutate in mutations:
            output=deepcopy(self.outputs['SU2']); mutate(output)
            self.assertEqual(self.check(output)['status'],'invalid')

    def test_finest_failure_is_preserved_without_fallback(self):
        original=replay.scalar.su2.character
        def injected(g,eta,j):
            if j==16:
                raise RuntimeError('injected finest failure')
            return original(g,eta,j)
        with patch.object(replay.scalar.su2,'character',side_effect=injected):
            output=replay.scalar.run('SU2',1,0,[8,16],[32,64])
        self.assertEqual(self.check(output)['status'],'verified')
        self.assertIsNone(self.check(output)['cross_representation_agreement'])
        output['result']['final']={'character':output['result']['rungs'][0]['result']}
        self.assertEqual(self.check(output)['status'],'invalid')

    def test_failed_comparison_retains_solver_records(self):
        with patch.object(replay.scalar.su2,'differences',side_effect=RuntimeError('injected comparison failure')):
            output=replay.scalar.run('SU2',1,0,[8,16],[32,64])
        self.assertEqual(self.check(output)['status'],'verified')
        self.assertIsNotNone(output['result']['final'])
        output['result']['cross_representation_agreement']=True
        self.assertEqual(self.check(output)['status'],'invalid')

    def test_failed_validation_retains_malformed_solver_evidence(self):
        with patch.object(replay.scalar.su2,'character',return_value={'E0':123}):
            output=replay.scalar.run('SU2',1,0,[8,16],[32,64])
        self.assertEqual(self.check(output)['status'],'verified')
        self.assertEqual(output['result']['rungs'][0]['result'],{'E0':123})


if __name__=='__main__':
    unittest.main()
