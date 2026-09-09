# Later-time development extension

State: **unregistered; no target choice or execution**.

## Reason and fixed scope

The initial [time-window assessment](TIME-WINDOWS.md) found that the original
samples support both observable gap estimators only for g=0.10. This extension
adds tau=12,16,20,24 to the original eight samples, retaining every old sample
and the same ten eta=1 couplings and four angle grids. The original results
are preserved. These extra times are development tuning, not registered target
inference times.

The two BDF settings are (rtol,atol)=(1e-8,1e-18) and (1e-10,1e-20).
Absolute tolerance still applies to normalized observable-vector components.
The smaller absolute tolerance supports decaying signals at later times;
neither tolerance is interpreted as an error bound. Existing exact character
certificates supply the total sampled correlation-error bounds and the
conservative mixture-plus-numerical effective-gap assessment.

## Execution and reuse

The runner requests 80 evolutions over 40 angle rungs. It recomputes ground
vectors on the first three grids and reuses the archived finest refinement
ground at 4800 nodes. This is 30 fresh ground solves and ten explicit cache
reads. Every cached vector is checked against its archived source hashes,
grid size, normalization and eigenpair record; the independently assembled
matrix residual is retained. Reuse does not claim a fresh independent ground
solve. All 42 target rows remain unrun.

Times use the same finest-character gap as the original semigroup run.
The old prefix must match bit-for-bit. The new binary64 times are interpreted
as exact dyadic rationals when evaluating the certificate. Every direct result
retains the full 2-by-2 correlation matrix, solver work counts and status.
Failures remain explicit and later independent evolutions continue.

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_late_time_run.py --output research/vacuum-spectrum/late-times.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_late_time*.py' -v
```

## Interpretation

All adjacent sample pairs are assessed separately for both observables and
all grids. A qualifying pair satisfies the documented development gap-error
budget with certified nonzero overlap. It is not a registration decision,
an assertion about unsampled times, or target selection. At very late times,
numerical error can grow relative to the shrinking signal; those failures
are retained even if an earlier pair qualifies.

The single-angle operator assumptions and arithmetic trusted base of
[CERTIFICATES.md](CERTIFICATES.md) still apply. U(1), remaining controls,
source-pilot conventions, registration and review remain separate prerequisites.
