# Reviewable numerical result contract

## Scope and representation

`result-contract.schema.json` defines a cell-result payload plus an
unregistered draft envelope. The checked-in envelope contains twenty
archived development examples and all 42 target identities with status
unrun and result null. Its schema prohibits target data and authorization.
The reusable cell-result definition permits available, failure and unresolved
records with a required reason. It is a proposed data contract; it is not
registration, a target executor or permission to execute a target.

Available records carry two observable channels and three checksum-pinned
JSON Pointer references. The scalar reference preserves E0, ground vector,
ordered finite spectra (both U(1) parities), moments, covariance, spectral
weights and solver diagnostics. The certificate reference preserves ordered
model enclosures, vector residual bounds, overlap intervals, padded moments,
omitted-spectrum bounds and correlation intervals. The temporal reference
preserves direct correlations, physical sample times, all assessed pairs,
mixture and numerical error components, and nonqualifying outcomes. Null
error components in the source stay null; they are not replaced by zero.
References are resolved and checked against the physical cell identity.
Thus the contract retains complete numerical artifacts without duplicating
large ground vectors and every intermediate rung into another schema.

The certificate adapter checks consecutive retained levels in the producer's
certified spectral scope: the full SU(2) sector or reflection-even U(1)
sector. Producers must supply valid ordered eigenvalue, invariant-sector and
omitted-spectrum certificates. The interface checks and existing archive
replays do not replace those mathematical arguments.

## Exact zeros, unknown overlaps and thresholds

`vacuum_channel_contract.threshold` examines every preceding retained level.
A rigorously positive weight is retained even if tiny. A weight interval
containing zero leaves the threshold unresolved. The contract never skips
such a level to report a cleaner higher threshold.

The supported exact-zero rule is `free_polynomial_selection`, valid only at
eta=0 for the specified SU(2) or reflection-even U(1) polynomial observables.
P excites level 1 and centered P^2 excites level 2; all other retained free
levels have zero weight. The checker rejects this rule at nonzero eta, at
the observable's active level, or without the exact [0,0] weight. It also
checks each free gap interval against the analytic spectrum. A rounded or
unsupported [0,0] without the structural rule remains unresolved.

For a candidate threshold, a positive omitted weight also requires its
certified spectral floor to lie above the candidate interval. Otherwise
the threshold is unresolved. `full_gap_claim_supported` permits a full-gap
claim only for the first full SU(2) level. A reflection-even U(1) threshold
never establishes a full-gap claim through this interface, even when its
energy happens to coincide with a full-gap energy.

The same conservative slope assessment is applied using the selected
accessible level. Analytic calibration at g=1/2, eta=0 demonstrates that
P^2 can qualify against its second-level threshold, without calling it the
full gap. These are free analytic fixtures, not target solver evaluations.
Nonpositive observed correlations retain an unresolved window. No universal
late time or target time window is selected here.

## Failure semantics and future integration

A failure cannot carry a successful channel result. An unresolved record can
retain no payload when the numerical evidence is unavailable, with an
explicit reason. An available record must retain all three provenance
references and both channels. A missing target row is rejected, rather than
dropped from an aggregate. Every target row is still unrun in this draft.

The proposed contract and free selection handling are now reviewable. Before
registration, the owner must approve/freeze the final target envelope, source
hashes, clauses and per-cell window procedure. Any executor must use the
correct physical sector and retain failed/unresolved rows. The current
module has no target execution entry point; its CLI only adapts already
archived development data. Original pilot replication, P/LC assignment and
independent review remain external prerequisites.

## Reproduction and drift checks

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_result_contract.py --output research/vacuum-spectrum/result-contract.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*contract*.py' -v
```

Dependencies are pinned in `requirements-readiness.txt`, using the existing
JSON Schema and JSON Pointer libraries. The archive records source/schema
hashes, and the verifier checks all referenced artifact hashes and pointers.
Tests reproduce all twenty examples and reject altered thresholds, swapped
cell payloads, missing rows, false target data and empty failure reasons.
Additional analytic tests exercise tiny uncertain/positive overlaps,
unsupported zero rules, omitted low spectrum and invalid correlation windows.

Validation: all 126 numerical tests passed. `git diff --check` passed.
The contract archive was regenerated after the final source-hash change;
historical numerical artifacts were unchanged.

Implementation commit: `83ceb8d`; artifact commit: `bd8a640`. Validated packet:
`7fb9e8fff469b3f35a926bb0f7e823fed4286f07e59c03834f4b70255f493add`.
Artifact validation passed and ket projection was clean. The packet retains
the document before this provenance paragraph, avoiding self-reference.
