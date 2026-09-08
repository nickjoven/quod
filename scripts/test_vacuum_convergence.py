"""Regression checks for exact-spacing extrapolation and archived audit drift."""
import hashlib
import json
from pathlib import Path
import unittest

from vacuum_convergence import audit, sequence_diagnostics

ROOT = Path(__file__).resolve().parents[1]


class ConvergenceTests(unittest.TestCase):
    def test_non_nested_second_order(self):
        h = [1 / 601, 1 / 1201, 1 / 2401, 1 / 4801]
        result = sequence_diagnostics(h, [3 + 10 * x*x for x in h])
        for p in result['observed_orders']:
            self.assertAlmostEqual(p, 2, places=7)
        for y in result['extrapolated_values']:
            self.assertAlmostEqual(y, 3, places=13)
        self.assertTrue(all(c < 0 for c in result['signed_fine_grid_corrections']))

    def test_flat_and_sign_reversal_do_not_claim_order(self):
        self.assertEqual(sequence_diagnostics([4, 2, 1], [1, 1, 1])['observed_orders'], [None])
        self.assertEqual(sequence_diagnostics([4, 2, 1], [1, 2, 1])['observed_orders'], [None])

    def test_exact_fourth_order(self):
        h = [1 / 7, 1 / 12, 1 / 23]
        r = sequence_diagnostics(h, [2 + x**4 for x in h], order=4)
        self.assertAlmostEqual(r['observed_orders'][0], 4, places=7)
        self.assertAlmostEqual(r['extrapolated_values'][-1], 2, places=13)

    def test_invalid_mesh(self):
        with self.assertRaises(ValueError):
            sequence_diagnostics([1, 2, 3], [1, 2, 3])

    def test_archive_reproduction_and_hashes(self):
        source = (ROOT / 'research/vacuum-spectrum/development.json').read_bytes()
        archived = json.loads((ROOT / 'research/vacuum-spectrum/refinement-audit.json').read_text())
        self.assertEqual(archived.pop('input_sha256'), hashlib.sha256(source).hexdigest())
        self.assertEqual(archived.pop('audit_source_sha256'), hashlib.sha256(
            (ROOT / 'scripts/vacuum_convergence.py').read_bytes()).hexdigest())
        self.assertEqual(archived, audit(json.loads(source)))


if __name__ == '__main__':
    unittest.main()
