# Development execution provenance

Date: 2026-09-08. Solver implementation commit: `8490937`.
Source SHA-256 values and exact library versions are in `development.json`.
See `DEVELOPMENT.md` for methods, results, limitations and reproduction.

## Executed checks

- Ten eta=1 development cells, five character rungs and four angle rungs
  each: 90 solves completed; zero solver failures.
- Eight calibration checks passed; all four named mutants rejected.
- Seven unittest checks passed, including archived source/coverage audit
  and an injected solver failure that did not prevent the next cell running.
- All ten cells remain unresolved; all 42 target rows remain unrun.
- `git diff --check` passed.

## Evidence packet

Local ignored store: `.ket/`. Catbus packet node:
`6e82501a23ffd70ee6a23323fcdc282e326b28b9961dd02cc11e7b89af7bc131`.
It parents the initial preflight packet and attaches the numerical source,
tests, development report, method documentation and dependency pins.
Catbus validation with `--require-artifacts` passed; ket projection was clean.

Sieve was not rerun in this leg: the previous sandboxed attempt and approved
network retry both timed out. No independent sieve verdict covers these
changes. See `RUN.md` for the retained failure roots and the identified
reviewer-failure accounting problem. No usage-limit response was observed.
