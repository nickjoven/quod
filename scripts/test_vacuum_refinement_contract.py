"""Adversarial fourth-order refinement checks; targets are never solved."""
import unittest

import numpy as np
from scipy.linalg import eig_banded
from unittest.mock import patch

import vacuum_development as development
import vacuum_angle_refined as refined


class RefinementContractTests(unittest.TestCase):
    def test_free_discrete_dispersion_and_haar_at_boundaries(self):
        for nodes in (24, 49):
            record = refined.angle_refined(.5, 0, nodes)
            h = np.pi / (nodes + 1)
            lam = 4 / h**2 * np.sin(np.arange(1, 5) * h / 2)**2
            exact = .25 * (lam + h**2 * lam**2 / 12 - 1)
            np.testing.assert_allclose(record['energies'], exact, atol=2e-12, rtol=0)
            np.testing.assert_allclose(record['moments'], [0, .25, .25, .0625, 0], atol=2e-12)
            # Check the normalized transformed Haar ground, not just a moment.
            sine = np.sqrt(2 / (nodes + 1)) * np.sin(np.arange(1, nodes + 1) * h)
            np.testing.assert_allclose(record['ground'], sine, atol=2e-12)
            np.testing.assert_allclose(np.asarray(record['weights'])[:2], [[.25, 0], [0, .0625]], atol=2e-12)

    def test_zero_exterior_ghost_mutant_breaks_free_dispersion(self):
        actual_solver = eig_banded

        def wrong_boundary(bands, **kwargs):
            bands = bands.copy()
            # Undo the odd-extension correction: plausible but wrong five-point closure.
            bands[0, [0, -1]] += bands[2, 0]
            return actual_solver(bands, **kwargs)

        baseline = refined.angle_refined(.5, 0, 49)
        with patch.object(refined, 'eig_banded', side_effect=wrong_boundary):
            mutant = refined.angle_refined(.5, 0, 49)
        self.assertGreater(max(abs(np.asarray(mutant['energies']) - baseline['energies'])), 1e-4)
        self.assertGreater(abs(mutant['moments'][1] - .25), 1e-5)

    def test_weak_development_cell_has_fourth_order_trend(self):
        reference = development.character(.1, 1, 80)
        errors = []
        for nodes in (300, 600, 1200):
            record = refined.angle_refined(.1, 1, nodes)
            errors.append(max(development.differences(record, reference)['gap_relative']))
            self.assertLess(record['orthogonality_defect'], 1e-12)
            self.assertLess(max(record['solver_relative_residual_first_four']), 1e-12)
            self.assertGreaterEqual(np.linalg.eigvalsh(record['unrepresented_covariance']).min(), -1e-12)
        self.assertTrue(all(12 < a / b < 20 for a, b in zip(errors, errors[1:])), errors)
        self.assertLess(errors[-1], 1e-6)

    def test_offset_and_clock_preserve_centered_spectral_measure(self):
        # Small Hermitian fixture with a nonzero observable mean and two channels.
        energies = np.array([-2., -.5, 3.])
        vectors = np.eye(3)
        applied = np.array([[.7, .2], [.3, -.4], [.2, .1]])
        baseline = development.observable_data(energies, vectors, applied, applied.T @ applied)
        shifted_applied = applied.copy()
        shifted_applied[0] += [4., -3.]
        shifted = development.observable_data(energies + 13, vectors, shifted_applied,
                                              shifted_applied.T @ shifted_applied)
        clocked = development.observable_data(3 * energies, vectors, applied, applied.T @ applied)
        for key in ('weights', 'cross_weights', 'covariance', 'vacuum_amplitudes'):
            np.testing.assert_allclose(shifted[key], baseline[key], atol=1e-14)
            np.testing.assert_allclose(clocked[key], baseline[key], atol=1e-14)
        np.testing.assert_allclose(shifted['first_three_gaps'], baseline['first_three_gaps'])
        np.testing.assert_allclose(clocked['first_three_gaps'], 3 * np.asarray(baseline['first_three_gaps']))

    def test_cutoff_tail_is_accounted_as_matrix_not_only_diagonal(self):
        record = development.character(.1, 1, 2)
        tail = np.asarray(record['observable_projection_tail_gram'])
        self.assertGreater(abs(tail[0, 1]), 1e-5)
        self.assertGreater(tail.trace(), 1e-4)
        np.testing.assert_allclose(record['unrepresented_covariance'], tail, atol=2e-14)
        np.testing.assert_allclose(np.asarray(record['weights']).sum(axis=0) + np.diag(tail),
                                   np.diag(record['covariance']), atol=2e-14)

    def test_invalid_refinement_inputs_rejected(self):
        for g, eta, nodes in ((0, 1, 10), (-1, 1, 10), (float('nan'), 1, 10),
                              (1, float('inf'), 10), (1, 1, 3), (1, 1, 10.5)):
            with self.assertRaises(ValueError):
                refined.angle_refined(g, eta, nodes)

    def test_exact_development_and_unrun_target_manifest(self):
        self.assertEqual(development.G_VALUES, (.10, .15, .20, .30, .50, .70, 1., 1.50, 2., 3.))
        expected = {f'{theory}:g={g}:eta={eta}' for theory in ('SU2', 'U1')
                    for g in ('0.125', '0.25', '0.40', '0.60', '0.85', '1.25', '2.50')
                    for eta in ('0', '0.5', '1')}
        self.assertEqual(set(development.target_ids()), expected)
        self.assertEqual(len(development.target_ids()), 42)


if __name__ == '__main__':
    unittest.main()
