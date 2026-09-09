<!-- commentary -->
# Vacuum–spectrum LITCHECK handoff

Task: `ym-vacuum-gap-litcheck`, 2026-09-08.
Repository: `nickjoven/proslambenomenos`.
Base: `da0084147986a97f355954be6b0eff4246b9d852`.
Owned worktree branch: `ym-vacuum-gap-litcheck`.

## Deliverables

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

The existing notes gate and commit-message gate passed. Local Markdown
links, display-math delimiters, code fences and whitespace were checked.
The tensor-sum null's eigenvectors were checked in exact rational
arithmetic; SU(2) Haar moments were checked with Gauss–Chebyshev U
quadrature, exact for these polynomial degrees up to roundoff. These
checks concern the document and analytic controls, not target results.
The full repository gate suite was not run for this commentary-only
handoff; it remains part of integrator landing.

The task has a local commit, but no remote branch was created. The shell
push had no GitHub credentials; authenticated branch creation separately
returned HTTP 403, `Resource not accessible by integration`. Delivery is
therefore a self-contained artifact bundle, including an apply-ready
patch against the inspected base. No remote repository content changed.
