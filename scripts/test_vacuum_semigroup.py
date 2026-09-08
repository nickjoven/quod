"""Independent references and adversarial controls for direct angle evolution."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from scipy.linalg import eigh, expm

import vacuum_development as baseline
import vacuum_semigroup as semigroup
import vacuum_semigroup_run as runner


class SemigroupTests(unittest.TestCase):
    def test_analytic_dense_offset_and_clock_calibrations(self):
        result = semigroup.calibration()
        self.assertTrue(result["pass"], result)

    def test_direct_exponential_and_omitted_states(self):
        matrix, observables = semigroup.angle_matrix(.7, 1, 24)
        record = semigroup.angle_refined(.7, 1, 24)
        vectors = semigroup.centered_vectors(record["ground"], observables)
        times = np.array([0., .1, .5, 1.])
        actual = np.asarray(semigroup.propagate(matrix, record["E0"], vectors, times)["correlations"])
        expected = np.array([vectors.T @ expm(-t * (matrix.toarray() - record["E0"] * np.eye(24))) @ vectors
                             for t in times])
        np.testing.assert_allclose(actual, expected, atol=2e-10, rtol=2e-8)
        truncated = semigroup.spectral_correlations(record, times)
        self.assertGreater(np.max(abs(actual - truncated)), 1e-6)
        np.testing.assert_allclose(actual[0] - truncated[0], record["unrepresented_covariance"], atol=1e-14)
        # A centering mutant leaves a nondecaying ground contribution.
        uncentered = np.asarray(record["ground"])[:, None] * observables
        mutant = np.asarray(semigroup.propagate(matrix, record["E0"], uncentered, times)["correlations"])
        self.assertGreater(np.max(abs(mutant[-1] - actual[-1])), .01)

    def test_signed_cross_spectral_sum(self):
        amplitudes = np.array([[.2, -.3], [.4, .1]])
        record = {"energies": [0., 1., 2.], "weights": (amplitudes**2).tolist(),
                  "cross_weights": np.prod(amplitudes, axis=1).tolist()}
        times = np.array([0., 1., 3.])
        expected = np.array([amplitudes.T @ np.diag(np.exp(-t * np.array([1., 2.]))) @ amplitudes for t in times])
        actual = semigroup.spectral_correlations(record, times)
        np.testing.assert_allclose(actual, expected, atol=1e-16)
        self.assertLess(actual[-1, 0, 1], 0)

    def test_free_continuum_limit_on_fixed_first_rung(self):
        # Analytic preparation avoids relying on the eigenvector solver here.
        n, g = 600, .5
        matrix, obs = semigroup.angle_matrix(g, 0, n)
        h = np.pi / (n + 1)
        ground = np.sqrt(2 / (n + 1)) * np.sin(np.arange(1, n + 1) * h)
        lam = 4 * np.sin(h / 2)**2 / h**2
        e0 = g**2 * (lam + h**2 * lam**2 / 12 - 1)
        times = np.asarray(semigroup.TAU) / (3 * g**2)
        actual = np.asarray(semigroup.propagate(matrix, e0, semigroup.centered_vectors(ground, obs), times)["correlations"])
        np.testing.assert_allclose(actual[:, 0, 0], .25 * np.exp(-3 * g**2 * times), atol=2e-9)
        np.testing.assert_allclose(actual[:, 1, 1], .0625 * np.exp(-8 * g**2 * times), atol=2e-9)
        np.testing.assert_allclose(actual[:, 0, 1], 0., atol=2e-12)

    def test_invalid_and_failed_evolution(self):
        matrix, obs = semigroup.angle_matrix(.5, 0, 8)
        _, v = eigh(matrix.toarray())
        vectors = semigroup.centered_vectors(v[:, 0], obs)
        for times in ([0., float("nan")], [0., 0.], [1., 2.], [0., -1.]):
            with self.assertRaises(ValueError):
                semigroup.propagate(matrix, 0., vectors, times)
        for tolerance in (float("nan"), 0., -1.):
            with self.assertRaises(ValueError):
                semigroup.propagate(matrix, 0., vectors, [0., 1.], rtol=tolerance)
        failed = SimpleNamespace(success=False, message="injected solver failure")
        with patch.object(semigroup, "solve_ivp", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "injected solver failure"):
                semigroup.propagate(matrix, 0., vectors, [0., 1.])
        bad = vectors.copy()
        bad[-1, -1] = np.nan
        with self.assertRaises(ValueError):
            semigroup.propagate(matrix, 0., bad, [0., 1.])

    def test_fixed_manifest(self):
        self.assertEqual(baseline.G_VALUES, (.1, .15, .2, .3, .5, .7, 1., 1.5, 2., 3.))
        self.assertEqual(baseline.CHARACTER_J, (20, 40, 80, 160, 320))
        self.assertEqual(baseline.ANGLE_INTERIORS, (600, 1200, 2400, 4800))
        self.assertEqual(semigroup.TAU, (0., .125, .25, .5, 1., 2., 4., 8.))
        self.assertEqual(semigroup.TOLERANCES, ((1e-8, 1e-11), (1e-10, 1e-13)))

    def test_failure_continues_and_accounts_for_nonfinite_result(self):
        calls = []
        original = semigroup.propagate

        def injected(*args, **kwargs):
            calls.append(1)
            result = original(*args, **kwargs)
            if len(calls) == 2:
                result["correlations"][-1][-1][-1] = float("nan")
            return result

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(baseline, "G_VALUES", (.1, .5)), \
                    patch.object(baseline, "CHARACTER_J", (20, 40)), \
                    patch.object(baseline, "ANGLE_INTERIORS", (16, 32)), \
                    patch.object(semigroup, "calibration", return_value={"pass": True}), \
                    patch.object(semigroup, "propagate", side_effect=injected), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
                report = json.loads(output.read_text())
                self.assertTrue(runner.accounting(report))
                bad = copy.deepcopy(report)
                bad["cells"][0]["rungs"].pop()
                self.assertFalse(runner.accounting(bad))
            self.assertEqual(len(calls), 8)
            self.assertEqual([c["status"] for c in report["cells"]], ["failure", "unresolved"])
            failed = report["cells"][0]["rungs"][2]["evolutions"][1]
            self.assertEqual(failed["status"], "failure")
            self.assertNotIn("result", failed)
            self.assertEqual(len(report["targets"]), 42)
            self.assertTrue(all(t["status"] == "unrun" for t in report["targets"]))

    def test_calibration_failure_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(semigroup, "calibration", side_effect=RuntimeError("injected")), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output), 1)
            report = json.loads(output.read_text())
            self.assertEqual(report["state"], "instrument_failure")
            self.assertEqual(len(report["cells"]), 10)
            self.assertIn("injected", report["calibration"]["reason"])


if __name__ == "__main__":
    unittest.main()
