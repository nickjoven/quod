# Attempts — a prover-in-the-loop, step 0 (intake) for review

Status: **design for review, nothing implemented.** Merge = approval to build
what is scoped here; comments change the scope first. This is the L4/L5
piece ARCHITECTURE.md describes (provers as agents, attempts as a separate
ledger) made concrete. The consumer-side scope lives in lemma (its PR #1).

## Intent

A harness that, given a **demonstrandum** (a declaration's statement at a
pin, identified by its lock), produces zero or more **attempts** — candidate
proofs — each verified *only* by the existing gates (`lock.py` equality,
`axiom_gate.py` triple, lean4checker) and recorded as a content-addressed
attempt node. The harness never declares; the gates compute. In the language
of SEMANTICS.md: an attempt is an *offered proof* of a demonstrandum, and its
verdict is exactly the existing proof-verdict lattice (`accepted`,
`incomplete: sorry`, `rejected: lock mismatch`, `rejected: extra axioms`,
`rejected: lean4checker`) plus one new outcome that is not a verdict at all:

    no_proof_found — the harness exhausted its budget. This is NOT `refuted`.
    Absence of a proof is not evidence of falsity; the ledger keeps them apart.

## Why

- Every table the runner consults must be a nomination that a gate verifies
  (HANDOFF.md). An attempt ledger is the first such table for *proofs*.
- lemma's S4 showed the Phase-3a mutant label (`elaborates`) is lexically
  shallow (a bag-of-tokens baseline nearly matches it). "Does the mutated
  claim still hold?" is a proof question; only attempts answer it.
- lemma's S5 emits equivalence proposals `A ↔ B`; the plan's bar (≥ 10 of the
  top 100 discharged) needs attempts against the gates.
- The attempt ledger is the on-policy data for the proof-state model.

## Scope (what changes in quod)

- `scripts/AttemptWalk.lean` — imports the pin, elaborates each demonstrandum,
  runs a **bounded tactic ladder** under a per-attempt heartbeat cap, and on
  success emits the proof term. CorpusWalk pattern: explicit-handle output,
  `START` markers, per-declaration budgets, runtime exceptions downgraded to
  a recorded outcome.
- `scripts/attempt.py` — driver reusing `corpus_extract.run_segment`
  (watchdog, process-group kill, resume past a hung demonstrandum). For every
  successful term it runs the gates *as they are* and records the verdict.
- `attempts/` — append-only ledger, one line per attempt:
  `demonstrandum_lock | prover | prover_config_cid | proof_cid | outcome |
  lock_ok axioms_ok checker_ok | verdict | heartbeats | wall_s`; plus a
  manifest whose CID is the attempt-corpus version, and a `ket put` of every
  proof term and gate output. Runner script sha256s recorded (Q-23).
- Two **calibration control sets**, run before any real attempts and required
  to land at their required outcome (the calibration doctrine of SEMANTICS.md
  §calibration applied to provers):
  - positive: 200 Mathlib theorems with proofs stripped → must be reproved at
    ≥ P% *and* every accepted proof must pass all three gates;
  - negative: `elaborates=false` mutants and `sorry`/`axiom` injections → the
    gates must reject **every** accepted attempt; one acceptance halts the run.

## Boundary (what does NOT change)

- No gate is modified. A positive control failing means the harness is
  wrong, not the gate.
- No claim status in `claims/` is written by the harness. Attempts are their
  own ledger; promoting an accepted attempt to a claim's `proven` is a later
  step that goes through `calibrate.py`'s existing path.
- No pin, corpus, or existing manifest is touched.

## The decision this PR asks for: which prover

| Tier | Prover | Pros | Cons | Cost |
|---|---|---|---|---|
| A | in-process ladder: `rfl`, `decide`, `simp`, `omega`, `exact?`/`apply?`, `aesop`, each heartbeat-capped | no external artifact; deterministic; cheap; an honest floor | low coverage on real Mathlib statements | ~1–2 days |
| B | LLM prover (Claude API) proposing proof scripts, **every one gate-verified** | coverage; provenance holds because the proof, not the prover, is trusted | an external model in the loop; API cost; prover identity/version must be in every record; memorized Mathlib contaminates *difficulty*, not validity | ~1 day + API |
| C | lean-dojo bounded tactic search | yields state/tactic/next-state traces for the proof-state model | heaviest; RAM (one Lean env at a time) | ~3–5 days |

**Recommendation: A first, B as escalation on A's failures, C deferred.**
Tier B is a doctrine call for the owner: quod's decisions table admits other
provers "via sieve from the start"; an LLM whose output is gate-verified is a
prover in exactly that sense, but its identity must be a recorded nomination.

## Exit conditions (falsifiable)

1. Positive controls reproved at ≥ P% (owner sets P per tier; A alone ≈ 20%,
   A+B ≥ 70%), every acceptance passing all three gates.
2. Negative controls: 0 accepted attempts.
3. `gate_verdict` ∈ {proven, no_proof_found, rejected:*} recorded for
   ≥ 5,000 statement mutants (a larger mutant sample: `sample_mod` 46 → ~10).
4. lemma's top-100 *reranked* proposals each attempted as `A ↔ B`; the
   discharged count is reported against the bar of 10.
5. Every number lands only as a sealed record with a CID.

## Rollback

Pure addition (new scripts, new ledger directory). Revert = delete them.

## Risks

- **Verdict semantics** — `no_proof_found` mistaken for `refuted` is the one
  failure that would corrupt every downstream label; the schema makes them
  distinct values and no code path maps one to the other.
- **Coverage** — tier A alone may be too sparse to train on.
- **Cost** — one Lean process at a time on this box; per-attempt caps; resume.
- **Prover leakage** — recorded prover identity lets consumers condition on it.

## Open questions for the reviewer

1. Tier B — acceptable, with the prover recorded as a nomination?
2. P for the approved tier.
3. Per-attempt and total budgets.
4. Mutant sample size (`sample_mod` 10 → ~25k parents?).
5. Should an accepted attempt on a *registry* demonstrandum ever auto-promote,
   or always require the serial integrator (decision 5: one serial integrator)?
