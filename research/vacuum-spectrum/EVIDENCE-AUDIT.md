# Refinement evidence and error-budget readiness

Date: 2026-09-08. State: **unregistered; all ten channels unresolved**.

## Reproduce the audit

From the repository root in the pinned numerical environment:

```sh
python3 scripts/vacuum_evidence_audit.py --output research/vacuum-spectrum/evidence-audit.json
python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

The audit reads the archived refinement without running solvers. It verifies
the recorded solver source hashes, complete development/rung/target accounting,
and final eigenvalue and ground-vector consistency. It recomputes scalar
agreement from final observables and the last two rungs instead of trusting
success flags. Its JSON records the input and audit-script checksums.
Tests reject source drift, a false agreement flag caused by changed rung data,
and a target row marked completed.

The archived evidence contains 130 completed solves and ten scalar-agreement
passes. All 42 targets remain unrun. This verifies local source provenance;
it does not revalidate the ket packet or complete sieve review.

## Error-budget dependencies

| Component | Available evidence | Still required |
| --- | --- | --- |
| Eigensolver | First four residuals and orthogonality diagnostics | Propagation through isolated eigenspaces to observable uncertainties |
| Character cutoff | Adjacent rungs, outside-basis residuals, projection-tail Gram matrix | Validated truncation and overlap bounds |
| Angle mesh | Fourth-order ladder and independent character agreement | Validated mesh enclosure; rung differences alone are insufficient |
| Quadrature | Discrete moments agree across methods | A quadrature error estimate; archived bound is null |
| Spectral overlap | Low-state weights and full omitted covariance matrix | Weight uncertainty intervals, including near-zero overlaps |
| Temporal window | Ordered gaps and spectral weights | Independent angle semigroup evaluation with propagation and tail errors |

Finite-matrix residual scales and omitted covariance are retained per cell in
the audit. Neither is relabeled as a continuum enclosure or a validated overlap
uncertainty. The audit deliberately makes no channel-readiness decision.

## Next numerical step

Implementation follow-up: [the semigroup instrument](SEMIGROUP.md) now supplies
direct angle propagation and its development runner. Its execution and remaining
error-budget limits are recorded in [SEMIGROUP-RUN.md](SEMIGROUP-RUN.md).

Implement an angle-space action of the centered semigroup on both observable
vectors, independent of the four-eigenpair spectral reconstruction. First test
it against analytic free correlations, energy-offset invariance, and a small
finite-matrix full-spectrum reference. Then compare it with the character
spectral sum on the existing development ladders, retaining full 2-by-2
correlations and explicit solver failures. Time samples must remain diagnostics
until propagated overlap, omitted-spectrum, mesh, and quadrature errors support
a usable window. No target execution or threshold assignment follows from this
audit.
