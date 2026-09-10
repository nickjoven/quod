"""Offline replay and corruption checks using development calibration only."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

import vacuum_temporal_replay as replay


class TemporalReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tolerances=[[1e-10,1e-14]]
        cls.certificates={t:replay.temporal.certificates.calculate(t,'1','0',8,[0,F(1,2),1]) for t in ('SU2','U1')}
        cls.outputs={t:replay.temporal.run(c,[128],cls.tolerances) for t,c in cls.certificates.items()}

    def test_two_models_replay_without_solver(self):
        with patch.object(replay.temporal.evolution,'propagate',side_effect=AssertionError('solver reached')):
            for theory in self.certificates:
                result=replay.verify(self.certificates[theory],self.outputs[theory],[128],self.tolerances)
                self.assertEqual(result['status'],'verified',result)

    def test_changed_assessment_clock_error_and_request_are_rejected(self):
        mutations=[lambda r:r['result']['times'].__setitem__(1,'1/4'),
                   lambda r:r['result']['rungs'][0].update(nodes=256),
                   lambda r:r['result'].update(certificate_sha256='0'*64),
                   lambda r:r['result']['rungs'][0]['evolutions'][0]['pairs'].pop(),
                   lambda r:r['result']['rungs'][0]['evolutions'][0].update(angle_error_bounds={}),
                   lambda r:r['result']['rungs'][0]['evolutions'][0]['result'].update(rtol=1e-4),
                   lambda r:r['result']['rungs'][0]['evolutions'][0]['pairs'][0]['observables'][0]['window'].update(
                       qualifies=not r['result']['rungs'][0]['evolutions'][0]['pairs'][0]['observables'][0]['window']['qualifies'])]
        for mutate in mutations:
            output=deepcopy(self.outputs['SU2']); mutate(output)
            self.assertEqual(replay.verify(self.certificates['SU2'],output,[128],self.tolerances)['status'],'invalid')

    def test_failed_assessment_retains_and_replays_propagation(self):
        with patch.object(replay.temporal,'angle_error_bounds',side_effect=RuntimeError('injected assessment failure')):
            output=replay.temporal.run(self.certificates['SU2'],[32],self.tolerances)
        self.assertEqual(replay.verify(self.certificates['SU2'],output,[32],self.tolerances)['status'],'verified')
        del output['result']['rungs'][0]['evolutions'][0]['result']
        self.assertEqual(replay.verify(self.certificates['SU2'],output,[32],self.tolerances)['status'],'invalid')

    def test_failed_propagation_is_accounted(self):
        with patch.object(replay.temporal.evolution,'propagate',side_effect=RuntimeError('injected failure')):
            output=replay.temporal.run(self.certificates['U1'],[32],self.tolerances)
        self.assertEqual(replay.verify(self.certificates['U1'],output,[32],self.tolerances)['status'],'verified')

    def test_coarse_certificate_remains_unresolved(self):
        certificate=replay.temporal.certificates.calculate('SU2','0.1','1',4,[0,F(1,8)])
        output=replay.temporal.run(certificate,[32],self.tolerances)
        result=replay.verify(certificate,output,[32],self.tolerances)
        self.assertEqual(result['status'],'verified',result)
        self.assertEqual(result['stage_status'],'unresolved')
        self.assertEqual(result['common_sample_pairs'],[])


if __name__=='__main__':
    unittest.main()
