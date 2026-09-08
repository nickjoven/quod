# Preflight execution record

Date: 2026-09-08. Implementation commit: `ec10249bdafd498aa7d7f44ec39875fde300e31a`.

## Deterministic checks

`python3 scripts/vacuum_preflight.py --output research/vacuum-spectrum/preflight.json`
completed with exit 0, seven fixture checks true, four named mutants rejected,
42 unique target rows unrun and zero targets executed. A second execution to
`/tmp/quod-vacuum-preflight.json` compared byte-equal using `cmp`. Source
SHA-256 values were independently recomputed and matched. `git diff --check`
passed. This is exact preflight calibration only, not the proposed numerical study.

## Ket and catbus

Local store: `.ket/` (ignored; CIDs below require retaining this store).
Ket version: 0.3.0. Catbus executable SHA-256:
`c8ab7b1f2ab99dbd28f6cce10fe933eace6901aa9ac0cdd42762f425ae26c9c4`.

The four source/report artifacts were packed with catbus; packet node:
`5717d6d8414f2a0fe0c43adacd263f285cc0b63fa7f2a5ff2bd7cac5cc8596d6`.
`catbus validate --require-artifacts` returned `ok: true`.
`ket verify-projection` reported a clean projection.

## Sieve review remains incomplete

Sieve source revision: `863fdf2f5cb2986ff12db8f1f70a820cb3b796aa`.
Used `sieve-dims.json`, one worker, verification of all findings, catbus
handoff enabled, 120-second timeout per agent, and the default Claude agent.
Both attempts audited the implementation commit above.

| Attempt | Audit root | Result |
| --- | --- | --- |
| Sandboxed | `1eda197f4095d0fbb13dab3290246b4c6ab59dfa97dd7df699ade379b8c39acd` | Reviewer timed out after 120 seconds |
| Approved network retry, parented to first | `0ffae8bdd78ba026e440e04e1f448c00fafdf8841cdba31eb072cbf6d65f082c` | Reviewer timed out after 120 seconds |

Retry handoff: `98b12c634f7ecadc6e2fac97c588daa255598eade0e263b8fc46a11cb22628fe`.
Neither attempt returned findings or verification. Sieve exited zero and
reported `error: 0` despite the reviewer timeout; this is **not an audit pass**.
The raw timeout is retained by sieve in ket. No usage-limit response was
observed; reset requirements cannot be inferred from these timeouts.

## Next toolchain repair

Before relying on automated sieve acceptance, make reviewer failure an
explicit machine-readable count and non-success outcome, with a test using
a deliberately timing-out reviewer. This belongs in sieve, not in a numerical
comparison or a theorem status. Then rerun the scoped review with a working
reviewer. The independent numerical instrument remains the next research
implementation milestone described in README.md.
