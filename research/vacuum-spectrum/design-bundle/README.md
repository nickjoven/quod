# Yang–Mills vacuum–spectrum LITCHECK artifacts

Date: 2026-09-08. Repository: nickjoven/proslambenomenos.

Start with notes/ym_vacuum_gap_litcheck.md. The companion registration
is a complete design draft for a finite-model instrument study, not an
executed or registered experiment. The handoff includes prior-pilot
provenance, source boundaries and validation details.

Contents:
- notes/ym_vacuum_gap_litcheck.md
- notes/ym_vacuum_gap_registration_draft.md
- notes/ym_vacuum_gap_handoff.md
- changes.patch
- manifest.json

Apply the patch in an owned repository worktree after inspecting current
AGENTS.md. The patch only creates the three namespaced notes. It does not
append a ledger or modify any gate. Run git apply --check first. The
integrator assigns any ledger IDs and performs the normal serial PR/gate
workflow. Alternatively copy the three notes; do not do both.

No remote branch was created: GitHub returned HTTP 403 for authenticated
branch creation. This bundle preserves the completed work for review.

Validation: notes gate, commit-message gate, Markdown local links and
math/fence delimiters, whitespace, tensor-sum eigenvector algebra, and
SU(2) Haar-moment quadrature. Full repo gates and target runs were not run.
