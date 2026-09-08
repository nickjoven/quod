# Same-cell SU(2) refinement

State: **unregistered development instrument; 42 targets unrun**.
This refinement keeps the ten development couplings, eta=1, and all
previously specified cutoff and grid rungs. It adds a fourth-order angle
method and audits the original second-order results using exact-spacing
Richardson extrapolation. It does not change the 1e-6 goals.

## Run and inspect liveness

From the repository root, with the existing pinned NumPy/SciPy environment:

```sh
python3 scripts/vacuum_refinement.py --output /tmp/vacuum-refinement.json
python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

The runner checkpoints its JSON report before and after each solve and
prints flushed `rung_started`, `rung_completed`, and `cell_completed`
events. All requests are present before execution. There are 130 requested
solves: five character rungs, four second-order angle rungs, and four
fourth-order angle rungs for each development cell. Rung durations are
retained so the increased computational cost is visible.

Each failed solve has an explicit reason; remaining requests continue.
Nonfinite results are rejected before entering the checkpoint. Exact row
accounting and unchanged source hashes are required for successful completion.
Exit zero means execution completed. It does not mean channel resolution or
a validated numerical error budget. No target-execution option exists.

## Three-agent contributions

1. Angle implementation: `vacuum_angle_refined.py` uses SciPy's symmetric
   banded eigensolver to compute the first four ordered eigenpairs of a
   fourth-order Dirichlet operator. It retains residuals, orthogonality,
   spectral weights, unrepresented covariance and the normalized ground.
2. Error audit: `vacuum_convergence.py` derives signed Richardson corrections
   and observed orders using the actual spacing pi/(N+1). Its read-only
   audit of the original report is in `REFINEMENT-AUDIT.md` and
   `refinement-audit.json`.
3. Regression audit: `test_vacuum_refinement_contract.py` checks the exact
   free dispersion, Haar convention, boundary mutant, clock/offset identities,
   cutoff covariance tails and fixed manifests. `REFINEMENT-REVIEW.md`
   records its scope and the baseline NaN finding.

The integrated runner is in `vacuum_refinement.py`; its separate tests
exercise nonfinite and failed-rung handling, calibration failure,
archived-source drift and complete accounting. Original development source
and results remain intact for comparison.

## Fourth-order operator and independent checks

Let L be the usual positive Dirichlet second-difference matrix, with
diagonal 2/h² and nearest off-diagonal -1/h². The new kinetic operator is
g²(L + h²L²/12 - I). The same diagonal cosine potential is added.
The interior stencil is pentadiagonal. Forming L² exactly gives endpoint
diagonals 29/(12h²) in place of the interior 30/(12h²).

This closure uses the odd extension at the endpoints. For the cosine
potential the Dirichlet eigenfunctions have a smooth odd extension;
the Schrödinger equation implies phi''=0 at each endpoint. Simply setting
exterior ghost values to zero is a different, incorrect closure. The
regression suite deliberately introduces that bug and observes failures
in the exact free spectrum and Haar moment checks.

For free sine mode k, lambda_k = 4 sin²(kh/2)/h², so its exact discrete
energy is g²(lambda_k + h²lambda_k²/12 - 1). This supplies an independent
finite-grid identity. Interacting comparisons against the character
method test discretization agreement. The methods still share SciPy and
floating-point arithmetic; they are not independent library implementations.

## What agreement means

The original second-order discrepancy is consistent with mesh error:
the read-only audit finds observed gap orders near two, and its finest
Richardson extrapolates agree with character gaps within about 2.02e-9.
The fourth-order method tests that explanation with a different finite
operator, rather than only extrapolating the original readings.

`numerical_goal_met` requires all final character/fourth-order differences
and both methods' final adjacent-rung differences to be <=1e-6 (absolute
for all five moments; relative for all three gaps). Raw differences,
signed extrapolations, observed orders and solver residual scales remain
separate fields. Missing or nonfinite values cannot pass that flag.

Residuals and observed convergence are not certified continuum error
bounds. At fine meshes and larger g, the matrix norm grows as g²/h² and
roundoff can dominate the remaining mesh difference. A missing or irregular
observed order in that regime is retained, not forced to four. Tiny
cross-method discrepancies do not justify corresponding accuracy digits.

Every cell remains `unresolved`: overlap uncertainty, usable temporal
windows, independent angle semigroup evaluation, and a validated complete
error budget are still outstanding. No physical or continuum conclusion
is registered. The source pilot, lessons workflow and P/LC assignment
process also remain external prerequisites.

## Evidence and remaining review

`refinement.json` archives the integrated run with source SHA-256 values,
environment, complete requests and full final observable records. Tests
verify the archived source hashes and manifests. The companion
`REFINEMENT-RUN.md` records aggregate results and ket/catbus provenance.
These agent reviews are not a completed sieve run; the earlier sieve
reviewer timeouts remain documented in `RUN.md`.
