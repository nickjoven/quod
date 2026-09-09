# Later-time execution and window results

Date: 2026-09-09 UTC. Instrument commit: `5ef4f0a`.
State: **development window support established; unregistered; targets unrun**.

## Results

The unchanged ten couplings and four angle grids completed 80 direct
evolutions without failures, using 30 fresh ground solves and ten archived
finest-ground reads. Wall time was 164.3 seconds; BDF evolution time was
117.1 seconds. Every old sample was retained, and tau=12,16,20,24 were added.

At 4800 nodes, every coupling now has at least one common adjacent sampled
pair that qualifies for both P and P^2 under the conservative
mixture-plus-numerical gap-error budget. The earliest common pair in this
sample list is shown below. The last column is the larger bound for the two
observables, relative to the first gap's lower bound.

| g | Earliest common sampled tau pair | Combined relative gap-error upper |
| --- | --- | ---: |
| 0.10 | 4 to 8 | 3.26e-7 |
| 0.15 | 8 to 12 | 3.38e-8 |
| 0.20 | 8 to 12 | 1.08e-7 |
| 0.30 | 8 to 12 | 6.48e-7 |
| 0.50 | 12 to 16 | 2.64e-7 |
| 0.70 | 16 to 20 | 1.15e-7 |
| 1.00 | 12 to 16 | 3.20e-8 |
| 1.50 | 12 to 16 | 5.49e-8 |
| 2.00 | 12 to 16 | 4.71e-7 |
| 3.00 | 16 to 20 | 2.83e-8 |

These are development diagnostics for the stated single-angle model, with
the analytic/arithmetic trusted base of [CERTIFICATES.md](CERTIFICATES.md).
They do not establish windows at unsampled times or select registered target
inference settings. All grid/tolerance results and unsupported pairs remain
in the report. The original early-time failures are preserved in
`time-windows.json`, documenting why this extension was made.

## Verification

All 59 numerical tests passed, including exact replay of the extended
correlation certificates, total angle error bounds, and every window
assessment. The extension tests also verify the original time prefix,
fixed grids, explicit cache provenance, and continued execution after an
injected nonfinite result. Exact request accounting and unchanged source
hashes passed; `git diff --check` passed.

Report: `late-times.json`. SHA-256:
`be56f1a21e1217c3ad738cd2cbefeccece5eafc6f37d1279f3774c9fd79918ad`.
The report records all input and instrument source hashes, full correlation
matrices, rational bounds, solver work counts and timings. The archive test
checks this document's report checksum and recomputes the assessments.

## Remaining prerequisites

The SU(2) development work now has scalar certificates, overlap bounds,
independent angle propagation, and sampled effective-gap precision support.
All 42 target rows remain unrun and no registered window or target is selected.
U(1) with both parities, the remaining analytic controls, source-pilot
conventions, owning registration process and the incomplete sieve review
still require work before target selection can be the next decision.
