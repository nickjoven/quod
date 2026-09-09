"""Deterministic replay of the initial window assessment."""
import json
import unittest

import vacuum_certificate_run as certificates
import vacuum_development as baseline
import vacuum_time_windows as windows


class WindowArchiveTests(unittest.TestCase):
    def test_reproduction_and_holdouts(self):
        report = json.loads((baseline.ROOT / 'research/vacuum-spectrum/time-windows.json').read_text())
        self.assertEqual(report, certificates.encode(windows.analyze()))
        self.assertFalse(report['registered'])
        self.assertEqual(report['targets_run'], 0)
        self.assertEqual(len(report['targets']), 42)
        self.assertTrue(all(t['status'] == 'unrun' for t in report['targets']))
        both = [c['g'] for c in report['cells'] if all(c['rungs'][-1]['qualified_pairs_by_observable'])]
        self.assertEqual(both, [.1])
        for cell in report['cells']:
            self.assertEqual([r['interiors'] for r in cell['rungs']], list(baseline.ANGLE_INTERIORS))
            self.assertTrue(all(len(r['pairs']) == 7 for r in cell['rungs']))


if __name__ == '__main__':
    unittest.main()
