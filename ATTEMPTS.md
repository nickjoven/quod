# Attempts — a prover-in-the-loop, step 0 (intake), revision 2

Status: **design for review, nothing implemented.** Merge = approval to build
what is scoped here. This is the L4/L5 piece ARCHITECTURE.md describes
(provers as agents, attempts as a separate ledger, a single serial integrator
per §5–6) made concrete. The consumer-side scope lives in lemma (its PR #1).

Revision 2 records the review's two blocking fixes as scope items with their
own exit conditions, records decisions 1–5, and removes the open questions.

## Intent

A harness that, given a **demonstrandum** (a declaration's statement at a
pin, identified by its lock), produces zero or more **attempts** — candidate
proofs — each verified *only* by the existing gates (`lock.py` equality,
`axiom_gate.py` triple, lean4checker) and recorded as a content-addressed
attempt node. The harness never declares; the gates compute. In the language
of SEMANTICS.md an attempt is an *offered proof*, and its verdict is exactly
the existing proof-verdict lattice (`accepted`, `incomplete: sorry`,
`rejected: lock mismatch`, `rejected: extra axioms`, `rejected: lean4checker`)
plus one outcome that is not a verdict at all:

    no_proof_found — the NAMED prover, within its RECORDED budget, found
    nothing. This is NOT `refuted`. Absence of a proof is not evidence of
    falsity; no code path maps one to the other. It is also not "unknown":
    it is a fact about that prover and that budget, which is why both are
    part of every attempt record.

## Why

- Every table the runner consults must be a nomination that a gate verifies
  (HANDOFF.md). An attempt ledger is the first such table for *proofs*.
- lemma OPEN.yml **L-6**: the Phase-3a mutant label (`elaborates`) is lexically
  shallow — a bag-of-tokens baseline nearly matches it. "Does the mutated
  claim still hold?" is a proof question; only attempts answer it.
- lemma's S5 emits equivalence proposals `A ↔ B` (lemma L-5); the plan's bar
  (≥ 10 of the top 100 discharged) needs attempts against the gates.
- The attempt ledger is the on-policy data for the proof-state model.

## Scope (what changes in quod)

1. `scripts/AttemptWalk.lean` — imports the pin, elaborates each demonstrandum,
   runs a **bounded tactic ladder** under a per-tactic heartbeat cap, and on
   success emits the proof term. CorpusWalk pattern: explicit-handle output,
   `START` markers, per-declaration budgets, runtime exceptions downgraded to
   a recorded outcome.
2. **Self-proof exclusion gate** (blocking fix 1). With the pin imported, a
   "proof-stripped" control theorem is still in the environment under its
   own name, and `exact?`/`apply?` would close it by lookup in one step. So an
   accepted proof term is gated: its `getUsedConstants` may contain **neither
   the demonstrandum's own name nor any constant whose lock equals the
   demonstrandum's lock** (the corpus already records `proof_consts` and
   locks — this is lock equality, a nomination verified by a gate). The check
   runs on every accepted attempt and its result is a field of the attempt
   record. Without it, P is set from a contaminated number; it therefore
   exists **before** the pilot (see decision 2).
3. `scripts/attempt.py` — driver reusing `corpus_extract.run_segment`
   (watchdog, process-group kill, resume past a hung demonstrandum). For every
   accepted term it runs the three gates *as they are* plus gate 2, and
   records the verdict.
4. `attempts/` — append-only ledger, one line per attempt:
   `demonstrandum_lock | prover | prover_config_cid | proof_cid | outcome |
   lock_ok axioms_ok checker_ok selfproof_ok | verdict | heartbeats | wall_s`;
   a manifest whose CID is the attempt-corpus version (carrying P, the
   budgets, and — for tier B — the total API budget, all written before the
   run); a `ket put` of every proof term and gate output; runner script
   sha256s (Q-23).
5. **Calibration control sets** (the SEMANTICS.md calibration doctrine applied
   to provers), run before any real attempts, each required to land at its
   required outcome:
   - **positive** — 200 Mathlib theorems with proofs stripped: reproved at
     ≥ P%, every acceptance passing all three gates **and** gate 2;
   - **prover negative** (blocking fix 2) — for every positive-control theorem
     `T`, attempt `¬T`. Any acceptance **halts the run**: it would mean the
     pin is inconsistent. This reuses the N4 refutation shape;
   - **gate-wiring test** — the `sorry`/axiom injections. These are proof-side
     and the ladder never emits `sorry`, so they test that the gates are wired
     into the harness correctly, not the prover. Named as such; required
     outcome: every one rejected by the gates.
   `elaborates=false` mutants are **not** in any control set: a lock needs an
   elaborated type, so an attempt against one is ill-formed, not negative.

## Boundary (what does NOT change)

- No gate is modified. A positive control failing means the harness is
  wrong, not the gate.
- No claim status in `claims/` is written by the harness. Attempts are their
  own ledger. Promotion of an accepted attempt to a claim's `proven` goes
  through `calibrate.py`'s existing path; a registry acceptance goes through
  the serial integrator (ARCHITECTURE.md §5–6) and a human, always. **There
  is no auto-promotion** (decision 5).
- No pin, corpus, or existing manifest is touched.

## Decisions (recorded from review)

1. **Prover tiers: A, then B as escalation on A's failures; C deferred.**
   A = in-process ladder (`rfl`, `decide`, `simp`, `omega`, `exact?`/`apply?`,
   `aesop`), no external artifact. **B = an LLM prover, admitted as a recorded
   nomination**: `prover_config_cid` covers model id, version date, system
   prompt, temperature, and seed; every B attempt is tagged so lemma can hold
   them out or condition on them; the total API budget is written into the
   attempt manifest before the run. C = lean-dojo bounded search, deferred to
   the proof-state stage.
2. **P is set from a pilot, then frozen.** 50 theorems per tier, P written
   into the manifest, *then* the 200 are run. Setting P after seeing the 200
   is the tuned-check lesson ARCHITECTURE.md §5 carries over. Both happen
   after scope item 2 exists; tier A alone is expected well under 20% once
   self-proof is excluded.
3. **Budgets.** Per tactic: a heartbeat cap in the range the walkers already
   use (2e7), with `exact?`/`aesop` at the top of it. Per demonstrandum: a
   ~60 s wall-clock watchdog, because `ppExpr` is not heartbeat-checked. Total:
   measured on the existing corpus first (decision 4), then written into the
   manifest.
4. **Mutant sample: keep `sample_mod` 46 for the first run.** The existing
   corpus (mutants-20260911) already has 8,187 statement mutants over 5,410
   parents, above exit condition 3's 5,000. Going to `sample_mod` 10 would
   multiply the walk and the attempts ~5× before the per-attempt cost is
   known. Run on what exists, measure, then decide.
5. **No auto-promotion.** Kept as boundary, above.

## Exit conditions (falsifiable)

1. Positive controls reproved at ≥ P% (P frozen from the pilot), every
   acceptance passing all three gates and the self-proof gate.
2. **Self-proof exclusion: 0 accepted proofs whose term uses the
   demonstrandum or any same-lock constant** (this is the check, recorded per
   attempt, that makes condition 1 measure proving rather than lookup).
3. Prover negatives (`¬T`): 0 acceptances; one acceptance halts the run.
4. Gate-wiring test: every injection rejected by the gates.
5. `gate_verdict` ∈ {proven, no_proof_found, rejected:*} — each tagged with
   prover and `prover_config_cid` — recorded for the existing 8,187
   statement mutants.
6. lemma's reranked proposals each attempted as `A ↔ B`; the discharged
   count reported against the bar of 10.
7. Every number lands only as a sealed record with a CID.

## Rollback

Pure addition (new scripts, new ledger directory). Revert = delete them.

## Risks

- **Verdict semantics** — `no_proof_found` mistaken for `refuted`, or read as
  "unknown" rather than "this prover, this budget": the schema makes it a
  distinct, prover-tagged value and no code path maps it elsewhere.
- **Self-proof contamination** — closed by scope item 2 / exit condition 2;
  it is the reason the pilot cannot precede the gate.
- **Coverage** — tier A alone may be too sparse to train on; hence B.
- **Cost** — one Lean process at a time on this box; per-attempt caps; resume.
- **Prover leakage** — an LLM reproving a memorized theorem yields a *valid*
  gate-verified proof; only the *difficulty* signal is contaminated. Recorded
  prover identity lets consumers condition on or hold out tier-B attempts.


## Amendment A1 (2026-09-14): the pilot frame and the frozen P

Decision 2 froze P at the point estimate of a 50-theorem pilot nominated
by seeded hash order over all theorems, while the test set was nominated the
same way separately. Both tiers then failed exit condition 1 in the same
direction (Q-26; diagnostic CID 3b527442…): the pilot was shallower and
shorter than the test. For every prover config after this date:

1. The test frame comes first: 200 or more theorems, sealed by CID.
2. The pilot is a seeded random subsample of that frame, stratified by
   proof-DAG depth quartile (`dag_depth.py` table), seed sealed.
3. P is frozen at the lower bound of an 80% Wilson interval on the pilot
   rate; the point estimate is recorded beside it.
4. Frozen values already on record (tier A 0.32, tier B 0.74) stay with their
   failures. A funded rerun is a new prover config under this amendment.

Nothing else in decision 2 changes: P is still frozen before the test and
never revised after it.
