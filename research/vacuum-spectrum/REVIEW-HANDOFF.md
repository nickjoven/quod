# Vacuum-spectrum development review handoff

## Candidate and decision requested

Review candidate: `4b96f84614a5ceda04269af7a5a1d4e91a27ef95` in quod,
branch `research/vacuum-spectrum-preflight`. This page packages existing work
for review; it is not a review verdict, a registration or target authorization.
The reviewer should report defects and unresolved assumptions against the
candidate commit and identify which must be resolved before registration.

The implemented study is the recovered single-angle SU(2)/U(1) instrument.
Ten development cells per theory have archived representation comparisons,
spectral and overlap certificates, and sampled temporal-window assessments.
Forty-two target cells remain unrun. The v3 revision preserves the numerical
specification and adds a separate full-domain proof milestone.

## Authoritative evidence and review questions

| Review scope | Entry point | Question to resolve |
| --- | --- | --- |
| Operator conventions and physical domains | [Design v3](design-bundle-v3/notes/ym_vacuum_gap_registration_draft.md), [alignment](DESIGN-ALIGNMENT.md) | Do the SU(2) Casimir and corrected U(1) coefficient 4g², domains, measures and cutoffs match the stated experiment? |
| Full-domain spectral and overlap bounds | [SU(2) certificates](CERTIFICATES-RUN.md), [U(1) certificates](U1-DESIGN-CERTIFICATES-RUN.md) | Are Sturm signs, tail/Schur enclosures, residual-to-vector bounds, padded moments and omitted spectral weight justified on the stated domains? |
| Combined temporal error | [SU(2) late times](LATE-TIMES-RUN.md), [U(1) propagation](U1-DESIGN-SEMIGROUP-RUN.md) | Does each accepted pair include the spectral-mixture and numerical slope errors, without promoting tolerance agreement to an unsupported bound? |
| Operator visibility and exact zero | [Result contract](RESULT-CONTRACT.md) | Are full gap and even-channel threshold separated, uncertain small overlaps retained, and exact zeros justified analytically? |
| Null responses and failures | [Specified nulls](DESIGN-NULLS.md), [readiness](DESIGN-READINESS.md) | Do the exact controls and solver mutants expose the intended failures, and are missing/unresolved rows retained? |
| Source provenance | [Pilot disposition](PILOT-DISPOSITION.md), [source recovery](SOURCE-RECOVERY.md) | Is historical replication correctly marked unavailable, with the independent development baseline and its source hashes explicit? |
| Mathematical milestone | [Vacuum coercivity](VACUUM-COERCIVITY.md), [v3 focus](V3-FOCUS.md) | Are the cancellation identity, full-domain comparison lemma, counterexample, physical scales and missing uniformity distinguished correctly? |
| Future registration | [Result contract](RESULT-CONTRACT.md), [cost plan](TARGET-COST-PLAN.md) | What additional derive-layer, executor or schema work must be frozen before any future target run? |

Tests support these questions but do not decide them. In particular a repeated
implementation identity is not an independent analytic proof, and a passing
finite-model regression supplies no field-theory construction. Cost scenarios
are estimates from development runs, not target convergence guarantees.

## Provenance deviations to carry into registration

The original pilot code and results are lost by the user's explicit report.
The handoff's expected hashes and quoted readings remain historical records;
original-pilot replication is unverifiable and is not a recovery prerequisite.
Future registration must name the current archived development baseline.

The old coefficient-1 U(1) archives are preserved for provenance. Current
design evidence uses only the corrected coefficient-4 instrument. Do not
combine the two as if they were interchangeable runs of the same Hamiltonian.

The supplied v3 proposal review concerns the conceptual proposal. It does not
constitute independent review of these numerical sources or their certificates.
The new bounded-potential comparison applies on its positive-margin parameter
region; it is not a volume-uniform or continuum Yang–Mills gap certificate.

## Reproduction

Use Python and dependencies pinned in `requirements-readiness.txt`. From the
quod root, run:

```sh
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
python3 scripts/verify_vacuum_coercivity.py
git diff --check
```

The suite replays archived development evidence and checks target exclusion;
it does not run a target solver. The coercivity check independently replays
the documented counterexample's rational upper bounds and source hashes.
Neither command checks a Lean formalization; none is claimed.

Validation at the candidate commit: all **130 tests passed in 62.583 seconds**;
all six coercivity sample bounds and their source hashes verified. Local
handoff links and `git diff --check` passed. These are local validation
results, not an independent review verdict.

## Remaining owning-workflow input

No P/LC identifiers have been assigned. The recovered owner guidance requires
assignment before ledger entries and an integrator for serial landing; its
snapshot is in `source-recovery/owner-guidance.txt`. The source clone remains
unmodified. A future registration must precede the work it covers and freeze
the final source hashes, error formulas, clauses, manifest, result envelope
and per-cell window procedure. It cannot retroactively register development.

Required next external inputs are an independent review of this candidate and
owner-assigned identifiers for the intended registration. No review request
has been sent to another person or service by this handoff. No target decision
is requested until those prerequisites and any resulting repairs are resolved.
