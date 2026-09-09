"""Recovered analytic nulls and immutable report replay."""
from fractions import Fraction as F
import json
import unittest
from unittest.mock import patch

import vacuum_design_nulls as runner


class DesignNullTests(unittest.TestCase):
    def test_archive_and_all_checks(self):
        result=runner.evaluate()
        self.assertTrue(result['pass'])
        self.assertEqual(runner.shared.encode(result),json.loads((runner.baseline.ROOT/'research/vacuum-spectrum/design-nulls.json').read_text()))
        self.assertEqual(len(result['targets']),42)
        self.assertTrue(all(t['status']=='unrun' for t in result['targets']))

    def test_tensor_exact_arithmetic_and_validation(self):
        result=runner.tensor(F(1,3))
        self.assertEqual(result['energies'],[0,F(2,3),2,F(8,3)])
        self.assertEqual(result['ground'],[F(1,2)]*4)
        self.assertTrue(all(isinstance(v,(int,F)) for row in result['matrix'] for v in row))
        self.assertTrue(all(result['eigenpair_checks']))
        for epsilon in (0,-1,2):
            with self.assertRaises(ValueError):
                runner.tensor(epsilon)

    def test_missing_low_mass_is_not_gapless_evidence(self):
        with patch.object(runner,'mass_below',return_value=(F(0),F(0))):
            result=runner.evaluate()
            self.assertFalse(result['pass'])
            self.assertFalse(result['checks']['exponential_measure_low_mass'])
            self.assertFalse(result['mutants_rejected']['positive_floor_for_exponential_measure'])


if __name__=='__main__':
    unittest.main()
