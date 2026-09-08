# Development mesh refinement audit

Date: 2026-09-08. State: unregistered numerical diagnostics. This audit reads
only the ten existing eta=1 development cells and executes no Hamiltonian
solves. All 42 targets remain unrun. It supplies no resolved spectral
channel, registered tolerance or rigorous error enclosure.

## Finding

The existing angle data exhibit second-order gap convergence. Applying
signed Richardson extrapolation to the finest two existing rungs reduces
the maximum relative discrepancy from the character spectrum to 2.02e-9.
The maximum absolute moment discrepancy becomes 4.98e-11. The original
weak-coupling discrepancy is therefore consistent with the expected
second-difference mesh error, rather than a different spectrum convention.
These discrepancies are not estimates of total accuracy.

| g | Largest relative extrapolated gap discrepancy | Largest absolute extrapolated moment discrepancy |
| --- | ---: | ---: |
| 0.10 | 2.01e-9 | 3.85e-12 |
| 0.15 | 3.97e-10 | 1.66e-12 |
| 0.20 | 1.26e-10 | 9.71e-13 |
| 0.30 | 3.59e-11 | 2.46e-13 |
| 0.50 | 3.71e-11 | 1.93e-12 |
| 0.70 | 7.32e-11 | 1.02e-11 |
| 1.00 | 4.30e-10 | 4.98e-11 |
| 1.50 | 1.56e-10 | 3.82e-12 |
| 2.00 | 2.05e-10 | 5.82e-12 |
| 3.00 | 1.06e-10 | 2.59e-11 |

All final three-rung observed gap orders lie between approximately 1.99966
and 2.00097. Moment order diagnostics should be inspected separately:
a tiny moment difference can make its fitted order noise dominated.

## Exact-spacing derivation

For Q(h) = Q(0) + a h^p + higher terms, the signed correction to the fine
rung is (Q_f - Q_c)/((h_c/h_f)^p - 1). Add this correction to Q_f to obtain
the extrapolate. Use h = pi/(N+1); the listed N ladder is not exactly
nested, so replacing the spacing ratio by 2 introduces avoidable error.
The original mesh estimate already used the correct ratio, but stored
only correction magnitudes and did not test observed orders.

For three rungs h0 > h1 > h2 solve

```text
(Q0-Q1)/(Q1-Q2) = (h0^p-h1^p)/(h1^p-h2^p).
```

The diagnostic returns no observed order if either difference vanishes,
their signs disagree, or no root exists in the diagnostic interval
0.1 <= p <= 8. That interval is not an acceptance tolerance. Positive
order alone does not prove an asymptotic expansion or bound its remainder.

## Residual and acceptance discipline

The finest angle residual scale (r0 + rk)/abs(Ek-E0) reaches 3.63e-9 over
these gap comparisons, already larger than some extrapolate discrepancies.
Finite symmetric matrix residuals locate nearby eigenvalues in exact
arithmetic, but assigning them to ordered levels and extending the claim
to the continuum operator needs additional arguments. Floating residual
arithmetic and cancellation in E0 subtraction also require accounting.
Richardson extrapolation amplifies its input errors: for ratio R=(hc/hf)^p,
the fine and coarse coefficients have magnitudes R/(R-1) and 1/(R-1).
Propagate those factors in any later declared solver budget. No 9–11 digit
accuracy claim follows from the small differences above.

Retain the proposed 1e-6 absolute moment and 1e-6 relative gap goals.
A development convergence assessment should retain signed rung differences,
observed orders, changes between successive extrapolates, independent
character discrepancies, character cutoff diagnostics, and solver residual
scales separately. A future frozen numerical budget must allocate solver,
mesh/remainder, cutoff and observable/quadrature contributions; it must not
silently replace these with agreement against a chosen reference. Agreement
and consistency within a proposed budget can be recorded now; a validated
error-budget decision remains separate. None of these scalar diagnostics
establishes overlap signs, operator coverage or a usable temporal window.

## Reproduce and verify drift

```sh
python3 scripts/vacuum_convergence.py --output /tmp/refinement-audit.json
python3 -m unittest discover -s scripts -p 'test_vacuum_convergence.py' -v
```

The checked-in `refinement-audit.json` contains all component diagnostics,
input and script SHA-256 hashes, and explicit limitations. Tests reproduce
the report, verify both hashes, and check signed extrapolation for exact
second/fourth-order synthetic sequences, non-nested spacings, invalid
meshes, flat sequences and sign reversals. The reusable API is
`convergence_diagnostics(records, order=2.0)`; it accepts coarse-to-fine
records containing `spacing`, `moments`, and `first_three_gaps`. It reports
diagnostics without making an acceptance decision.
