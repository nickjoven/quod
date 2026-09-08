"""Independent fourth-order angle discretization for development/calibration.

For L = tridiag(-1,2,-1)/h**2 with Dirichlet endpoints, use
K = g**2 * (L + h**2 * L@L/12 - I).  Forming L@L exactly gives
endpoint diagonal 29/12 instead of the interior 30/12.  This is the odd
Dirichlet extension, not a five-point stencil with zero exterior ghosts.
The smooth cosine potential and zero endpoint values admit a smooth odd
extension of the eigenfunctions; in particular phi'' vanishes at endpoints.
Thus the boundary closure preserves fourth-order consistency.  The free
sine-mode eigenvalues are known exactly and tested independently.

Only four ordered eigenpairs are returned.  Spectral tails, mesh error, and
quadrature errors are not certified.  No target runner is supplied here.
"""
import numpy as np
from scipy.linalg import eig_banded

from vacuum_development import observable_data


def angle_refined(g, eta, interiors):
    """Return the existing observable record plus finite-matrix diagnostics."""
    if g <= 0 or not np.isfinite(g) or not np.isfinite(eta):
        raise ValueError("g must be positive finite and eta finite")
    if not isinstance(interiors, (int, np.integer)) or interiors < 4:
        raise ValueError("at least four integer interior nodes required")
    h = np.pi / (interiors + 1)
    x = np.arange(1, interiors + 1) * h
    scale = g**2 / h**2
    d = np.full(interiors, 2.5 * scale - g**2) - 2 * eta / g**2 * np.cos(x)
    d[[0, -1]] -= scale / 12
    off = np.full(interiors - 1, -4 * scale / 3)
    off2 = np.full(interiors - 2, scale / 12)
    # Lower band storage: ab[k,j] = H[j+k,j].
    ab = np.zeros((3, interiors))
    ab[0] = d
    ab[1, :-1] = off
    ab[2, :-2] = off2
    e, v = eig_banded(ab, lower=True, select="i", select_range=(0, 3))
    if v[np.argmax(abs(v[:, 0])), 0] < 0:
        v[:, 0] *= -1
    obs = np.column_stack((np.cos(x), np.cos(x)**2))
    applied = v[:, :1] * obs
    record = observable_data(e, v, applied, applied.T @ applied)
    hv = d[:, None] * v
    hv[:-1] += off[:, None] * v[1:]
    hv[1:] += off[:, None] * v[:-1]
    hv[:-2] += off2[:, None] * v[2:]
    hv[2:] += off2[:, None] * v[:-2]
    row_sums = abs(d)
    row_sums[:-1] += abs(off)
    row_sums[1:] += abs(off)
    row_sums[:-2] += abs(off2)
    row_sums[2:] += abs(off2)
    norm_upper = float(max(row_sums))
    residual = np.linalg.norm(hv - v * e, axis=0)
    record.update({
        "method": "angle_dirichlet_fourth_order", "interiors": interiors,
        "spacing": float(h), "formal_mesh_order": 4,
        "solver_residual_first_four": residual.tolist(),
        "solver_relative_residual_first_four": (residual / (norm_upper + abs(e))).tolist(),
        "finite_matrix_norm_upper": norm_upper,
        "orthogonality_defect": float(np.linalg.norm(v.T @ v - np.eye(4), ord=2)),
        "omitted_spectrum": "all states above index 3; unrepresented covariance retained",
        "quadrature_error_bound": None, "mesh_error_bound": None,
        "boundary_closure": "exact square of Dirichlet L; odd extension",
    })
    return record
