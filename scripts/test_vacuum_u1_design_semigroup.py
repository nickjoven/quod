"""U1 even-gap reference contracts and failure continuation."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import vacuum_development as baseline
import vacuum_u1_design_semigroup_run as runner
import vacuum_semigroup as semigroup


class U1DesignSemigroupTests(unittest.TestCase):
    def test_calibration_and_even_reference(self):
        self.assertTrue(runner.calibration()['pass'])
        inputs, hashes = runner.load_inputs()
        self.assertEqual(len(hashes), 2)
        for cell in inputs['u1-design-certificates.json']['cells']:
            reference = runner.window_reference(cell)['rungs'][-1]['result']
            final = cell['rungs'][-1]['result']
            self.assertEqual(reference['first_three_gap_intervals'], final['first_three_even_gap_intervals'])
            self.assertNotEqual(reference['first_three_gap_intervals'][0], final['parity']['full_gap_interval'])
            self.assertEqual(reference['first_gap_overlap_certified'], [True, True])
        broken = copy.deepcopy(cell)
        broken['rungs'][-1]['result']['parity']['even_ground_below_odd_certified'] = False
        with self.assertRaises(ValueError):
            runner.window_reference(broken)

    def test_direct_against_dense_exponential(self):
        import numpy as np
        from scipy.linalg import eigh, expm
        matrix, obs = runner.u1.periodic_matrix(.7, 1, 32)
        energies, vectors = eigh(matrix.toarray())
        initial = semigroup.centered_vectors(vectors[:, 0], obs)
        times = [0., .1, .5, 2.]
        result = semigroup.propagate(matrix, energies[0], initial, times)
        expected = [initial.T @ expm(-t * (matrix.toarray() - energies[0] * np.eye(32))) @ initial for t in times]
        np.testing.assert_allclose(result['correlations'], expected, atol=2e-10, rtol=0)

    def test_calibration_failure_checkpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'failed.json'
            with patch.object(runner, 'calibration', side_effect=RuntimeError('injected')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
            report = json.loads(output.read_text())
            self.assertEqual(report['state'], 'instrument_failure')
            self.assertEqual(len(report['cells']), 10)
            self.assertTrue(all(t['status'] == 'unrun' for t in report['targets']))

    def test_failure_does_not_cancel_remaining_evolutions(self):
        inputs, hashes = runner.load_inputs()
        inputs = copy.deepcopy(inputs)
        for report in inputs.values():
            report['cells'] = report['cells'][:2]
        for cell in inputs['u1-design-development.json']['cells']:
            cell['final']['angle'] = runner.u1.angle(cell['g'], 1, 32)
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
            with patch.object(runner, 'calibration', return_value={'pass': True}), patch.object(runner, 'load_inputs', return_value=(inputs, hashes)), \
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
