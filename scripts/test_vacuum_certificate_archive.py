"""Exact replay of every archived development certificate and angle bound."""
from fractions import Fraction as F
import hashlib
import json
import unittest

import vacuum_certificate_run as runner
import vacuum_development as baseline


def fractions(value):
    if isinstance(value, str):
        return F(value)
    if isinstance(value, list):
        return [fractions(child) for child in value]
    if isinstance(value, dict):
        return {key: fractions(child) for key, child in value.items()}
    return value


class CertificateArchiveTests(unittest.TestCase):
    def test_full_exact_replay_and_input_provenance(self):
        path = baseline.ROOT / 'research/vacuum-spectrum/certificates.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        self.assertEqual(report['state'], 'completed')
        self.assertTrue(runner.accounting(report))
        self.assertTrue(report['source_unchanged_during_run'])
        self.assertEqual(report['source_sha256'], runner.source_hashes())
        source = baseline.ROOT / report['input']
        self.assertEqual(report['input_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
        source_report = json.loads(source.read_text())
        doc = (baseline.ROOT / 'research/vacuum-spectrum/CERTIFICATES-RUN.md').read_text()
        self.assertIn(hashlib.sha256(raw).hexdigest(), doc)
        for cell, source_cell in zip(report['cells'], source_report['cells']):
            times = [F(t) for t in cell['times']]
            self.assertEqual(times, [F(float(t)) for t in source_cell['times']])
            self.assertEqual(cell['status'], 'unresolved')
            self.assertIsNone(cell['usable_time_window'])
            for rung in cell['rungs']:
                self.assertEqual(rung['status'], 'completed')
                result = rung['result']
                self.assertEqual(result['size'], 2 * rung['J'] + 1)
                self.assertTrue(runner.verify_result(cell['g'], result, times))
                eigen = result['enclosures']
                gaps = [(F(e['lower']) - F(eigen[0]['upper']), F(e['upper']) - F(eigen[0]['lower']))
                        for e in eigen[1:4]]
                self.assertEqual(result['first_three_gap_intervals'], runner.encode(gaps))
                vacuum = fractions(result['vacuum'])
                moments = None if vacuum is None else [*vacuum['raw_moments'][:2],
                    vacuum['covariance'][0][0], vacuum['covariance'][1][1], vacuum['covariance'][0][1]]
                gap_ok = all(low > 0 and (high - low) / (2 * low) <= F(1, 10**6) for low, high in gaps)
                moment_ok = moments is not None and all((high - low) / 2 <= F(1, 10**6) for low, high in moments)
                self.assertEqual(result['scalar_budget_met'], gap_ok and moment_ok)
                if result['overlaps'] is not None:
                    self.assertEqual(result['first_gap_overlap_certified'], [
                        F(entry['weight_lower']) > 0 for entry in result['overlaps'][0]])
            final = cell['rungs'][-1]['result']
            expected = runner.angle_error_bounds(fractions(final['correlations']), fractions(final['vacuum']),
                [r for r in source_cell['rungs'] if r['method'] == 'angle_fourth'])
            self.assertEqual(cell['angle_error_bounds'], runner.encode(expected))


if __name__ == '__main__':
    unittest.main()
