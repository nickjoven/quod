# Alignment with the recovered experiment draft

## Authoritative design recovered

The user supplied `ym-vacuum-gap-litcheck-artifacts.zip`. Its original
manifest verifies all five listed payload hashes. The bundled LITCHECK
is byte-identical to the previously recovered Downloads draft. All six
original files are preserved under `design-bundle/`; the patch is retained
as evidence and was not applied. `archive-provenance.json` records the ZIP
and manifest hashes. No ledger entry or target execution occurred.

The [registration draft](design-bundle/notes/ym_vacuum_gap_registration_draft.md)
now supplies the operator conventions, cutoff ladders, exact nulls and
pre-registration requirements. The [handoff](design-bundle/notes/ym_vacuum_gap_handoff.md)
provides hashes of the separate pilot archive, script and results. That
pilot archive is not included in this bundle.

## Material differences found

| Requirement in recovered draft | Existing development evidence | Required action |
| --- | --- | --- |
| SU(2): 4 g^2 C2 - 2 eta P/g^2; J=20..320 | Matches implemented convention and ladder | Retain numerical evidence; pilot replication still awaits original output/code |
| U(1): 4 g^2 n^2 - 2 eta cos(theta)/g^2 | Archived U(1) instrument uses g^2 n^2 | Implement and run the specified kinetic coefficient; old results remain valid only for their declared different model |
| U(1) cutoffs 40,80,160,320,640 | Archived cutoffs 20,40,80,160,320 | Use the recovered five-rung ladder in the new instrument |
| Gapless measure exp(-E)dE, C(t)=1/(1+t) | Existing analytic null uses uniform measure on [0,1] | Add the specified exponential-measure null; retain uniform measure as an additional control |
| Tensor H=(I-X) tensor I + eps I tensor (I-X) | Existing dark-factor family has a different energy normalization | Add the exact specified matrix family and fixed-ground checks |
| Hidden state diag(0,eps,1) with C(t)=exp(-t) | Existing hidden-state fixture uses fixed energies 0,1,2 | Add the specified epsilon family |
| Raw G(t)=mean^2+C(t), slope tends to zero | Existing disconnected-vacuum null emphasizes ground degeneracy | Add the nonzero-mean raw-correlation finite-time control explicitly |
| Lessons query lists fourteen IDs | Recovered workflow query used a different keyword set and returned eight | Reproduce the draft's exact query and incorporate all relevant clauses |
| Pilot replication | Pilot hashes now available, but code/JSON still missing | Obtain separate `ym-gap-pilot-artifacts.zip`; do not infer its operator from quoted numbers |
| Freeze before target execution | Development artifacts are unregistered | Assign IDs through owner, finish derive layer/review and register future work only |

The U(1) kinetic change is not a mere energy offset or overall clock scaling:
its potential coefficient is held fixed. It can change eigenvectors, moments,
overlaps and all correlation bounds. Existing U(1) certificates and qualifying
sampled windows therefore cannot stand in for the recovered design's results.

## Next numerical work

Update: [U1-DESIGN-RUN.md](U1-DESIGN-RUN.md) records completion of the
corrected scalar run. Certificates and temporal bounds remain to be regenerated.

Preserve hash-locked historical instruments. Add a version using the recovered
U(1) coefficient and ladder, independently verify Fourier/periodic agreement,
then regenerate exact spectral/overlap bounds and direct-propagation window
assessments for the ten development cells. Complete the specified analytic
null fixtures. The old readiness record is a historical audit of the earlier
model, not evidence of readiness for this recovered specification.

The source pilot, assigned P/LC IDs and independent review remain outstanding,
but they no longer prevent these explicit development corrections. All 42
target rows remain unrun. Target selection is not yet required.

## Verification

```sh
python3 scripts/verify_vacuum_design_bundle.py
```

This verifies the original file hashes and equality of the two LITCHECK
copies. It authenticates internal bundle consistency, not scientific approval
or independent confirmation of the handoff's historical claims.
