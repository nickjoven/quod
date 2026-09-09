"""Analytic temporal-bias and numerical-error discrimination."""
from fractions import Fraction as F
import unittest

import vacuum_intervals as interval
import vacuum_time_windows as windows


def exponential(time):
    return interval.exp_negative(F(time))


def midpoint(bounds):
    return sum(bounds) / 2


class TimeWindowTests(unittest.TestCase):
    def test_logarithm_against_exact_series(self):
        # ln(2)=2 sum z^(2n+1)/(2n+1), z=1/3, with a geometric tail bound.
        z, terms = F(1, 3), 160
        lower = 2 * sum((z**(2 * n + 1) / (2 * n + 1) for n in range(terms)), F(0))
        upper = lower + 2 * z**(2 * terms + 1) / ((2 * terms + 1) * (1 - z**2))
        actual = windows.log_point(F(2))
        self.assertLessEqual(actual[0], lower)
        self.assertGreaterEqual(actual[1], upper)
        self.assertEqual(windows.log_point(F(1)), (F(0), F(0)))

    def test_single_mode_qualifies(self):
        left, right = exponential(1), exponential(2)
        result = windows.assess_pair(left, right, midpoint(left), midpoint(right), F(1), (F(1), F(1)), True)
        self.assertTrue(result['qualifies'])
        self.assertLess(result['relative_combined_error_upper'], F(1, 10**60))

    def test_mixture_requires_later_times(self):
        def mixed(t):
            return interval.add(exponential(t), exponential(2 * t))
        for start, end, expected in ((F(0), F(1), False), (F(20), F(24), True)):
            left, right = mixed(start), mixed(end)
            result = windows.assess_pair(left, right, midpoint(left), midpoint(right), end - start, (F(1), F(1)), True)
            self.assertEqual(result['qualifies'], expected)

    def test_noise_is_not_mistaken_for_small_mixture(self):
        left, right = exponential(1), exponential(2)
        result = windows.assess_pair(left, right, midpoint(left), midpoint(right) * F(101, 100), F(1), (F(1), F(1)), True)
        self.assertFalse(result['qualifies'])
        self.assertGreater(result['relative_numerical_slope_error_upper'], F(1, 1000))

    def test_dark_first_state_cannot_qualify(self):
        left, right = exponential(1), exponential(2)
        result = windows.assess_pair(left, right, midpoint(left), midpoint(right), F(1), (F(1), F(1)), False)
        self.assertFalse(result['qualifies'])
        self.assertEqual(result['reason'], 'first overlap not certified nonzero')

    def test_nonpositive_observation_remains_unresolved(self):
        result = windows.assess_pair((F(1), F(1)), (F(1, 2), F(1, 2)), F(1), F(0), F(1), (F(1), F(1)), True)
        self.assertFalse(result['qualifies'])
        with self.assertRaises(ValueError):
            windows.log_point(F(0))
        with self.assertRaises(ValueError):
            windows.slope_interval((F(0), F(1)), (F(1), F(2)), F(1))


if __name__ == '__main__':
    unittest.main()
