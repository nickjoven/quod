"""Late-time extension contracts and failure continuation."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import vacuum_development as baseline
import vacuum_late_time_run as runner
import vacuum_semigroup as semigroup


class LateTimeTests(unittest.TestCase):
    def test_extension_preserves_old_times_and_fixed_grids(self):
        self.assertEqual(runner.TAU[:8], semigroup.TAU)
        self.assertEqual(runner.TAU[8:], (12., 16., 20., 24.))
        self.assertEqual(runner.TOLERANCES, ((1e-8, 1e-18), (1e-10, 1e-20)))
        self.assertEqual(baseline.ANGLE_INTERIORS, (600, 1200, 2400, 4800))
        inputs, hashes = runner.load_inputs()
        self.assertEqual(len(inputs['semigroup.json']['cells']), 10)
        self.assertEqual(len(hashes), 3)

    def test_failure_does_not_cancel_remaining_evolutions(self):
        inputs, hashes = runner.load_inputs()
        inputs = copy.deepcopy(inputs)
        for report in inputs.values():
            report['cells'] = report['cells'][:2]
        for cell in inputs['refinement.json']['cells']:
            cell['final']['angle_fourth'] = semigroup.angle_refined(cell['g'], 1, 32)
        calls = []
        original = semigroup.propagate

        def injected(*args):
            calls.append(1)
            result = original(*args)
            if len(calls) == 2:
                result['correlations'][-1][-1][-1] = float('nan')
            return result

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'late.json'
            with patch.object(runner, 'load_inputs', return_value=(inputs, hashes)), \
                    patch.object(baseline, 'G_VALUES', (.1, .15)), \
                    patch.object(baseline, 'ANGLE_INTERIORS', (16, 32)), \
                    patch.object(semigroup, 'propagate', side_effect=injected), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
                report = json.loads(output.read_text())
                self.assertTrue(runner.accounting(report))
            self.assertEqual(len(calls), 8)
            self.assertEqual([c['status'] for c in report['cells']], ['failure', 'unresolved'])
            self.assertEqual(report['cells'][0]['rungs'][0]['evolutions'][1]['status'], 'failure')
            self.assertNotIn('result', report['cells'][0]['rungs'][0]['evolutions'][1])
            self.assertTrue(all(t['status'] == 'unrun' for t in report['targets']))


if __name__ == '__main__':
    unittest.main()
