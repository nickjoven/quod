# SU(2) development instrument

State: **unregistered development run; every target remains unrun**.
This implements the first two numerical representations of the supplied
proposal. It does not complete the registration prerequisites.

## Reproduce and check liveness

The tested dependencies are pinned in `requirements.txt` (Python 3.10).
From the repository root:

```sh
python3 scripts/vacuum_development.py --calibration-only --output /tmp/vacuum-calibration.json
python3 scripts/vacuum_development.py --output /tmp/vacuum-development.json
python3 -m unittest discover -s scripts -p 'test_vacuum_development.py' -v
```

Flushed JSON events mark every completed rung and cell. The report is
atomically checkpointed after each rung; all requested development cells
are present as pending before solving. Exceptions become explicit failure
rows, later cells continue, and the final exit code is nonzero if any cell
failed. Exit zero means execution completed, **not** precision resolved.
`--calibration-only` executes no interacting development ladder.
There is no command-line coupling or target-execution option.

`development.json` retains all 90 rung summaries, final ground vectors,
energies, spectral weights and cross weights, covariance matrices, error
diagnostics, runtime library versions and source SHA-256 hashes. The test
suite audits those hashes and row coverage to detect drift. Ground vectors
use Euclidean normalization in both representations: angle entries are
approximately sqrt(h) times the normalized transformed wavefunction phi.

## Independent representations

The character Hamiltonian has n = 2j, diagonal g²n(n+2), and off-diagonal
-eta/g². It uses a full finite ordered eigenbasis at J = 20, 40, 80, 160,
320 (dimension 2J+1). Applying P adds one character coefficient; applying
P² adds two. Moment and covariance multiplication retains this padding
before projecting. The excluded observable Gram matrix is retained, so the
finite spectral sum is not incorrectly equated to an unprojected variance.

The angle Hamiltonian discretizes -g²phi'' - g²phi - 2eta cos(x)phi/g²
with centered second differences and zero endpoint values. It uses 600,
1200, 2400, 4800 interior points and computes the first four ordered
eigenpairs. Multiplication by cos(x) and cos²(x) is diagonal on this grid.
The cosine operators use phi's probability weight; flat weighting of psi
is tested as a deliberate wrong-Haar mutant. The specified grid counts
form a refinement ladder but do not have exactly nested nodes, since
their spacings are pi/(N+1).

Both representations call SciPy's tridiagonal eigensolver; their operators
and discretizations are independent, their eigensolver library is shared.
The angle output retains the covariance not represented by the first three
excited states. It is a finite-grid spectral-weight accounting quantity,
not an infinite-dimensional error certificate. Neither representation
reports an asymptotic channel threshold or discards a small overlap.

## Error diagnostics and interpretation

| Field | Meaning | Limitation |
| --- | --- | --- |
| solver_residual_first_four | Euclidean norm of Hv-Ev in the finite matrix | Does not certify the ordering or continuum eigenvalue |
| outside_basis_residual_first_four | Magnitude of the missing character hopping component | Not a cutoff eigenvalue enclosure; tiny components may round to zero |
| observable_projection_tail_gram | Exact arithmetic expression for omitted padded observable components | Evaluated in floating point |
| finite_basis_sum_rule_defect | Spectral covariance discrepancy after accounting for padding | Internal completeness check, not independent spectroscopy |
| adjacent_rung_difference | Absolute moment and relative gap differences | Numerical convergence evidence only |
| leading_h2_mesh_error_estimate | Adjacent difference divided by ((h_coarse/h_fine)²-1) | Assumes leading second-order behavior; not an enclosure |
| cross_method_difference | Final character/angle discrepancies | Not an upper bound on either method's error |

No separate quadrature bound or certified mesh bound is available; both
are explicitly null in angle records. `numerical_goal_met` requires every
final cross-method and adjacent-rung moment difference <= 1e-6 and gap
relative difference <= 1e-6. This deliberately conservative convergence
flag is not a detection rule. Every cell remains `unresolved` because
overlap and temporal error budgets are also outstanding.

## Calibration and regression coverage

Eight numerical calibration checks cover the free character spectrum and
moments, exact second-difference free eigenvalues, Haar measure, centering,
energy shifts, spectral completeness with padding, and target coverage.
Four named mutants use the actual solver outputs or measure computation:
flat-psi second moment, omitted centering, absolute shifted E1, and a
deleted target row. Tests also check the free channel selection rule,
cutoff-edge projection, an interacting cross-method comparison, duplicate
rows, and injected failure followed by a successfully executed unresolved
cell. Calibration tolerance 1e-9 is a floating-point regression tolerance,
not a registered physical threshold or rigorous error bound.

## Observed development result

Ten g values (0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 1.00, 1.50, 2.00,
3.00), all eta=1, completed without solver failures. At g=0.10 the largest
relative discrepancy among the first three gaps is approximately 2.38e-5;
the first character gap is approximately 3.987467769. Across all cells,
the largest absolute moment discrepancy is approximately 1.32e-7.
Six cells satisfy the final cross-method 1e-6 gap comparison, but none
satisfy the stricter combined adjacent-rung convergence flag. The result
is a development accuracy limitation, not gap closure or target evidence.

## Next work

Use these development results to derive and validate a more accurate angle
discretization or controlled extrapolation within the fixed cost ladder.
Do not widen the proposed tolerance. Then add independent angle semigroup
evaluation, overlap uncertainty, per-cell temporal windows, the remaining
analytic nulls, and U(1) with both parities. The source pilot, lessons query,
registration workflow and frozen error budget remain prerequisites before
target execution. The previous sieve reviewer timeouts remain unresolved;
ket/catbus packaging does not substitute for that review.
