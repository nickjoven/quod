# Same-cell refinement execution record

Date: 2026-09-08. Integrated runner commit: `ce0c70b`; result commit: `e1d6a55`.
State: **unregistered; numerical agreement achieved; channels unresolved**.

## Completed work

Three agents contributed independent angle implementation, convergence
analysis, and adversarial regression checks. Their commits are `21551f9`,
`450da5b`, `2e3c9e3`, and the fixed-ladder test follow-up `f1e3ba4`.
The integrator added finite-data guards, full request accounting and
checkpointing, then ran the complete unchanged development manifest.

The run completed 130 solves in approximately 166 seconds wall time
(153 seconds measured inside solvers). Ten calibration checks and all
four named analysis mutants passed. The complete numerical test suite
passed **24 tests**. Source hashes were unchanged during execution,
exact row accounting passed, and `git diff --check` passed.

All ten cells meet the unchanged 1e-6 cross-method and adjacent-rung
agreement checks. All ten remain unresolved for channel interpretation;
all 42 target rows remain unrun. There were no solver failures.

## Final character/fourth-order comparisons

| g | Largest relative gap difference | Largest absolute moment difference | Largest relative gap residual scale |
| --- | ---: | ---: | ---: |
| 0.10 | 1.78e-9 | 3.97e-12 | 5.58e-11 |
| 0.15 | 3.47e-10 | 1.82e-12 | 1.91e-10 |
| 0.20 | 1.08e-10 | 2.36e-13 | 3.05e-10 |
| 0.30 | 1.87e-11 | 1.28e-12 | 1.07e-9 |
| 0.50 | 3.22e-11 | 5.04e-12 | 3.80e-9 |
| 0.70 | 4.96e-11 | 4.40e-11 | 1.04e-8 |
| 1.00 | 1.03e-10 | 6.79e-11 | 2.31e-8 |
| 1.50 | 8.96e-11 | 3.65e-11 | 2.54e-8 |
| 2.00 | 5.07e-10 | 4.91e-10 | 2.75e-8 |
| 3.00 | 1.24e-10 | 6.87e-11 | 2.59e-8 |

Gap differences cover the first three ordered gaps. Moment differences
cover the five specified vacuum components. Residual scale means
(r0+rk)/gap_k for the finite fourth-order matrix; it is not a rigorous
continuum bound. Its size relative to the smaller discrepancies prevents
interpreting those discrepancies as accuracy to 9–11 digits.

At g=0.10 the maximum raw second-order gap discrepancy was 2.38e-5;
the new fourth-order discrepancy is 1.78e-9 on the same finest grid.
The separate Richardson audit of the old results agrees with this mesh-error
interpretation. No claim about a continuum gap follows.

## Evidence and limits

Local ignored ket store: `.ket/`. Catbus packet node:
`cf1f5e1b647f6816b4274c114d5ac41e9ffd6cb69619f52547158f67d3f5167c`.
It parents the prior development packet and includes the new source,
tests, results, audit and method documentation. Catbus validation with
`--require-artifacts` passed; ket projection was clean.

The full runner report contains per-rung timings, source hashes, library
versions, complete final observable records and convergence diagnostics.
The original development report is preserved. Sieve was not rerun after
its two prior reviewer timeouts; the three-agent review does not stand in
for a completed sieve verdict. No usage-limit response or reset requirement
was observed.

Next numerical prerequisites are a validated combined error budget,
overlap uncertainties, and independent angle semigroup/time-window checks.
They remain separate from these successful scalar agreement checks.

## Resumed evidence audit

The follow-up [evidence audit](EVIDENCE-AUDIT.md) verifies archived source
hashes and recomputes final and adjacent-rung agreement without new solves.
Its machine-readable report is `evidence-audit.json`. It inventories the
missing error-budget components and specifies the next semigroup check;
it does not resolve channels or replace the outstanding sieve review.
