# Rational certificate execution record

Date: 2026-09-09 UTC (2026-09-08 local). Instrument commit: `f9c1421`.
State: **unregistered; model bounds available; channel windows unresolved**.

## Completed development work

All 50 fixed character rungs completed in 78.4 seconds with no instrument
failures. Exact endpoint checks passed for every rung. Forty-nine rungs
provided the required isolated-vector/correlation bounds; 48 met the original
1e-6 scalar midpoint-radius budgets. The g=0.10, J=20 rung remained unresolved
for correlations, and its J=40 rung did not meet the scalar budget. Broad
cutoff bounds are retained instead of being replaced by adjacent-rung agreement.

At J=320, all ten cells meet the scalar budgets and establish a nonzero
first-gap overlap for both P and P^2 in the stated infinite character model.
These are development-model statements, not target results or field-theory
claims. The derivation and trusted arithmetic base are in [CERTIFICATES.md](CERTIFICATES.md).

## Finest-rung bounds

Gap radius is half the interval width divided by its positive lower endpoint,
maximized over the first three gaps. Vector distance is the largest aligned
normalized distance upper bound among the first four eigenvectors. The angle
column is the total entry-error upper bound normalized by a lower bound on the
true initial covariance scale, maximized over tau=4 and tau=8 and all matrix
entries at 4800 nodes. It is not a relative late-time error.

| g | Relative gap radius | Vector distance upper | Late-sample angle error upper |
| --- | ---: | ---: | ---: |
| 0.10 | 1.42e-14 | 1.98e-14 | 2.95e-10 |
| 0.15 | 1.42e-14 | 1.07e-14 | 2.29e-10 |
| 0.20 | 1.42e-14 | 6.68e-15 | 1.97e-10 |
| 0.30 | 1.42e-14 | 1.34e-14 | 1.52e-10 |
| 0.50 | 1.42e-14 | 1.47e-14 | 2.64e-10 |
| 0.70 | 1.44e-14 | 8.61e-15 | 1.61e-10 |
| 1.00 | 1.19e-14 | 7.17e-15 | 5.82e-11 |
| 1.50 | 6.15e-15 | 6.94e-15 | 8.00e-11 |
| 2.00 | 3.77e-15 | 3.42e-15 | 4.76e-11 |
| 3.00 | 2.21e-15 | 9.32e-16 | 7.36e-11 |

The exact character endpoint calculation supports much narrower intervals
than the earlier floating-point cross-method differences. This does not make
the angle calculation equally accurate: its total error is separately bounded
against the model correlation intervals.

At early positive times, retaining only three excited states leaves loose
tail allowances. At g=0.70 and tau=0.125, the finest-angle total error upper
bound is approximately 8.86e-4 on the initial-variance scale. This is a loose
bound, not an observed error of that size. It tightens substantially at later
times. These time-dependent bounds motivate a separate effective-gap/window
assessment rather than a global correlation success flag.

## Verification and provenance

Report: `certificates.json`. SHA-256:
`416b46c9eb363475b43cf83e33a64c68a2d0b95433fd85092e9e646b856eef5c`.
The report records the exact source/input hashes, rational endpoints,
hexadecimal candidate vectors, interval calculations, timings, and request
accounting. The archive audit replays every certificate and every angle error
bound from those values. It checks the document's report checksum as well.

All 49 numerical tests passed, including independent exact free-spectrum and
Taylor-series fixtures, zero-pivot Sturm cases, false endpoint/tail mutants,
sign invariance, nonfinite failure continuation, and full archived replay.
Source hashes were unchanged during execution; `git diff --check` passed.

No channel window has been selected. All 42 target rows remain unrun. The next
development iteration will propagate the correlation intervals through the
effective-gap estimator and retain unsupported windows explicitly. U(1),
remaining controls, source-pilot/registration prerequisites, and the incomplete
sieve review also remain outstanding.
