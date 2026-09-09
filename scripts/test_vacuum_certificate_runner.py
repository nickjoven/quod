"""Certificate replay and resilient fixed-manifest runner failure checks."""
import contextlib
import copy
from fractions import Fraction as F
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import vacuum_certificate_run as runner
import vacuum_development as baseline


class CertificateRunnerTests(unittest.TestCase):
    def test_exact_replay_rejects_changed_vector_and_bounds(self):
        result = runner.encode(runner.calculate(.7, 20, [F(0), F(1)]))
        self.assertTrue(runner.verify_result(.7, result, [F(0), F(1)]))
        changed = copy.deepcopy(result)
        changed['candidate_vectors_hex'][0][0] = float(0).hex()
        self.assertFalse(runner.verify_result(.7, changed, [F(0), F(1)]))
        changed = copy.deepcopy(result)
        changed['overlaps'][0][0]['weight_lower'] = '1'
        self.assertFalse(runner.verify_result(.7, changed, [F(0), F(1)]))
        changed = copy.deepcopy(result)
        changed['enclosures'][0]['finite_lower'] = '9999'
        self.assertFalse(runner.verify_result(.7, changed, [F(0), F(1)]))

    def test_injected_nonfinite_failure_preserves_later_requests(self):
        original = runner.calculate
        calls = []

        def injected(g, j, times):
            calls.append((g, j))
            result = original(g, j, times)
            if len(calls) == 2:
                result['invalid'] = float('nan')
            return result

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'certificates.json'
            with patch.object(baseline, 'G_VALUES', (.1, .15)), \
                    patch.object(baseline, 'CHARACTER_J', (2, 3)), \
                    patch.object(runner.semigroup_run, 'accounting', return_value=True), \
                    patch.object(runner, 'calculate', side_effect=injected), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
                report = json.loads(output.read_text())
                self.assertTrue(runner.accounting(report))
                changed = copy.deepcopy(report)
                changed['cells'][0]['rungs'].pop()
                self.assertFalse(runner.accounting(changed))
            self.assertEqual(len(calls), 4)
            self.assertEqual([c['status'] for c in report['cells']], ['failure', 'unresolved'])
            self.assertEqual(report['cells'][0]['rungs'][1]['status'], 'failure')
            self.assertNotIn('result', report['cells'][0]['rungs'][1])
            self.assertTrue(all(t['status'] == 'unrun' for t in report['targets']))

    def test_total_error_uses_both_interval_endpoints(self):
        correlations = [{'time': F(0), 'correlation': [[(F(1), F(2)), (F(-1), F(1))],
                                                      [(F(-1), F(1)), (F(2), F(4))]]}]
        vacuum = {'covariance': [[(F(1), F(2)), (F(-1), F(1))],
                                  [(F(-1), F(1)), (F(4), F(5))]]}
        rungs = [{'rung': 600, 'evolutions': [{'result': {'correlations': [[[1.5, .25], [.25, 3.]]]}}]}]
        result = runner.angle_error_bounds(correlations, vacuum, rungs)[0]['samples'][0]
        self.assertEqual(result['absolute_error_upper'], [[F(1, 2), F(5, 4)], [F(5, 4), F(1)]])
        self.assertEqual(result['initial_variance_normalized_error_upper'], [[F(1, 2), F(5, 8)], [F(5, 8), F(1, 4)]])


if __name__ == '__main__':
    unittest.main()
