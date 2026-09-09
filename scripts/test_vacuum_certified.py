"""Exact endpoint checks, independent fixtures, and deliberately false bounds."""
import copy
from fractions import Fraction as F
import unittest

import numpy as np
from scipy.linalg import eigh_tridiagonal

import vacuum_certified as certified
import vacuum_intervals as interval


class CertifiedTests(unittest.TestCase):
    def test_sturm_zero_minors_and_reducible_diagonal(self):
        self.assertEqual(certified.sturm_count([0, 0], 1, 0), 1)
        self.assertEqual(certified.sturm_count([0, 0, 0], 1, 0), 1)
        self.assertEqual(certified.sturm_count([0, 0, 0], 1, -1), 1)
        self.assertEqual(certified.sturm_count([0, 0, 0], 1, 1), 2)
        self.assertEqual(certified.sturm_count([0, 0, 1], 0, 0), 0)
        self.assertEqual(certified.sturm_count([0, 0, 1], 0, 1), 2)

    def test_sturm_independent_dense_eigenvalues(self):
        for size in (3, 7, 12):
            diagonal = [F(n * n - 3, 7) for n in range(size)]
            hopping = F(-2, 3)
            exact_matrix = np.diag(np.array(diagonal, dtype=float))
            exact_matrix += np.diag(np.full(size - 1, float(hopping)), 1)
            exact_matrix += np.diag(np.full(size - 1, float(hopping)), -1)
            eigenvalues = np.linalg.eigvalsh(exact_matrix)
            for x in (F(-2), F(-1, 5), F(1, 7), F(10)):
                self.assertGreater(np.min(abs(eigenvalues - float(x))), 1e-6)
                self.assertEqual(certified.sturm_count(diagonal, hopping, x), sum(eigenvalues < float(x)))

    def test_free_infinite_enclosures_and_endpoint_mutants(self):
        enclosures = certified.eigenvalue_enclosures('.5', 0, 41)
        self.assertTrue(certified.verify_enclosures('.5', 0, 41, enclosures))
        for k, enclosure in enumerate(enclosures):
            exact = F(k * (k + 2), 4)
            self.assertLessEqual(enclosure["lower"], exact)
            self.assertGreaterEqual(enclosure["upper"], exact)
            self.assertLess(enclosure["upper"] - enclosure["lower"], F(1, 10**11))
        for key, delta in (("lower", F(1)), ("upper", F(-1))):
            mutant = copy.deepcopy(enclosures)
            mutant[1][key] += delta
            self.assertFalse(certified.verify_enclosures('.5', 0, 41, mutant))

    def test_cutoff_tail_cannot_be_ignored(self):
        enclosures = certified.eigenvalue_enclosures('.1', 1, 41)
        self.assertTrue(certified.verify_enclosures('.1', 1, 41, enclosures))
        self.assertGreater(enclosures[0]["upper"] - enclosures[0]["lower"], 1)
        mutant = copy.deepcopy(enclosures)
        mutant[0]["lower"] = mutant[0]["finite_lower"]
        self.assertFalse(certified.verify_enclosures('.1', 1, 41, mutant))
        vector = np.zeros(41)
        vector[-1] = 1
        bound = certified.eigenvector_bound('.1', 1, vector, 0, enclosures)
        mu = bound["rayleigh_reference"]
        expected_squared = (F(40 * 42, 100) - mu)**2 + 2 * 100**2
        self.assertGreaterEqual(bound["residual_norm_upper"]**2, expected_squared)

    def test_sqrt_and_decimal_enclosures(self):
        for value in (F(0), F(1), F(2, 3), F(123456789, 7), F(1, 10**40)):
            low, high = certified.sqrt_interval(value)
            self.assertLessEqual(low**2, value)
            self.assertGreaterEqual(high**2, value)
        # Independent exact alternating Taylor bounds for exp(-x), x<=1.
        for x in (F(1), F(1, 8), F(1, 3)):
            term, total = F(1), F(1)
            for n in range(1, 181):
                term *= -x / n
                total += term
            true_upper = total
            true_lower = total + term * -x / 181
            low, high = interval.exp_negative(x)
            self.assertLessEqual(low, true_lower)
            self.assertGreaterEqual(high, true_upper)

    def test_free_overlaps_and_correlations(self):
        enclosures = certified.eigenvalue_enclosures('.5', 0, 41)
        vectors = np.eye(41)[:4]
        bounds = [certified.eigenvector_bound('.5', 0, vector, k, enclosures)
                  for k, vector in enumerate(vectors)]
        overlaps = certified.overlap_intervals(vectors, bounds)
        expected = [[F(1, 4), F(0)], [F(0), F(1, 16)], [F(0), F(0)]]
        for row, reference in zip(overlaps, expected):
            for enclosure, truth in zip(row, reference):
                self.assertLessEqual(enclosure["weight_lower"], truth)
                self.assertGreaterEqual(enclosure["weight_upper"], truth)
                self.assertEqual(enclosure["nonzero_certified"], truth > 0)
        vacuum = certified.vacuum_intervals(vectors[0], bounds[0])
        correlations = certified.correlation_intervals(enclosures, overlaps, vacuum, [F(0), F(1)])
        for row in correlations:
            expected = [interval.exp_negative(F(3, 4) * row["time"]),
                        interval.exp_negative(2 * row["time"])]
            for a, (low, high) in enumerate(expected):
                scale = F(1, 4) if a == 0 else F(1, 16)
                self.assertLessEqual(row["correlation"][a][a][0], low * scale)
                self.assertGreaterEqual(row["correlation"][a][a][1], high * scale)
            self.assertLessEqual(row["correlation"][0][1][0], 0)
            self.assertGreaterEqual(row["correlation"][0][1][1], 0)

    def test_sign_invariance_of_weights_and_cross_correlations(self):
        diagonal, hopping, _ = certified.parameters('.7', 1, 41)
        _, vectors = eigh_tridiagonal(np.array(diagonal, dtype=float), np.full(40, float(hopping)),
                                     select='i', select_range=(0, 3))
        vectors = vectors.T
        enclosures = certified.eigenvalue_enclosures('.7', 1, 41)
        bounds = [certified.eigenvector_bound('.7', 1, v, k, enclosures) for k, v in enumerate(vectors)]
        overlaps = certified.overlap_intervals(vectors, bounds)
        vacuum = certified.vacuum_intervals(vectors[0], bounds[0])
        reference = certified.correlation_intervals(enclosures, overlaps, vacuum, [F(1)])
        flipped = vectors.copy()
        flipped[2] *= -1
        mutated = certified.overlap_intervals(flipped, bounds)
        self.assertEqual(reference, certified.correlation_intervals(enclosures, mutated, vacuum, [F(1)]))

    def test_nonfinite_and_invalid_inputs(self):
        for g in (0, float('nan'), float('inf')):
            with self.assertRaises((ValueError, OverflowError)):
                certified.parameters(g, 1, 41)
        with self.assertRaises(ValueError):
            interval.exp_negative(F(-1))
        with self.assertRaises(ValueError):
            interval.decay((F(-1), F(2)), F(1))


if __name__ == '__main__':
    unittest.main()
