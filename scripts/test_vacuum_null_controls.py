"""Exact analytic null controls and report reproduction."""
from fractions import Fraction as F
import json
import unittest
from unittest.mock import patch

import vacuum_certificate_run as certificates
import vacuum_development as baseline
import vacuum_null_controls as controls


class NullControlTests(unittest.TestCase):
    def test_hidden_and_disconnected_channels_remain_distinct(self):
        hidden = controls.measure([0,1,2], [0,0,1])
        self.assertEqual(hidden['first_ordered_gap'], 1)
        self.assertEqual(hidden['observed_threshold'], 2)
        disconnected = controls.measure([0,0,1], [3,1,1])
        self.assertEqual(disconnected['ground_multiplicity'], 2)
        self.assertEqual(disconnected['zero_gap_weight'], 1)
        self.assertEqual(disconnected['variance'], 2)
        self.assertEqual(disconnected['gap_above_ground_space'], 1)

    def test_uniform_measure_normalization_and_small_energy_mass(self):
        self.assertEqual(controls.uniform_gapless_correlation(0), (F(1), F(1)))
        for n in (2,10,100):
            self.assertEqual(controls.uniform_mass_below(F(1,n)), F(1,n))
            low, high = controls.uniform_gapless_correlation(n)
            self.assertTrue(0 < low <= high < F(1,n))
        with patch.object(controls, 'uniform_mass_below', return_value=F(0)):
            self.assertFalse(controls.evaluate()['pass'])

    def test_control_report_and_archive(self):
        result = controls.evaluate()
        self.assertTrue(result['pass'])
        self.assertTrue(all(result['mutants_rejected'].values()))
        self.assertEqual(result['targets_run'], 0)
        self.assertEqual(len(result['targets']), 42)
        report = json.loads((baseline.ROOT / 'research/vacuum-spectrum/null-controls.json').read_text())
        self.assertEqual(report, certificates.encode(result))


if __name__ == '__main__':
    unittest.main()
