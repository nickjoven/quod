# Autonomous development status

## Authorized boundary

The user approved autonomous development iteration, including method choices,
implementation, verification and small commits, until a target must be chosen.
No target is selected or executed. A required external input may block progress
earlier, but optional implementation choices do not require renewed approval.

## Verified progress

| Prerequisite | Evidence |
| --- | --- |
| Independent SU(2) scalar representations | `REFINEMENT-RUN.md`: all ten fixed cells pass scalar agreement |
| Ordered model spectral and overlap bounds | `CERTIFICATES-RUN.md`: exact tail/endpoint certificates and residual propagation |
| Independent angle correlations | `SEMIGROUP-RUN.md`: full direct propagation, two tolerances, fixed ladders |
| Sampled gap precision for both observables | `LATE-TIMES-RUN.md`: qualifying sampled pairs for every finest-grid development cell |
| Hidden, tensor, gapless, disconnected nulls | `NULL-CONTROLS.md`: exact analytic controls and analysis mutants |
| U(1) Fourier and periodic-angle representations | `U1-RUN.md`: both parities; 90 requests; scalar agreement in all ten cells |
| U(1) exact parity and overlap bounds | `U1-CERTIFICATES-RUN.md`: all 50 rungs replayed; all ten finest rungs meet scalar and overlap budgets |
| U(1) direct correlations and sampled gaps | `U1-SEMIGROUP-RUN.md`: 80 evolutions; every finest development cell has qualifying pairs for both even probes |
| Consolidated schema and replay | `READINESS.md`: twenty development cells; target authorization disabled; external gates unresolved |
| Artifact lineage | Latest validated ket packet is recorded in `READINESS.md` |

The tests replay archived sources, exact endpoints, overlaps, correlation
intervals, effective-gap bounds and target accounting. The latest full run
passed 87 tests, including exact parity, propagation, window and readiness replay.
Certificates concern the stated single-angle model and its documented trusted
arithmetic/analytic base, not a registered field-theory conclusion.

## Next work and unresolved inputs

The recovered [experiment specification](DESIGN-ALIGNMENT.md) reveals that
existing U(1) results use a different kinetic coefficient and cutoff ladder.
The earlier readiness report remains a historical audit, not a qualification
of the recovered specification.

1. Corrected U(1) scalar development comparisons are complete in
   [U1-DESIGN-RUN.md](U1-DESIGN-RUN.md): coefficient 4 g^2, cutoffs 40..640,
   all 90 requests and all ten scalar-agreement cells. Regenerate certificates
   and direct window assessment for these new results.
2. Add the exact null families specified by the recovered draft and reproduce
   its original fourteen-lesson query. Retain earlier controls as additional cases.
3. Obtain the separate `ym-gap-pilot-artifacts.zip`, whose expected hashes
   are now recorded in the recovered handoff, to verify pilot replication.
4. Obtain P/LC assignment through the owning workflow, address independent
   review, and freeze future work before any target execution.
5. Stop for the user's target decision only when it is the next required step.
   All 42 target rows remain unrun in every current report.
