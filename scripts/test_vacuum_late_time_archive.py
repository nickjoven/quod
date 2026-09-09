"""Replay later-time certificates, window bounds, and input provenance."""
import hashlib
import json
import unittest

import vacuum_certificate_run as certificates
import vacuum_development as baseline
import vacuum_late_time_run as runner
import vacuum_time_windows as windows


class LateTimeArchiveTests(unittest.TestCase):
    def test_complete_archive_and_window_replay(self):
        raw = (baseline.ROOT / 'research/vacuum-spectrum/late-times.json').read_bytes()
        report = json.loads(raw)
        self.assertEqual(report['state'], 'completed')
        self.assertTrue(runner.accounting(report))
        self.assertTrue(report['source_unchanged_during_run'])
        self.assertEqual(report['source_sha256'], runner.source_hashes())
        inputs, hashes = runner.load_inputs()
        self.assertEqual(report['input_sha256'], hashes)
        doc = (baseline.ROOT / 'research/vacuum-spectrum/LATE-TIMES-RUN.md').read_text()
        self.assertIn(hashlib.sha256(raw).hexdigest(), doc)
        self.assertEqual(report['dimensionless_times'], list(runner.TAU))
        self.assertEqual(sum(len(r['evolutions']) for c in report['cells'] for r in c['rungs']), 80)
        for i, cell in enumerate(report['cells']):
            self.assertEqual(cell['status'], 'unresolved')
            self.assertEqual(cell['times'][:8], inputs['semigroup.json']['cells'][i]['times'])
            cert = runner.extended_certificate(inputs['certificates.json']['cells'][i], cell['times'])
            final = cert['rungs'][-1]['result']
            self.assertEqual(cell['certified_correlations'], certificates.encode(final['correlations']))
            expected = windows.assess_cell(cert, cell)
            self.assertEqual(cell['window_assessment'], certificates.encode(expected))
            self.assertTrue(all(expected['rungs'][-1]['qualified_pairs_by_observable']))
            self.assertEqual(cell['angle_error_bounds'], certificates.encode(certificates.angle_error_bounds(
                final['correlations'], windows.numeric(final['vacuum']), cell['rungs'])))
            for rung in cell['rungs']:
                self.assertEqual(rung['status'], 'completed')
                self.assertEqual(rung['ground_origin'], 'archived_refinement' if rung['rung']==4800 else 'fresh_banded_solve')
                for evolution in rung['evolutions']:
                    self.assertEqual(evolution['status'], 'completed')
                    self.assertEqual(len(evolution['result']['correlations']), 12)


if __name__ == '__main__':
    unittest.main()
