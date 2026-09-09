# U(1) direct propagation execution

Date: 2026-09-09 UTC. Instrument commit: `6be1104`.
State: **unregistered; qualifying development samples; targets unrun**.

## Results

All 80 requested evolutions completed without instrument failures in 80.0
seconds. The 40 ground preparations comprise 30 fresh periodic parity solves
and 10 explicitly reused finest-grid grounds. Direct BDF evolution took
69.3 seconds; ground preparation took 0.18 seconds.

Every one of the ten development cells has a finest-grid sampled pair that
qualifies for both P and P^2. In particular, the dimensionless pair [20,24]
qualifies in all ten cells, with maximum combined relative bound below
3.82e-8, against the existing 1e-6 budget. This is an observed development
result, not selection or registration of a time window. Physical times are
scaled by each cell's archived first-even gap.

The reference is the **first even excitation**, whose overlap is certified
nonzero for both probes. The lower odd excitation determines the full model
gap and is invisible to these probes. Both intervals remain separately
labeled in the report. These results therefore do not estimate the full gap
from even-probe decay.

The combined bound adds the certified mixture-bias upper bound and the
numerical slope-error upper bound. The latter compares direct binary64
correlations against infinite-model intervals; tolerance agreement alone
is not used as an error certificate. Every adjacent sampled pair and every
coarser grid, including nonqualifying outcomes, remains in the archive.

## Verification and provenance

All 82 numerical tests passed. New checks cover the analytic periodic free
correlation, independent dense matrix exponential, explicit even-gap mapping,
calibration failure, continuation after nonfinite output, and archive replay
of every window and combined correlation bound. Input/source hashes and
request accounting passed. `git diff --check` passed.

Report: `u1-semigroup.json`. SHA-256:
`e44fe5c295b8fa1683ef397df5323c57de7013c381d629dd3a1402e5ef585c44`.
The archive test checks this checksum and recomputes the reported assessments.
The implementation and trusted-base limits are documented in
[U1-SEMIGROUP.md](U1-SEMIGROUP.md).

## Remaining prerequisites

Both theories now have development scalar comparisons, exact model
spectral/overlap bounds, direct propagation and qualifying sampled pairs.
The source-pilot convention, owning registration workflow and independent
review remain unresolved. No P/LC identifier or target has been chosen.
All 42 target cells remain unrun.
