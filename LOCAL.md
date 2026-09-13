# LOCAL.md — a local ecosystem that reduces paid-token dependence

Design document (like ATTEMPTS.md): scope, pieces, gates, order. Nothing
here changes a gate. Every piece lands as a recorded prover, a sealed run,
or a scripted pipeline; the ledger doctrine is unchanged.

## Why

Paid frontier tokens are consumed by exactly two things in this project:

1. **The tier B prover** (claude-opus-5 through the Batches API). The pilot
   proved 46/50 for $25.30 all-in. Extrapolated to the 5,410-theorem sample
   and 6,152 mutants it is thousands of dollars per pass, and every rerun
   (new pin, new ladder, adversarial corpus) pays again.
2. **Agent labor** (Claude Code sessions): design, harness code, run
   babysitting, review. This is the larger consumer and the harder one to
   replace; the lever is making the pipeline run unattended so agent time
   goes to design and review, not to watching logs.

Everything else — Lean, the gates, the corpora, the encoders, W0 — is
already local and free. The plan therefore has three legs: a **local
prover tier** that takes most of the load off tier B, a **distillation
loop** that turns each paid proof into local capability, and **unattended
orchestration** so runs stop costing agent tokens.

## What we have

| resource | state |
|---|---|
| GPU | RTX 4070, 12 GB — serves an 8B model at 4-bit, or trains W0/S4, not both at once |
| CPU / RAM | 24 cores, 15 GB (WSL cap 24 GB after restart) — one Lean walker (≈8 GB) at a time |
| disk | ≈860 GB free — weights (5–10 GB each) and corpora are not a constraint |
| local inference | nothing installed yet (no llama.cpp, vLLM, or ollama) |
| provers | tier A (ladder-A, P_A 0.32), tier S (ladder-S, P_S 0.28 / test 0.445), tier B (P_B(16) 0.92) |
| learned models | S2 encoder, S4 v2, W0 v2 (passed its gate) — all local |

## Pieces

### L1. Local inference server (the substrate)

`llama.cpp` server (GGUF, CUDA build) as the default: single binary,
OpenAI-compatible `/v1` endpoint, batched decoding, no Python stack on the
GPU. vLLM is the alternative if throughput on the 4070 turns out to matter
(AWQ 4-bit); decide from the L2 smoke, not in advance.

Doctrine hooks:
- a **model registry** in quod's ket: each weight file `ket put`, with a
  `models/<name>.json` recording the CID, source repo and revision,
  quantization, license, context length, and the server build sha. A prover
  config cites the weight CID exactly as it cites the Mathlib pin.
- the server runs under a fixed launch script with health check; one GPU
  job at a time is scheduled by the orchestrator (L6), never by hand.

### L2. Tier L: the local prover, same protocol as tier B

`attempt_b.py` already abstracts the prover as "one proof script per open
demonstrandum per round, with the previous Lean error appended". Add a
backend switch (`--backend anthropic | openai-compat --base-url … --model …`)
and the prover name `tier-L-<model>`; everything downstream (stepwise
replay, self-proof gate, batch module, axiom triple, lean4checker,
transitions with `source=search`, spend = 0 but wall-clock recorded) is
unchanged. Two differences from tier B, both recorded in the config:
- **sampling instead of thinking**: `n` samples per round at temperature
  0.6–0.8 (pass@n), each replayed; the first gate-accepted wins.
- **rounds are cheap**, so the level ladder becomes 1 / 4 / 16 / 64.

Candidate models (Lean-4 tuned, 7–8B, fit 12 GB at 4-bit): Goedel-Prover
V2 8B, DeepSeek-Prover V2 7B, Kimina-Prover distill 8B; a general Qwen3-8B
as the control. They were trained on older Mathlib pins, so lemma names
drift; the error-feedback rounds absorb that, and the drift rate is a
descriptor worth reporting per model.

Gate: P_L frozen from the same 50-theorem pilot (all levels), then the
200-theorem test; ¬T halt-on-accept as for every prover.

### L3. The escalation ladder: pay only for what the local stack cannot do

A demonstrandum goes A → S → L → B, each tier with its recorded budget,
and a theorem enters tier B only after tiers A, S and L have failed on it.
The escalation rate (fraction reaching B) is the number that measures the
ecosystem: at the pilot's shape (S proves 0.28–0.45, B(1) 0.74) a decent L
should push the paid share below a fifth of the corpus, and distillation
(L4) pushes it further with every pass.

### L4. Distillation: convert paid proofs into local capability

Every gate-accepted proof from any tier is a labelled example
(statement → script), already sealed by CID. QLoRA fine-tuning of the
tier L base on the accepted set fits the 4070 (hours per epoch at 8B
4-bit). The gate is the only one that matters: P_L before vs after on the
FROZEN control sets, tier by tier, with the adapter CID in the prover
config. Leakage rule: no control-set theorem in the training set, ever;
mutants inherit exclusion from their parent.

Priority of training signal, in order of value per example: tier B proofs
(hardest), tier S multi-step paths, tier A one-liners. The 46 tier B proofs
already exist; the first adapter can be trained the day the tier L base is
running.

### L5. W0 as the search policy

W0 predicts the next state, the outcome class, and (after L-8 is fixed) the
cost. That is a policy and a value: order the step ladder per state by the
predicted closure energy and prune branches predicted to hit the budget.
Gate: proofs found per node budget vs the unguided ladder-S on the frozen
sets, and cost per proof in heartbeats. This is the payoff of the world
model and costs no tokens at all.

### L6. Unattended orchestration (the agent-token lever)

- **Queue and timers**: a small local queue (one file per job: run id,
  command, resources needed: `lean`, `gpu`) drained by a systemd timer or a
  cron loop that never runs two Lean walkers or two GPU jobs at once. The
  chain scripts written this week (`run-transitions-t1.sh`,
  `run-ladderS.sh`, `run-w0.sh`) are the first jobs.
- **Run doctor**: a deterministic classifier over driver logs and manifests
  (crashed / hung / halted on cap / sealed / gate failed) that writes one
  status line per run and a daily summary; no model involved. Only a status
  the doctor cannot classify goes to an agent.
- **Wire on seal**: when a manifest seals, the wiring script runs
  automatically and the lemma manifest is updated by CID.
- **Push summaries, not logs**: one message per sealed run (numbers plus
  CIDs), the same text that goes into memory and the PR body.

Agent time then covers: design docs, reviewing sealed numbers, the next
runner revision. Not: watching a batch poll.

### L7. Local prose and adversaries (the remaining API uses)

- **Gloss fidelity (Q-5, S3)**: a local sentence encoder (bge-m3 or nomic-
  embed, weights by CID) for docstring drift, replacing the tokenizer
  re-pin decision that stalled S3; and a local 8B for paraphrase controls.
- **Gate adversary (item 7)**: a local model generates forged proofs,
  disguised leaves and lock-collision candidates by printing; every catch
  becomes an N-control. Nick's note that this should be a non-Claude
  generator is satisfied for free.
- **Model adversary (item 8)**: the (goal, tactic) search that maximizes W0
  error runs locally against the local Lean; Lean labels; misses become
  `source=adversarial` rows with `predictor_cid` set.

## Measurements (all sealed, none new in kind)

| number | meaning |
|---|---|
| paid cents per gate-accepted proof, per pass | the ecosystem's headline; falls with L2–L4 |
| escalation rate to tier B | the share the local stack cannot do |
| P_L per level, per model, before/after distillation | local prover capability |
| wall-clock per attempt per tier | the cost the local stack actually pays |
| proofs per node budget, guided vs unguided | W0's search value |
| agent sessions per sealed run | the orchestration lever, tracked from the handoff log |

## Order

0. **Now, with the funded tokens**: tier B on the 200-theorem test set at a
   cap Nick sets (recommended: 4 rounds, ≈$30, since rounds 1–4 carried
   most of the pilot's value), so P_B has a test number before any
   escalation policy is built on it.
1. **L1 + L2 (days)**: server, registry, backend switch, tier L pilot on
   the 50 and the 200 with two Lean-tuned models and the general control.
   Freeze P_L.
2. **L3 (a day)**: escalation ladder over the 5,410-theorem sample and the
   mutants; measure the escalation rate and paid cents per proof.
3. **L4 (days)**: first adapter from all accepted proofs; P_L' vs P_L.
4. **L5 (days)**: W0-guided ladder-S; L-8 cost head first (a cheap run).
5. **L6 (a day, in parallel)**: queue, timers, run doctor, wire-on-seal.
6. **L7 (as needed)**: local gloss encoder, local adversaries.

## Risks, stated

- **Lean-pin drift** in local provers: they know older Mathlib names; the
  feedback rounds cope, but P_L(1) will look worse than the models' papers
  claim. Report it; do not tune the pin to the model.
- **GPU contention**: serving and training cannot overlap on 12 GB; the
  orchestrator serializes, so wall-clock grows. An eventual second GPU is
  the cheapest upgrade in the whole plan.
- **Distillation leakage**: the control sets must never enter training;
  the leakage rule is a test, not a promise.
- **Overfitting to what the gates accept**: the gates accept valid proofs,
  including ugly ones; a distilled model learns the ladder's style. The
  transition corpus and W0 are the counterweight (multi-step, state-level).
- **Weights licensing**: recorded per model in the registry; no model with
  an unclear license enters the escalation ladder.
