"""Cost scenarios must use complete development timing evidence only."""
import copy
import json
import unittest
import vacuum_target_cost as runner


class TargetCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=runner.load_inputs()

    def test_replay_and_counts(self):
        result=runner.estimate(self.inputs)
        self.assertEqual(runner.shared.encode(result),json.loads((runner.DIRECTORY/'target-cost-plan.json').read_text()))
        self.assertEqual(sum(t['planned_counts']['representation_requests'] for t in result['theories']),378)
        self.assertEqual(sum(t['planned_counts']['certificate_rungs'] for t in result['theories']),210)
        self.assertEqual(sum(t['planned_counts']['evolutions'] for t in result['theories']),336)
        for theory in result['theories']:
            s=theory['scenario_seconds']
            self.assertLessEqual(s['mean_development'],s['slowest_development'])
            self.assertEqual(s['four_times_slowest_stress_assumption'],4*s['slowest_development'])
        self.assertFalse(result['target_execution_authorized'])

    def test_missing_and_nonfinite_timings_rejected(self):
        inputs=copy.deepcopy(self.inputs)
        inputs['u1-design-semigroup.json']['cells'][0]['rungs'][0]['evolutions'].pop()
        with self.assertRaisesRegex(ValueError,'evolution timing'):
            runner.estimate(inputs)
        inputs=copy.deepcopy(self.inputs)
        inputs['certificates.json']['cells'][0]['rungs'][0]['elapsed_seconds']=float('nan')
        with self.assertRaisesRegex(ValueError,'duration'):
            runner.estimate(inputs)

    def test_target_data_rejected(self):
        inputs=copy.deepcopy(self.inputs)
        inputs['refinement.json']['targets_run']=1
        with self.assertRaisesRegex(ValueError,'nondevelopment'):
            runner.estimate(inputs)


if __name__=='__main__':
    unittest.main()
