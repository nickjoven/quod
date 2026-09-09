"""Replay later-time certificates, window bounds, and input provenance."""
import hashlib
import json
import unittest

import vacuum_certificate_run as certificates
import vacuum_development as baseline
import vacuum_u1_design_semigroup_run as runner
import vacuum_time_windows as windows


class U1DesignSemigroupArchiveTests(unittest.TestCase):
    def test_complete_archive_and_window_replay(self):
        raw = (baseline.ROOT / 'research/vacuum-spectrum/u1-design-semigroup.json').read_bytes()
        report = json.loads(raw)
        self.assertEqual(report['state'], 'completed')
        self.assertTrue(runner.accounting(report))
        self.assertTrue(report['source_unchanged_during_run'])
        self.assertEqual(report['source_sha256'], runner.source_hashes())
        inputs, hashes = runner.load_inputs()
        self.assertEqual(report['input_sha256'], hashes)
        doc = (baseline.ROOT / 'research/vacuum-spectrum/U1-DESIGN-SEMIGROUP-RUN.md').read_text()
        self.assertIn(hashlib.sha256(raw).hexdigest(), doc)
        self.assertEqual(report['dimensionless_times'], list(runner.certificates.TAU))
        self.assertEqual(sum(len(r['evolutions']) for c in report['cells'] for r in c['rungs']), 80)
        for i, cell in enumerate(report['cells']):
            self.assertEqual(cell['status'], 'unresolved')
            source = inputs['u1-design-certificates.json']['cells'][i]
            self.assertEqual(cell['times'], [float(runner.F(t)) for t in source['times']])
            cert = runner.window_reference(source)
            final = source['rungs'][-1]['result']
            self.assertEqual(cell['full_gap_interval'], final['parity']['full_gap_interval'])
            self.assertEqual(cell['first_even_gap_interval'], final['parity']['first_even_gap_interval'])
            self.assertEqual(report['observable_gap_reference'], 'first_even_gap')
            expected = windows.assess_cell(cert, cell)
            self.assertEqual(cell['window_assessment'], certificates.encode(expected))
            last_pair = expected['rungs'][-1]['pairs'][-1]
            self.assertEqual(last_pair['sample_indices'], [10, 11])
            self.assertTrue(all(o['qualifies'] and o['relative_combined_error_upper'] < runner.F('4.41e-8') for o in last_pair['observables']))
            self.assertEqual(cell['angle_error_bounds'], certificates.encode(certificates.angle_error_bounds(
                windows.numeric(final['correlations']), windows.numeric(final['vacuum']), cell['rungs'])))
            for rung in cell['rungs']:
                self.assertEqual(rung['status'], 'completed')
                self.assertEqual(rung['ground_origin'], 'archived_u1_development' if rung['rung']==4800 else 'fresh_parity_solve')
                for evolution in rung['evolutions']:
                    self.assertEqual(evolution['status'], 'completed')
                    self.assertEqual(len(evolution['result']['correlations']), 12)


if __name__ == '__main__':
    unittest.main()
