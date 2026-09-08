# Direct angle semigroup execution record

Date: 2026-09-08. Instrument commit: `0488a5b`; result commit: `187bf89`.
State: **unregistered; independent propagation completed; channels unresolved**.

## Results

All ten development couplings completed the unchanged cutoff/grid ladders:
50 character spectral solves, 40 angle ground preparations, and 80 direct BDF
evolutions. There were no solver failures. Wall time was 168.2 seconds;
recorded spectral/ground solve time was 152.6 seconds and BDF time was 8.8
seconds. The command set `OPENBLAS_NUM_THREADS=1`. The environment was Python
3.10.12, NumPy 2.2.6, and SciPy 1.15.3.

The five runtime calibration checks passed. The complete numerical suite
passed 37 tests, including independent dense-exponential and analytic checks,
injected failure/nonfinite paths, exact manifests, and archived-source and
comparison reproduction. Exact request accounting and unchanged source hashes
passed; `git diff --check` passed.

## Finest-angle correlation comparisons

Every entry below is the maximum over all eight time samples and all four
matrix entries, normalized by sqrt(C_character(0)_aa C_character(0)_bb).
These are variance-normalized differences, not relative late-time errors.
The angle result uses the tighter propagation tolerance. The mesh column
compares 2400 and 4800 interior nodes; the tolerance column compares the two
BDF tolerances at 4800 nodes. Definitions and fixed times are in [SEMIGROUP.md](SEMIGROUP.md).

| g | Character difference | Adjacent mesh difference | Tolerance difference | Four-state reconstruction difference |
| --- | ---: | ---: | ---: | ---: |
| 0.10 | 8.66e-10 | 3.98e-09 | 3.98e-08 | 7.66e-10 |
| 0.15 | 5.87e-10 | 7.81e-10 | 3.68e-08 | 5.63e-10 |
| 0.20 | 4.51e-10 | 2.70e-10 | 2.93e-08 | 5.56e-10 |
| 0.30 | 2.63e-10 | 5.21e-11 | 1.21e-08 | 9.67e-08 |
| 0.50 | 1.69e-10 | 5.55e-11 | 4.95e-09 | 1.45e-04 |
| 0.70 | 1.42e-10 | 1.65e-10 | 4.36e-09 | 1.49e-03 |
| 1.00 | 2.24e-10 | 1.99e-10 | 7.42e-09 | 8.17e-05 |
| 1.50 | 3.77e-10 | 1.53e-10 | 2.05e-08 | 1.99e-07 |
| 2.00 | 8.32e-10 | 7.50e-10 | 1.73e-08 | 2.04e-09 |
| 3.00 | 5.94e-10 | 1.55e-10 | 3.53e-08 | 6.31e-10 |

The largest finest-angle/character absolute entry difference was 1.04e-10.
Across all angle rungs and both tolerances, the largest raw symmetry defect
was 1.91e-14; the smallest eigenvalue of the symmetric part was 1.08e-16.
These are observed diagnostics, without a certified error allowance.

Direct propagation captures contributions omitted by the three excited states
in the four-eigenpair reconstruction. The largest discrepancy in the table is
at g=0.70, approximately 1.49e-3 on the variance scale. At small discrepancies,
propagation and eigenpair error also contribute; no discrepancy here is
relabeled as a rigorous tail bound.

## Interpretation and next prerequisite

The independent angle evolution and character spectral sum agree closely on
these diagnostic samples. The propagation tolerance differences are larger
than the finest cross-method differences, so those smaller differences do not
establish matching accuracy digits. Local BDF tolerances do not certify global
correlation error. The shared ground solver is another limitation on independence.

All ten cells retain null usable windows and thresholds. All 42 target rows
remain unrun. Next, derive and validate a combined error budget that propagates
ground/eigenspace uncertainty to overlaps and correlations, includes mesh and
quadrature uncertainty, and controls omitted-spectrum and integration errors.
Only then can the sampled time intervals be assessed as usable channel windows.
No continuum spectral conclusion or registration follows from this run.

## Results and provenance

`semigroup.json` contains complete correlation matrices, per-rung comparisons,
timings, source SHA-256 values, calibration results, and failure accounting.
Report SHA-256:
`cd80964e402ab10f4ca85131bd3e6ca5c29a676f4cbb0e949e3f7b4f9790fe1e`.
The archive regression test checks this document's report checksum, current
solver sources, and recomputes all stored comparison arrays.

Local ignored ket store: `.ket/`. Catbus packet node:
`1c6c67155b049f520e1f8413866ab292ca9d447481799725a665e75b1fd283dc`.
It parents the prior refinement packet and includes the semigroup source,
tests, results, method/run documentation at result commit `187bf89`, and
the intervening evidence audit. `catbus validate --require-artifacts` passed;
`ket verify-projection` reported a clean projection. This provenance paragraph
was added after packaging to avoid a self-referential packet checksum.

Sieve was not rerun. The prior reviewer timeouts remain outstanding; this
numerical run and its tests do not constitute a completed sieve verdict.
