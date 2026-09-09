# U(1) development execution record

Date: 2026-09-09 UTC. Instrument commit: `4209587`; result commit: `20662f7`.
State: **unregistered; scalar agreement achieved; parity thresholds unresolved**.

## Execution

All ten development couplings completed five Fourier and four periodic-angle
rungs in 7.3 seconds without failures. These are 90 representation requests,
each solving two parity problems. Seven runtime calibration checks passed
and all four named mutants were rejected. All ten cells satisfy the unchanged
1e-6 scalar agreement goals across methods and adjacent final rungs.

The convention and Fourier cutoff ladder are explicit development choices
documented in [U1.md](U1.md), pending source-pilot verification. Both numerical
representations implement that same convention.

## Finest-rung comparisons

The first two gap columns are Fourier values. The discrepancy column covers
the first three even gaps. All quantities below are numerical readings,
not certified endpoints or accuracy bounds.

| g | Full gap | First even gap | Largest relative even-gap discrepancy |
| --- | ---: | ---: | ---: |
| 0.10 | 1.997496865 | 3.992486658 | 1.89e-8 |
| 0.15 | 1.994359062 | 3.983057070 | 3.66e-9 |
| 0.20 | 1.989949332 | 3.969783558 | 1.13e-9 |
| 0.30 | 1.977239080 | 3.931377827 | 2.06e-10 |
| 0.50 | 1.935365591 | 3.803081804 | 1.91e-11 |
| 0.70 | 1.868472366 | 3.588735076 | 1.78e-12 |
| 1.00 | 1.756849961 | 2.777398413 | 2.88e-12 |
| 1.50 | 2.385872295 | 2.550740091 | 3.18e-12 |
| 2.00 | 4.025832474 | 4.056868480 | 2.47e-12 |
| 3.00 | 9.002285510 | 9.005028252 | 2.41e-12 |

The largest relative full-gap discrepancy was 1.83e-9; the largest absolute
moment discrepancy was 1.03e-11. In each interacting cell the numerical
lowest odd excitation lies below the first even excitation. Both observables
preserve parity, so that odd excitation is invisible to them. Even-state
overlap uncertainty still has to be bounded before assigning a threshold.

## Verification and provenance

All 70 numerical tests passed, including complete parity embeddings, analytic
free dispersion and Haar moments, fourth-order convergence, wrong-measure and
periodic-boundary mutants, projection-edge accounting, failure continuation,
and source/comparison replay. Request accounting and unchanged source hashes
passed; `git diff --check` passed.

Report: `u1-development.json`. SHA-256:
`5e69d26ba7956cee3eeeb096b3db820e5b5b2a6d3ebccde96dbe6288c4d08888`.
The report contains all rung summaries, final even/odd spectra, ground vectors,
observable weights, numerical residuals, timings and source/environment hashes.
The archive regression test checks this document's report checksum and
recomputes the reported comparisons.

Local ignored ket packet:
`cf5b18461e8aeb20faba8a252d8f85b3cead33ecbbec31b4d49dcef1df812b8b`.
It parents the later-time/null-control packet and contains this instrument's
source, tests, report and documentation at result commit `20662f7`. Catbus
artifact validation passed and ket projection was clean. This paragraph was
added after packaging; no independent sieve verdict is claimed.

## Next prerequisite

Develop exact parity-specific spectral and overlap bounds, then direct U(1)
angle propagation and sampled gap-error assessment. The full gap and even
observable threshold must remain separate through those calculations.
All 42 target rows remain unrun. Source-pilot/registration and independent
review prerequisites remain outstanding; no target is selected.
