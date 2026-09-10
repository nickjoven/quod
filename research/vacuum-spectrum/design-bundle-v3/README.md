# Yang–Mills vacuum–spectrum LITCHECK artifacts — v3

Artifact version: **3**. Revised 2026-09-09; first issued 2026-09-08.
Inherited glueball literature cutoff: 2026-09-08.
Focused geometry/coercivity source check: 2026-09-09.
Source/design repository: `nickjoven/proslambenomenos`.
Requested GitHub document archive: `nickjoven/quod`.

Start with [the LITCHECK](notes/ym_vacuum_gap_litcheck.md), especially
section 3a. The ground-state-transform/Poincaré route was already present.
Version 3 explains what cancels, what geometry remains, and why a
nonnegative remainder does not establish a uniform positive gap.
The [design draft](notes/ym_vacuum_gap_registration_draft.md) records the
independent lower-bound certificate as a separate proof milestone.
Its original pilot cells, controls, budgets and unrun status are preserved.

## Contents

- `notes/ym_vacuum_gap_litcheck.md` — synthesis, 20-source table,
  conditional propositions, retained glueball update and new clarification.
- `notes/ym_vacuum_gap_registration_draft.md` — unregistered design v3.
- `notes/ym_vacuum_gap_handoff.md` — provenance, scope and landing boundary.
- `review/yang_mills_proposal_review_v1.md` — unchanged proposal review;
  its section 5 already describes this mathematical route.
- `changes.patch` — full three-note addition for the recorded source base.
- `v2_to_v3.patch` — incremental changes to the archived version-2 notes.
- `v1_to_v2.patch` — unchanged historical incremental patch.
- `github_issue_body.md` and `github_issue_request.json` — refreshed v3
  issue text and exact REST payload containing the three core notes.
- `github_delivery.json` — current delivery status.
- `history/v2/` — original issue request, body, delivery record and manifest.
- `manifest.json` — provenance, validation scope and payload hashes.

## GitHub issue delivery

The version-3 payload is prepared but was not posted. The earlier v2
attempt failed: `gh` was absent and the connected API returned HTTP 404.
That historical record cannot distinguish missing access from an
unavailable repository. It is retained with the exact old payload.

After confirming repository access and checking for an existing issue,
run from this extracted directory:

```sh
gh api --method POST repos/nickjoven/quod/issues --input github_issue_request.json --jq '.html_url'
```

The issue body contains the three core notes themselves and does not
depend on temporary file links. The unchanged proposal review is included
in this bundle, separately from the issue body and source patches.

## Source patch use

Inspect the source repository's current AGENTS.md and use an owned
worktree. Choose `changes.patch` when starting at the recorded base,
or `v2_to_v3.patch` when the archived v2 notes are already present.
For v1, apply `v1_to_v2.patch` followed by `v2_to_v3.patch`.
Run `git apply --check` first. Do not also apply the full patch after
applying incremental patches. All patches touch only the three namespaced
notes; they allocate no ledger IDs and register or execute no experiment.
No source commit, remote write or GitHub posting occurred for v3.

## Validation scope

Version 3 checks preserve the original pilot content and unchanged review,
verify Markdown companion links, math/code delimiters, source keys S1–S20,
patch applicability in temporary empty and exact-v2 workspaces, issue
payload content/size, and SHA-256 hashes for every payload member.
These checks do not substitute for source-repository landing gates or
a rebase onto current main. No repository gates, target cells, analytic
control reruns or Lean builds were run for v3. Earlier validation remains
historical, as recorded in the handoff and archived version-2 manifest.
