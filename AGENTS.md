# AGENTS.md — operating rules for agents working in quod

Fleet-wide rules (ports, processes, shell hygiene, secrets) live in
[homeserv/AGENTS.md](https://github.com/nickjoven/homeserv/blob/main/AGENTS.md)
and apply here. quod adds:

- **Status is computed, never typed.** A claim's status comes from the gates
  through `calibrate.py` / `write_claims.py`; do not edit `claims/*.yml` by
  hand. Prose describes what was computed and says nothing about authors.
- **Every number is a sealed record.** A result without a manifest and a
  CID does not exist; `scripts/verify_records.py` (CI) checks the tracked
  records and must pass before a push to `main`.
- **Never edit a runner while a run is in flight** (Q-23): manifests hash
  `scripts/` at the end; the record must describe what ran. Stage the patch
  and apply it after the run exits.
- **One Lean process at a time on this box** (15 GB): the walker, a gate
  build, an intake build, or a checker replay, never two. `lean4checker`
  needs `--num-workers=2` here.
- **Provers are prover-relative.** `no_proof_found` is never `refuted`; P
  is frozen before a test and never revised after (decision 2, amendment
  A1: frame first, depth-stratified pilot, Wilson lower bound).
- **Paid runs:** credentials from the gitignored `.env` (`VALID`, `SPACE`),
  mapped into the launcher's process only; a cap in cents sealed in the
  pre-manifest before the first request; paid batches are reused by id,
  never resubmitted; spend is recorded from `usage`, including voided runs.
- **Cross-pin locks are never compared** (decision 3); an external claim is
  built and gated at its own pin (`intake/<name>/`), and statement fidelity
  to another formalization is a descriptor.
