# Readiness against the recovered experiment design

## Current numerical evidence

Provenance update: the user confirmed the original pilot script and results
are lost. [PILOT-DISPOSITION.md](PILOT-DISPOSITION.md) supersedes recovery
requests below. The archived audit remains unchanged; its unresolved pilot
status now means unverifiable due to source loss. Current development evidence
is the reproducible baseline, subject to review and future registration.

`design-readiness.json` supersedes the earlier readiness snapshot for the
recovered specification. It consolidates ten SU(2) development cells and
ten corrected U(1) cells, preserving full-gap versus observable-threshold
intervals, nonzero overlaps, scalar budget checks and all qualifying common
sampled pairs. It neither registers a window nor authorizes target execution.
All twenty development cells qualify under the existing model assumptions.

The audit replays exact certificates, derived gaps, scalar budgets, combined
correlation error bounds and window assessments, using the corrected U(1)
coefficient 4g^2 and cutoffs 40..640. It reproduces both the original and
specified analytic null reports and verifies the recovered bundle and both
lessons queries. Computational sources, inputs, schema, design and recovery
verifiers are hashed. Historical artifacts remain unchanged.

The development result schema is in `design-readiness.schema.json` and uses
the existing JSON Schema validator. Exact semantic relations and request
accounting are checked in the audit. This reviewable schema is still a draft;
a final target result schema must support exact-zero selection rules and
failed/unresolved outcomes across all deformations before registration.

## Requirement audit

| Requirement | Current evidence | Disposition |
| --- | --- | --- |
| Fixed operator conventions and ladders | Recovered draft plus SU(2) and corrected U(1) sources | Implemented and checked on development cells |
| Spectral ordering, parity and padded moments | Exact certificate replay and representation tests | Checked on fixed development ladders |
| Combined error and nonzero overlap bounds | Corrected certificate and direct-evolution archives | Qualified at finest development rungs; coarse misses retained |
| Per-cell temporal analysis | Sampled mixture-plus-numerical slope intervals | Qualifying development pairs; no registered target windows |
| Named analytic null families | `design-nulls.json` and retained legacy controls | Specified families reproduced |
| Solver mutants and failure accounting | Numerical regression suite | Checks separate solver bugs from analytic premise controls |
| Lessons consultation | Exact fourteen-ID draft query reproduced from pinned tool/ledger | Reproduced; clauses still belong in eventual registration |
| Target-domain cost estimate | `TARGET-COST-PLAN.md` | Measured-development scenarios only, no precision guarantee |
| Original pilot replication | Handoff supplies expected archive/script/JSON hashes; one quoted scalar matches | Incomplete: original code/JSON still missing |
| P/LC assignment and registration | Owning process recovered | Incomplete: no assigned IDs or registration commit |
| Independent review | Earlier reviewer timeouts remain failures | Incomplete |
| Target result contract and derive checks | `RESULT-CONTRACT.md`: draft, development adaptations and free selection tests | Implemented for review; owner freeze before execution remains incomplete |
| Target choice/execution | 42 manifest rows explicitly unrun | User boundary preserved; not yet the next required step |

The numerical qualification is about the specified single-angle models,
not a continuum field-theory gap. This audit cannot retroactively register
completed development work. The remaining missing input is the separate
`ym-gap-pilot-artifacts.zip`; P/LC assignment and independent review also
remain required external steps.

## Reproduction

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_design_readiness.py --output research/vacuum-spectrum/design-readiness.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

The regression reproduces the full audit and rejects changed provenance,
missing requests, target execution and false external-completion claims.

Validation: all 117 numerical tests passed, including the corrected audit
and cost-plan rejection checks. `git diff --check` passed.

Audit commit: `b1f233f`; cost-plan commit: `3ac7166`. Validated packet:
`e0ddf5c12f4bcf211bbb2a5e91ab3b1e2dbc411b7e5725ced55ac0ff0097785a`.
Artifact validation passed and ket projection was clean. The packet retains
the document before this provenance paragraph, avoiding self-reference.
