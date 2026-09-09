# Sampled effective-gap assessment

State: **unregistered development diagnostic; no target selected**.

## Criterion

For each observable's positive diagonal correlation and adjacent samples
t1<t2, define the effective gap

```text
alpha = log(C(t1)/C(t2)) / (t2-t1).
```

The exact correlation intervals from `certificates.json` enclose alpha.
Monotonicity of log gives the lower endpoint from C(t1).lower/C(t2).upper
and the upper endpoint from C(t1).upper/C(t2).lower. Rational inputs are
converted outward to Decimal; the correctly rounded logarithms are expanded
by one adjacent representable number and converted back to rationals.
This follows the [Decimal.ln rounding contract](https://docs.python.org/3.10/library/decimal.html#decimal.Decimal.ln).
An independent rational series for ln(2) tests the implementation.

An exact positive spectral mixture supported at gaps >=Delta1 has
alpha>=Delta1. Its relative mixture-bias upper bound is therefore
max(0, alpha.upper-Delta1.lower)/Delta1.lower. The archived angle entries
give a second effective-gap interval with only outward logarithm rounding.
The greatest distance between the two intervals, divided by Delta1.lower,
bounds the numerical error in that estimator.

A sampled pair qualifies as a **development precision diagnostic** only if:

1. Its first-gap overlap is certified nonzero.
2. Both required model correlation intervals and angle observations are positive.
3. The sum of the mixture-bias and numerical-error upper bounds is <=1e-6.

The 1e-6 is the existing gap-precision goal, now applied explicitly to this
estimator. The sum avoids accepting accidental cancellation between numerical
error and higher-state contamination. This does not register an inference
rule for targets, establish an interval of unsampled times, or select a target.
Both observables are assessed separately at every existing angle rung.

## Initial assessment

The read-only instrument is `scripts/vacuum_time_windows.py`. Its inputs are
the archived certificates and original semigroup run, whose hashes and source
provenance are checked. All seven adjacent pairs on the original tau ladder
0, 0.125, 0.25, 0.5, 1, 2, 4, 8 are retained, including failures.

At 4800 nodes, only g=0.10 has a qualifying pair for both observables, namely
tau=4 to tau=8. P also has qualifying pairs for g=0.15, 0.20, 1.50, 2.00,
and 3.00, but P^2 does not. No pair qualifies for either observable at g=0.30,
0.50, 0.70, or 1.00. A nonzero first overlap does not by itself make the
earlier samples sufficient for extracting that gap.

This motivates a separate development extension to later samples and tighter
propagation tolerances. The old report and its times remain unchanged, so the
reason for that extension is preserved. No target cell is evaluated.

The [later-time execution record](LATE-TIMES-RUN.md) reports the completed
extension and its sampled precision support for all ten development cells.

## Reproduce

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_time_windows.py --output research/vacuum-spectrum/time-windows.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_time_windows*.py' -v
```

The report is deterministic. It contains exact rational bounds and both
failure reasons and qualifying pair indices. Source/input checksums and an
archive reproduction test detect drift.
