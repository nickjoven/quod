# Independent angle semigroup development instrument

State: **unregistered; targets unavailable; channel windows unresolved**.

## Method and independence

For the fourth-order Dirichlet angle matrix H and normalized ground u, form
the two columns B_a = (O_a - <O_a>)u for O = (cos(x), cos(x)^2). Evolve

```text
dY/dt = -(H - E0 I)Y,  Y(0) = B
C(t) = B^T Y(t).
```

`vacuum_semigroup.py` assembles H using the sparse Dirichlet Laplacian and
its exact square. This is separate from the band-storage implementation.
SciPy's BDF integrator evolves both columns with a constant sparse Jacobian.
Each column is normalized before integration and restored afterwards, so the
absolute integration tolerance applies to normalized vector components.
See the pinned [SciPy solve_ivp documentation](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.integrate.solve_ivp.html)
for BDF, sparse Jacobians, and local tolerance semantics.

Propagation does not use excited eigenvectors or reconstruct a four-state
spectral sum. Ground preparation uses the existing banded eigensolver, and
both methods still use SciPy and floating-point arithmetic. This is independent
propagation, not an independent ground solver or library implementation.
All four entries of C are retained without forcing symmetry or positivity.

## Fixed development manifest and time samples

The existing ten SU(2) couplings at eta=1 are unchanged. Character cutoffs
are J = 20, 40, 80, 160, 320; angle interiors are 600, 1200, 2400, 4800.
There are 50 character solves, 40 angle preparations, and 80 BDF evolutions.
Every angle rung uses (rtol, atol) = (1e-8, 1e-11) and (1e-10, 1e-13).

Dimensionless samples are tau = 0, 0.125, 0.25, 0.5, 1, 2, 4, 8.
Within each cell t = tau / Delta_character, using the finest character first
ordered gap to set the same physical times for every rung. This clock choice
does not assert that either observable couples to that gap. The samples are
diagnostics; none is an accepted detection window.

The character comparison sums every available excited state, including signed
cross weights. Its omitted projection-tail Gram matrix remains in the record.
The angle four-state sum is also recorded, separately from direct propagation,
to expose omitted-state contributions. Their difference includes propagation
and eigenpair error and is not itself a certified omitted-spectrum bound.

## Diagnostics and error limits

Each comparison retains absolute differences and differences divided by
sqrt(C_character(0)_aa C_character(0)_bb). This fixed variance scale avoids
division by vanishing or sign-changing cross correlations. It is not the
relative error in a late-time correlation.

The report separates tolerance refinement, adjacent mesh rungs, adjacent
character cutoffs, and finest-character comparison. It also retains symmetry
defects, minimum eigenvalues of the symmetric part of C, initial covariance
consistency, centering residuals, independent matrix ground residuals, and
integration work counts. Negative eigenvalues or asymmetry are not clipped.

BDF tolerances control local error estimates; their values and refinement
differences do not enclose global correlation error. Ground uncertainty,
overlap uncertainty, mesh, quadrature, and spectral tails have not been combined
into a validated budget. `integration_error_bound`, usable windows, and
thresholds remain null. There is no numerical flag that assigns a channel.

## Execute and verify

From the repository root with the pinned numerical environment:

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_semigroup_run.py --output research/vacuum-spectrum/semigroup.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

The runner preallocates every request, atomically checkpoints before and after
solves, and emits flushed progress events. Nonfinite outputs and integration
failures are recorded; independent later requests continue. A failed finest
character reference explicitly prevents that cell's angle evolutions. Exit zero
means execution completed with exact accounting and unchanged source hashes.
Calibration failure leaves all unexecuted requests visible and exits nonzero.
All 42 target rows remain unrun; there is no target execution interface.

Analytic free correlations use the exact finite-grid dispersion and Haar
coefficients 1/4 and 1/16. Additional checks use a dense full-spectrum reference,
a dense matrix exponential, energy offsets, clock scaling, a free continuum
limit, signed cross weights, omitted-state contributions, missing centering,
invalid inputs, and injected solver/nonfinite failures. Small calibration grids
are analytic fixtures, not replacement development rungs.
