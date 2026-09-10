<!-- commentary -->
# Vacuum–spectrum LITCHECK handoff v3

Artifact version: **3**, revised 2026-09-09; first issued 2026-09-08.
Task: `ym-vacuum-gap-litcheck`.
Repository: `nickjoven/proslambenomenos`.
Base: `da0084147986a97f355954be6b0eff4246b9d852`.
Historical source worktree branch: `ym-vacuum-gap-litcheck`.

## Deliverables

Version 3 clarifies the cancellation identity and the uniform coercivity
estimate already implicit in the ground-state-transform route. It adds
two primary geometric sources, distinguishes three meanings of geometry,
and separates a lower-bound proof milestone from numerical calibration.
The inherited glueball search ends on 2026-09-08; the focused geometry
check is dated 2026-09-09. No new scientific target cells were added or run.
The original pilot specification is preserved. The earlier proposal
review already describes this route in section 5 and remains version 1;
an unchanged copy is included under review/ in the bundle.

Version 2 adds five primary sources and the 2026 glueball update to the
LITCHECK. The registration draft adds a follow-on benchmark note. The
existing mathematical derivations, numerical cells and target status
are preserved. Literature reviewed through 2026-09-08 is incorporated;
that revision did not purport to audit later publications.

- [LITCHECK draft](ym_vacuum_gap_litcheck.md): primary-source table,
  exact conditional propositions, corrected necessity/sufficiency
  logic, vacuum-measure/kinetic-form bridge, exclusions.
- [Registration draft](ym_vacuum_gap_registration_draft.md): explicit
  finite SU(2)/U(1) models, development and target cells, derived nulls,
  operator coverage, numerical refinement, temporal-window budgets,
  decision rules and requirements for a later connected-lattice study.

The source results are cited literature; the formulas in the design are
displayed derivations or analytic controls. No scientific target cells
were executed. The study has no allocated ledger number and has not
been preregistered. The terms theorem and bound refer to their stated
mathematical assumptions, not to any computed repository status.

## Prior-pilot provenance

The recovered archive is `ym-gap-pilot-artifacts.zip`.

| Item | SHA-256 |
|---|---|
| Prior archive | `064976b9954a6d2c83c9dc24a94a3cfda64f3673fafc3d9f2976a5198b35c0a4` |
| Archived `scripts/experiments/ym_gap_pilot.py` | `9f5cd7cda74cb5623c8e20b07b34671f7cd52eb3ff9a89721571ffe356fe238a` |
| Archived `scripts/experiments/ym_gap_pilot_results.json` | `0e1a529828409cddf4ab3c1a78c5b0ccd82450e7c329c86bd93a8d88ff1b6025` |

The archive README lists `notes/ym_gap_pilot.md` and
`notes/ym_gap_next_registration_skeleton.md`, but neither is in the ZIP.
The pilot script is also absent from the inspected repo base. The
available script and JSON, not the absent notes, ground this handoff.
Their prior numerical readings retain the exploratory qualification.

## Suggested ledger-entry text for assignment

The following is an unnumbered content draft, not an append to LITCHECKS.md:

> Vacuum-state diagnostics versus excitation thresholds (2026-09-08).
> Checked the official Yang–Mills definition, Euclidean reconstruction,
> connected clustering, vacuum-functionals, lattice spectra/topology,
> condensate subtraction and ground-state geometry. The vacuum/threshold
> distinction and the centered spectral representation are classical.
> Detailed state information with a specified kinetic form can control a
> gap through a Poincaré inequality; no uniform four-dimensional bound
> follows from this review. No generic nonzero-VEV sufficiency theorem was
> identified in the checked sources. The draft corrects sufficiency versus
> necessity, operator-coverage omissions and physical-unit normalization.
> Source table and assumptions: notes/ym_vacuum_gap_litcheck.md. Proposed
> instrument study: notes/ym_vacuum_gap_registration_draft.md. This is a
> synthesis and search record, with no novelty or claim-status change.

## Landing boundary

AGENTS.md requires assignment of ledger IDs and serial integrator landing.
Accordingly these are namespaced commentary notes. No append-only ledger,
claim YAML, gate-covered script, catalog, public page or existing result
was edited. There is no unresolved mathematical claim being promoted.
The integrator should rebase onto current main, allocate an ID if a
ledger append is desired, run the existing gates and use the normal PR
process. Target execution still waits for a real registration and its
implemented derive layer.

## Checks and delivery

For version 1, the notes gate and commit-message gate passed. Local Markdown
links, display-math delimiters, code fences and whitespace were checked.
The tensor-sum null's eigenvectors were checked in exact rational
arithmetic; SU(2) Haar moments were checked with Gauss–Chebyshev U
quadrature, exact for these polynomial degrees up to roundoff. These
checks concern the document and analytic controls, not target results.
The full repository gate suite was not run for this commentary-only
handoff; it remains part of integrator landing.

The version-1 source work had a local commit, but no remote branch was
created. The shell push lacked GitHub credentials; authenticated branch
creation separately returned HTTP 403. The version-2 bundle retains the
source repository and base above as provenance and includes a patch
against that base. Its manifest distinguishes current document checks
from the analytic checks inherited from version 1. No numerical targets
were executed for version 2.

The user requested an issue in `nickjoven/quod` as a document archive.
That issue destination is separate from the source/design repository.
The prepared issue text contains the documents themselves; it does not
depend on temporary file links. The bundle records the posting outcome
separately in `github_delivery.json`.

## Version-3 validation and delivery boundary

This revision updates document artifacts. It has no new source commit,
remote write, GitHub posting attempt, ledger entry or claim promotion.
The source branch and commit references above are historical provenance.
The repository's current instructions and gates must be checked when an
integrator lands the patch; no repository gates were run for version 3.

Document checks cover preserved pilot content, source keys S1–S20,
companion links, math/code delimiters, patch application in temporary
workspaces, exact agreement between the issue body and its JSON payload,
the GitHub body-size limit, and archive member hashes. Full-patch checks
use an empty notes workspace; incremental checks use the exact archived
version-2 notes. They do not constitute a rebase onto current repository
main. No numerical targets, analytic-control reruns or Lean builds were
performed in this revision.

The version-3 issue payload is prepared but was not posted. The previous
HTTP 404 delivery record and the exact version-2 request/body are retained
under history/v2/. The current github_delivery.json distinguishes that
historical failure from this revision's unattempted delivery.
