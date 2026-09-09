# U(1) direct propagation and sampled time windows

## Scope and operator

This development instrument uses the convention in [U1.md](U1.md), which
remains unverified against the missing source pilot. It evolves centered
cos(theta) and cos(theta)^2 vectors with the full periodic fourth-order
angle matrix. The sparse BDF action reuses `vacuum_semigroup.propagate`;
excited eigenpairs are not used to construct the propagated correlation.

The full gap is odd in these certified development cells. Reflection-even
probes instead see the first even excitation. `window_reference` explicitly
maps the certified even gaps and overlaps into the shared time-window
estimator; the full gap remains a separately labeled report field.

## Fixed development requests

All ten existing g values at eta=1 use periodic grids 600, 1200, 2400, 4800.
Two tolerance settings, (rtol,atol)=(1e-8,1e-18) and (1e-10,1e-20), give
80 requested evolutions. Thirty ground preparations are fresh parity solves;
ten finest-grid grounds are reused from the source-hashed U(1) archive.
The report labels each origin and measures centered-vector parity defects.

The sampled dimensionless times are 0, .125, .25, .5, 1, 2, 4, 8, 12, 16,
20, 24, scaled by the numerical finest Fourier first-even gap. The physical
times are copied from the exact certificate archive, preserving their binary64
values. This is development timing, not a registered window.

## Error assessment and controls

Both direct diagonal correlations and signed cross correlations are compared
with the certified infinite-model intervals. The shared effective-gap
assessment bounds mixture bias and numerical slope error separately against
the first-even gap. Their conservative sum must meet the existing 1e-6
relative budget and the relevant overlap must exclude zero. Only adjacent
sampled pairs can qualify; no unsampled interval is inferred.

Tolerance differences and Fourier comparison are diagnostics, not certified
integration errors. The combined error bound instead compares each stored
binary64 output to both endpoints of the exact model interval. Failure and
unresolved states remain visible; failed evolutions do not cancel later requests.

The free periodic calibration checks analytic discrete dispersion and Haar
variances over the same time span with rtol=1e-10, atol=1e-13. A trial at
atol=1e-20 stalled and was interrupted before production; the calibration
uses the established shared calibration tolerance instead. Interacting
production retains the two declared tighter settings. Tests also compare a
small interacting matrix against an independent dense matrix exponential,
reject a missing parity prerequisite, and inject nonfinite evolution output.

## Reproduction

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_u1_semigroup_run.py --output research/vacuum-spectrum/u1-semigroup.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

Inputs and all computational dependencies are SHA-256 checked. The instrument
records timings, solver diagnostics, full accounting and every target as unrun.
The arithmetic/analytic trusted base remains that of [U1-CERTIFICATES.md](U1-CERTIFICATES.md).
Registration and independent review are outstanding.
