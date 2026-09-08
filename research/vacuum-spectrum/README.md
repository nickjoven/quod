# Vacuum–spectrum preflight

Date: 2026-09-08. Task: `ym-vacuum-gap-litcheck`.
State: **unregistered; 42 target cells unrun; no P or LC identifier**.

## Purpose and boundary

This is the first executable prerequisite for the supplied two-axis study.
It is separate from quod's Lean claim ledger: no result here discharges a
demonstrandum or changes `claims/millennium/yang_mills.yml`.
The inspected base `addeb4e` has neither the referenced LITCHECK draft,
pilot solver, `scripts/tools/lessons.py`, nor the proposed P/LC assignment
workflow. The lesson IDs and archived pilot convention cannot yet be
verified here. No lessons-tool execution is claimed.

## Check liveness

From the repository root:

```sh
python3 scripts/vacuum_preflight.py --output research/vacuum-spectrum/preflight.json
```

The command emits flushed `started` and `completed` JSON events, exits
nonzero on a failed check, and atomically replaces its report. It requires
only Python's standard library. This short command finishes synchronously;
it is not a background research worker. The report includes source SHA-256
hashes so source changes are visible on rerun, not a registration lock.

Exact rational character multiplication checks free SU(2) observable
coefficients, vacuum centering, a cutoff-edge path, and energy-offset
invariance. Four synthetic analysis mutants must break their named check:
wrong Haar second moment, omitted centering, absolute E1, missing target.
These are fixture-level comparator checks, not mutations of a numerical
solver. They establish no discretization accuracy or spectral detection.

The generated manifest enumerates SU(2) and U(1), each with g = 0.125,
0.25, 0.40, 0.60, 0.85, 1.25, 2.50 and eta = 0, 0.5, 1. Every row is
explicitly unrun. There is no target execution entry point.

## Build next: development-only independent instrument

1. Obtain the source pilot and registration workflow; rerun the actual
   lessons query there. Preserve the supplied draft as design provenance.
2. Implement the SU(2) character tridiagonal Hamiltonian and independently
   discretized Dirichlet angle operator. Use the ten development g values
   from the proposal at eta=1; free eta=0 cells are analytic calibration.
   Compute polynomial multiplication before projection. Retain full ordered
   eigenpairs or explicit omitted-weight bounds.
3. Add U(1) Fourier and periodic-angle implementations with both parities.
   Distinguish full gap from even-observable threshold. Add the remaining
   offset, clock, hidden-state, tensor-sum, gapless and disconnected controls.
4. Derive residual, truncation, mesh, quadrature and overlap error estimates
   on the fixed ladders. Price per-cell temporal windows and an independent
   angle semigroup evaluation. Treat rung agreement as numerical evidence,
   not a rigorous enclosure. Retain unresolved overlaps and cells explicitly.
5. Freeze the complete result schema, target manifest, error formulas and
   source hashes; allocate identifiers through the owning repository's
   process and commit registration before any target execution.

Acceptance for the next milestone: independent development spectra and
moments with separately reported errors; spectral-weight/variance and
projection-edge checks; all declared nulls; four solver-level named mutants
rejected; failure and unresolved paths exercised; no target execution.
The proposed 1e-6 budgets remain goals until development evidence supports
them. No finite-model output implies a continuum gap or a lower bound.

## Evidence toolchain

Use an isolated ignored `.ket` store in this checkout. Archive the report
and source with `catbus pack --file`, then `catbus validate --require-artifacts`.
The checked-in `sieve-dims.json` scopes a real sieve review to this preflight.
An unavailable reviewer or failed review must remain a recorded failure;
successful packaging does not imply scientific review passed.
