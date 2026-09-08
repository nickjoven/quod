"""Direct sparse angle evolution for development-only correlation diagnostics.

The BDF action uses the full finite angle operator, not its excited eigenpairs.
Ground preparation still uses the existing banded eigensolver. Integration
tolerances and their refinement differences are not certified error bounds.
"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigh
from scipy.sparse import diags, eye, kron

from vacuum_angle_refined import angle_refined

TAU = (0., .125, .25, .5, 1., 2., 4., 8.)
TOLERANCES = ((1e-8, 1e-11), (1e-10, 1e-13))


def angle_matrix(g, eta, interiors):
    """Assemble via the sparse Dirichlet square, independently of band storage."""
    if not np.isfinite(g) or g <= 0 or not np.isfinite(eta):
        raise ValueError("g must be positive finite and eta finite")
    if isinstance(interiors, bool) or not isinstance(interiors, (int, np.integer)) or interiors < 4:
        raise ValueError("at least four integer interior nodes required")
    h = np.pi / (interiors + 1)
    x = np.arange(1, interiors + 1) * h
    laplace = diags((-np.ones(interiors - 1), 2 * np.ones(interiors),
                     -np.ones(interiors - 1)), (-1, 0, 1), format="csc") / h**2
    hamiltonian = g**2 * (laplace + h**2 / 12 * (laplace @ laplace) - eye(interiors))
    hamiltonian += diags(-2 * eta / g**2 * np.cos(x))
    return hamiltonian.tocsc(), np.column_stack((np.cos(x), np.cos(x)**2))


def centered_vectors(ground, observables):
    ground = np.asarray(ground, dtype=float)
    observables = np.asarray(observables, dtype=float)
    if (ground.ndim != 1 or observables.shape != (len(ground), 2)
            or not np.isfinite(ground).all() or not np.isfinite(observables).all()
            or abs(ground @ ground - 1) > 1e-9):
        raise ValueError("invalid ground or observables")
    applied = ground[:, None] * observables
    return applied - ground[:, None] * (ground @ applied)


def propagate(hamiltonian, e0, vectors, times, rtol=1e-10, atol=1e-13):
    """Return B.T exp[-t(H-E0)] B without excited-state reconstruction.

    Each initial column is normalized for integration and restored afterwards.
    Absolute tolerances therefore apply to normalized vector components.
    """
    vectors = np.asarray(vectors, dtype=float)
    times = np.asarray(times, dtype=float)
    if (vectors.ndim != 2 or vectors.shape[1] != 2
            or hamiltonian.shape != (len(vectors), len(vectors))
            or not np.isfinite(vectors).all() or not np.isfinite(hamiltonian.data).all()
            or not np.isfinite(e0) or not np.isfinite([rtol, atol]).all()
            or rtol <= 0 or atol <= 0):
        raise ValueError("invalid evolution inputs")
    if (times.ndim != 1 or len(times) < 2 or times[0] != 0
            or not np.isfinite(times).all() or not (np.diff(times) > 0).all()):
        raise ValueError("times must start at zero and strictly increase")
    norms = np.linalg.norm(vectors, axis=0)
    if not (norms > 0).all():
        raise ValueError("zero observable vector")
    generator = -(hamiltonian - e0 * eye(len(vectors), format="csc"))
    jacobian = kron(eye(2), generator, format="csc")
    solution = solve_ivp(lambda t, y: jacobian @ y, (0., times[-1]),
                         (vectors / norms).ravel(order="F"), method="BDF",
                         jac=jacobian, t_eval=times, rtol=rtol, atol=atol)
    if (not solution.success or solution.status != 0
            or solution.y.shape != (vectors.size, len(times))
            or not np.array_equal(solution.t, times) or not np.isfinite(solution.y).all()):
        raise RuntimeError("incomplete/nonfinite BDF evolution: " + solution.message)
    evolved = np.stack([y.reshape(vectors.shape, order="F") * norms for y in solution.y.T])
    correlations = np.einsum("ni,tnj->tij", vectors, evolved)
    if not np.isfinite(correlations).all():
        raise RuntimeError("nonfinite correlations")
    return {"correlations": correlations.tolist(), "rtol": rtol, "atol": atol,
            "nfev": solution.nfev, "njev": solution.njev, "nlu": solution.nlu,
            "message": solution.message,
            "max_symmetry_defect": float(np.max(abs(correlations - correlations.transpose(0, 2, 1)))),
            "minimum_symmetric_eigenvalue": float(np.linalg.eigvalsh(
                (correlations + correlations.transpose(0, 2, 1)) / 2).min()),
            "initial_covariance_defect": float(np.max(abs(correlations[0] - vectors.T @ vectors))),
            "integration_error_bound": None}


def spectral_correlations(record, times):
    """Full available spectral sum, including signed off-diagonal weights."""
    energies = np.asarray(record["energies"])
    weights = np.asarray(record["weights"])
    cross = np.asarray(record["cross_weights"])
    decay = np.exp(-np.outer(times, energies[1:] - energies[0]))
    result = np.empty((len(times), 2, 2))
    result[:, 0, 0] = decay @ weights[:, 0]
    result[:, 1, 1] = decay @ weights[:, 1]
    result[:, 0, 1] = result[:, 1, 0] = decay @ cross
    if not np.isfinite(result).all():
        raise ValueError("nonfinite spectral correlations")
    return result


def comparison(a, b, covariance):
    """Absolute and variance-normalized differences, safe at zero cross-weight."""
    delta = abs(np.asarray(a) - np.asarray(b))
    variances = np.diag(covariance)
    if not np.isfinite(delta).all() or not np.isfinite(variances).all() or not (variances > 0).all():
        raise ValueError("invalid correlation comparison")
    normalized = delta / np.sqrt(np.outer(variances, variances))
    return {"absolute": delta.tolist(), "variance_normalized": normalized.tolist(),
            "max_absolute": float(delta.max()), "max_variance_normalized": float(normalized.max())}


def calibration():
    """Small analytic and dense full-spectrum fixtures; never target cells."""
    g, n = .5, 32
    hamiltonian, observables = angle_matrix(g, 0, n)
    x = np.arange(1, n + 1) * np.pi / (n + 1)
    ground = np.sqrt(2 / (n + 1)) * np.sin(x)
    h = np.pi / (n + 1)
    lam = 4 * np.sin(np.arange(1, 4) * h / 2)**2 / h**2
    energies = g**2 * (lam + h**2 * lam**2 / 12 - 1)
    times = np.asarray(TAU) / (3 * g**2)
    vectors = centered_vectors(ground, observables)
    direct = np.asarray(propagate(hamiltonian, energies[0], vectors, times)["correlations"])
    exact = np.zeros_like(direct)
    exact[:, 0, 0] = .25 * np.exp(-(energies[1] - energies[0]) * times)
    exact[:, 1, 1] = .0625 * np.exp(-(energies[2] - energies[0]) * times)
    free_error = float(np.max(abs(direct - exact)))
    hamiltonian, observables = angle_matrix(.7, 1, n)
    energies, eigenvectors = eigh(hamiltonian.toarray())
    ground = eigenvectors[:, 0]
    vectors = centered_vectors(ground, observables)
    times = np.asarray(TAU) / (energies[1] - energies[0])
    direct = np.asarray(propagate(hamiltonian, energies[0], vectors, times)["correlations"])
    amplitudes = eigenvectors.T @ vectors
    exact = np.einsum("ki,tk,kj->tij", amplitudes,
                      np.exp(-np.outer(times, energies - energies[0])), amplitudes)
    shifted = propagate(hamiltonian + 7 * eye(n), energies[0] + 7, vectors, times)
    clocked = propagate(2 * hamiltonian, 2 * energies[0], vectors, times / 2)
    prepared = angle_refined(.7, 1, n)
    ground_residual = float(np.linalg.norm(hamiltonian @ np.asarray(prepared["ground"])
                                          - prepared["E0"] * np.asarray(prepared["ground"])))
    metrics = {"free_discrete_correlation": free_error,
               "dense_full_spectrum": float(np.max(abs(direct - exact))),
               "energy_offset": float(np.max(abs(direct - shifted["correlations"]))),
               "clock_scaling": float(np.max(abs(direct - clocked["correlations"]))),
               "independent_matrix_ground_residual": ground_residual}
    checks = {name: value < 2e-9 for name, value in metrics.items()}
    return {"pass": all(checks.values()), "checks": checks, "max_absolute_errors": metrics,
            "tolerance": 2e-9, "scope": "finite-matrix calibration, not continuum certification"}
