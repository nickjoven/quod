from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import harness as h


class DurableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = h.specification()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        h.publish(self.directory / 'spec.json', self.spec)
        self.ledger = h.Ledger(self.directory, self.spec)

    def tearDown(self):
        self.temp.cleanup()

    def test_completed_work_replays_and_resumes_without_propagation(self):
        result = h.execute(self.ledger)
        self.assertEqual(result['terminal'], 8)
        self.assertTrue(all(v == 'completed' for v in result['outcomes'].values()))
        with patch.object(h.replay.temporal.evolution, 'propagate', side_effect=AssertionError('must not integrate')):
            restored = h.Ledger(self.directory, self.spec)
            self.assertEqual(h.summary(restored), result)
            with patch.object(h.replay.temporal.certificates, 'calculate', side_effect=AssertionError('must not regenerate certificates')):
                h.validate(self.spec)
                self.assertEqual(h.execute(restored), result)

    def test_raw_survives_crash_before_assessment_and_is_reused(self):
        with patch.object(h.replay.temporal, 'angle_error_bounds', side_effect=KeyboardInterrupt('power loss')):
            with self.assertRaises(KeyboardInterrupt):
                h.execute(self.ledger)
        restored = h.Ledger(self.directory, self.spec)
        self.assertEqual([e['kind'] for e in restored.events], ['started', 'propagation'])
        with self.assertRaisesRegex(ValueError, 'retry-interrupted'):
            h.execute(restored)
        original = h.replay.temporal.evolution.propagate
        with patch.object(h.replay.temporal.evolution, 'propagate', wraps=original) as solver:
            result = h.execute(restored, retry_interrupted=True)
        self.assertEqual(solver.call_count, 7)  # Eight tasks, first propagation reused.
        self.assertEqual(result['terminal'], 8)
        self.assertEqual(result['interrupted_attempts'], 1)
        self.assertEqual(restored.events[4]['reused_from'], 1)

    def test_solver_failures_are_terminal_and_never_retried(self):
        with patch.object(h.replay.temporal.evolution, 'propagate', side_effect=RuntimeError('injected solver failure')):
            result = h.execute(self.ledger)
        self.assertTrue(all(v == 'failed' for v in result['outcomes'].values()))
        with patch.object(h.replay.temporal.evolution, 'propagate', side_effect=AssertionError('must not retry')):
            self.assertEqual(h.execute(h.Ledger(self.directory, self.spec), True), result)

    def test_input_mismatch_stops_without_silent_recomputation(self):
        with patch.object(h.replay.temporal, 'angle_error_bounds', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                h.execute(self.ledger)
        with patch.object(h, 'input_digest', return_value='0' * 64), patch.object(
                h.replay.temporal.evolution, 'propagate', side_effect=AssertionError('must not recompute')):
            with self.assertRaisesRegex(h.DurabilityError, 'input mismatch'):
                h.execute(self.ledger, True)

    def test_storage_failure_is_not_relabelled_numerical_failure(self):
        original = h.publish
        def injected(path, value):
            if value.get('kind') == 'propagation':
                raise OSError('disk full')
            original(path, value)
        with patch.object(h, 'publish', side_effect=injected):
            with self.assertRaisesRegex(h.DurabilityError, 'disk full'):
                h.execute(self.ledger)
        self.assertEqual([e['kind'] for e in self.ledger.events], ['started'])

    def test_manifest_mutation_and_target_substitution_rejected(self):
        for mutate in (lambda s: s['tasks'][0].update(nodes=600),
                       lambda s: s['certificates']['U1'].update(g='1/8'),
                       lambda s: s['environment']['dependencies'].update(scipy='other')):
            spec = deepcopy(self.spec)
            mutate(spec)
            with self.assertRaisesRegex(ValueError, 'drift'):
                h.validate(spec)

    def test_corrupt_chain_or_orphan_is_rejected(self):
        self.ledger.append('started', self.spec['tasks'][0]['id'], 0)
        path = self.directory / 'event-000000.json'
        data = path.read_bytes()
        path.write_bytes(data.replace(b'started', b'altered'))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            h.Ledger(self.directory, self.spec)
        path.write_bytes(data)
        (self.directory / '.pending-crash').write_text('retained bytes')
        with self.assertRaisesRegex(ValueError, 'orphan'):
            h.Ledger(self.directory, self.spec)

    def test_exclusive_lock_and_no_overwrite(self):
        with h.locked(self.directory):
            with self.assertRaises(BlockingIOError):
                with h.locked(self.directory):
                    self.fail('second writer admitted')
        path = self.directory / 'spec.json'
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            h.publish(path, {'changed': True})
        self.assertEqual(path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
