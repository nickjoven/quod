# Development readiness record

## Scope

`readiness.json` consolidates the twenty fixed development cells across SU(2)
and U(1). It is a reviewable draft record, not a registration lock. The
schema explicitly prohibits registered windows and target authorization.
The 42 target rows remain unrun; this instrument has no target solver.

The record distinguishes the full ordered model gap from the observable
threshold. U(1) even probes see the first even excitation, while its certified
full gap is odd. SU(2) uses the first ordered excitation. Gap intervals are
rational endpoint strings; common qualifying pairs are zero-based indices
into each theory's archived twelve-sample time array. All qualifying pairs
are retained, without choosing a registered window.

## Verification

The audit checks source and input hashes, exact development request accounting,
all archived spectral/vector/overlap certificates, derived gap intervals,
finest-rung scalar radius budgets, cross-representation scalar agreement,
combined correlation error bounds and sampled effective-gap assessments.
It reproduces the analytic null report. Existing solver-level calibration
and failure tests remain in the full numerical suite; the audit does not
rerun the 80 time evolutions or treat a provenance packet as scientific review.

Schema constraints live in `readiness.schema.json`, validated with the existing
JSON Schema library. Exact arithmetic, cross-field relations, target identity
coverage and certificate replay remain semantic checks in the audit. The
schema describes this unregistered development record; a future registered
result requires the owning workflow and an explicitly reviewed schema change.

```sh
python3 -m pip install -r research/vacuum-spectrum/requirements-readiness.txt
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_readiness.py --output research/vacuum-spectrum/readiness.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

The deterministic report pins its input archives, audit source and schema.
The archive regression test reproduces it and rejects changed provenance,
missing requests, target execution and false external-completion claims.
The source archives retain their original historical limitations; this
consolidation supplies the current cross-archive view without rewriting them.

## Outstanding requirements

Execution evidence: all twenty development cells qualified in the consolidated
replay; all 87 numerical tests passed. `git diff --check` passed.
Result commit: `622931e`. Validated packet:
`cea7a92965892dc119ddb383245af3addf062e6e0cb4d52cf9a7911c860cf6e6`.
Artifact validation passed and ket projection was clean. The packet includes
this document before the execution paragraph, avoiding self-reference.

| Requirement | Evidence needed | Current state |
| --- | --- | --- |
| Source conventions | Authoritative pilot and comparison with both implemented operators | Unresolved; paths requested from user |
| Supplied design provenance | Referenced LITCHECK draft and actual lessons query | Unresolved; not found in inspected workspace |
| Registration | Owning process, P/LC identifiers, frozen manifest/schema/formulas/source hashes | Unresolved; no identifiers fabricated |
| Independent review | Completed review with findings addressed | Unresolved; earlier reviewer timeouts are not passes |
| Target choice | User decision after preceding requirements | Not reached; all targets unrun |

These missing inputs prevent a claim of registration readiness. Numerical
qualification concerns only the stated single-angle models and documented
analytic/arithmetic assumptions, not a field-theory conclusion.
