# Completion monitor for the existing registered run

The user explicitly instructed continuation after reviewing the U(1) runtime
bottleneck. The original numerical process remains unchanged. This monitor
adds no solver, restart, timeout, tolerance adjustment, sample, or refinement.
It is postprocessing automation, not a replacement registration.

## Completion path

The committed `completion-monitor.json` pins the monitor, its tests, the report
postprocessors, their tests, and report dependency versions. The monitor also
checks the original registration and source/dependency pins. It polls the
existing process and operational index every 30 seconds without imposing a
runtime limit. An exclusive lock prevents duplicate monitors.

Only a terminal index accounting for all 42 selected cells can start:

1. Registered full evidence replay, including every checkpoint and outcome.
2. Exact selected-result summary, with full gaps distinct from probe thresholds.
3. Single-document report generation.
4. The complete vacuum regression suite.
5. Scoped commit and push of the verified generated artifacts and raw evidence.

A failed check, unexpected process exit, source drift, existing finalization
artifacts, or publication failure stops the monitor and records the reason.
It never silently retries finalization, overwrites raw evidence, restarts the
original run, or turns an interruption into a numerical failure. Another
process with a different invocation is not accepted as the original solver.

`/tmp/quod-vacuum-completion-monitor/status.json` records monitor status;
`selected-run/completion-validation.txt` retains final verification and test
output when finalization starts. The earlier live snapshot remains historical.
The existing independent review covers 21 SU(2) cells. A completed automatic
report does not silently extend that human/agent review to U(1).

The original pilot is permanently unverifiable. This workflow cannot produce
a uniform Yang–Mills gap proof from finite-rotor results.

## Publication and validation

The monitor pins the attached branch, origin fetch/push destinations, and
upstream. It rejects destination or checkout drift, stages and commits only
explicit result paths, and pushes explicitly to the pinned origin branch.
Existing unrelated staged work prevents publication. Eleven focused tests cover
terminal gating, drift, failure retention, command ordering, and publication.
The full pre-launch transcript is retained in `completion-monitor-validation.txt`.

After its specification is committed, the monitor is launched against the
existing host process ID, with that full monitor commit supplied. It must run
with visibility of the original process and access to the already authorized
Git remote. Its status file is the authority for whether automatic finalization
is waiting, complete, or needs attention; it does not replace the numerical
run's operational index.
