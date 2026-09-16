# Handoff: taking over quod on another machine

State as of 2026-09-16 (see `git log` for the commit you are on; the last
handoff was 2026-09-06 at addeb4e). No run is in flight at the time of writing; the GPU is free.

## What this is

A ledger of theorems whose status is computed, never declared, plus the
prover-in-the-loop harness that turns the gates into labels. Read in this
order:

1. `SEMANTICS.md` — the rule everything follows: proof requires a
   demonstrandum; `proven` means the demonstrandum's lock is discharged;
   everything else is a descriptor or a verdict on the offered proof.
2. `ARCHITECTURE.md` — layers, locks, gates, the calibration set.
3. `ATTEMPTS.md` — the attempts harness (rev 2: self-proof exclusion,
   ¬T prover negatives, decisions 1–5, exit conditions 1–7) and
   amendment A1 (frame first, stratified pilot, Wilson lower bound).
4. `LOCAL.md` — the local ecosystem (L1 model registry … L7) that tier L
   implements; what is measured and in which order.
5. `OPEN.yml` — every known problem, Q-1 to Q-29, with severity and
   status. Closed: Q-1, Q-8, Q-18, Q-22, Q-27, Q-28 (the last two on
   2026-09-16 after the v2 tier L runs). Q-29 (low) states the self-citing
   record convention. A known gap that is not in this file is a defect of
   the ledger.
6. `models/ADMISSIONS.md` — which local models are admitted and why;
   `models/<name>.json` is the evidence (weights by sha256 and CID).
7. `intake/openai-ns/README.md` — the first external claim run through the
   gates, at its own pin; the runbook for the next intake.
8. `AGENTS.md` — the operating rules for anyone working here (fleet rules
   by reference to homeserv/AGENTS.md).

## Bootstrap

    git clone <this repo> ~/code/quod && cd ~/code/quod
    pip install pyyaml blake3
    scripts/bootstrap.sh crouzeix        # calibration pin: lean v4.28.0, ~30–60 min (both pins: ~20 GB)
    scripts/bootstrap.sh millennium      # registry pin (v4.31.0), only when registry labels are wanted

- `blake3` is a hard prerequisite for anything that will be compared to a
  record: `lock.py` falls back to blake2b and says so in `hash_algo`, and a
  blake2b lock is a different lock. Do not produce records under the fallback.
- Per-project ket stores. `calibrate.py` defaults `KET_HOME` to
  `~/code/handoffs/.ket`; every launcher here sets
  `KET_HOME=$HOME/code/quod/.ket`. Set it explicitly, always. Without ket,
  run with `--no-ket` and the claim files carry `null` evidence CIDs.
- Trust gate, before any label is believed:
  `python3 scripts/calibrate.py --only N2,N9 --no-ket` (smoke, ~2 min), then
  `KET_HOME=~/code/quod/.ket python3 scripts/calibrate.py` → PASS 12/12 with
  non-null CIDs. A positive control failing means the gates are wrong.
- `python3 scripts/verify_records.py` is the ledger's own consistency check
  (claims, manifests, exit records, intake, calibration pins); CI runs it
  (`.github/workflows/records.yml`) and it must pass before a push to main.

Tier L extras (local prover on a GPU):

- llama.cpp built with CUDA: `~/src/llama.cpp/build` (CUDA 12.8; configure
  with `-DCUDAToolkit_ROOT=/usr/local/cuda-12.8`, else cmake picks the
  Ubuntu 11.5 headers). Observed on this box, not a repo record: Ubuntu's
  `nvidia-cuda-toolkit` (11.5) cannot target the 4070 (sm_89), and prebuilt
  `llama-cpp-python` wheels SIGILL because the i7-13700KF has no AVX-512.
  A CPU-only build sits in `~/src/llama.cpp/build-cpu` (quantize, ~9 tok/s).
- Weights: `python3 scripts/models_register.py add --name … --file|--url …
  --source <org>/<repo>@<rev> --license <as on the card>`; refuses without a
  license. `verify <name>` re-hashes. Weights live in `models/weights/`
  (gitignored); the JSON records are tracked. Admitted so far:
  `models/goedel-prover-v2-8b-q4km.json` (Q4_K_M, 5.03 GB, sha256 48326245…,
  CID da2f0d24…, converted here from the official commit dfd02e62…).
- Ports come from the homeserv table: `homeserv-port claim llama-primary`
  (8080); the launcher does this and releases on exit.

## Running

    python3 scripts/calibrate.py --only N2,N9 --no-ket   # smoke first (Q-23)
    python3 scripts/calibrate.py                          # full set, ~15 min
    python3 scripts/registry_import.py                    # seven registry demonstranda (millennium pin)

Per-declaration tools, all `<project_dir> <Module> <Decl>`-shaped: `lock.py`,
`axiom_gate.py`, `anchor_check.py`, `refute_check.py`, `closure.py`,
`hyp_mutant.py`. Each prints a reason and exits non-zero on a rejection.

Attempts harness (one Lean process at a time; every step recorded as a
transition; every accepted proof replayed through kernel, self-proof gate,
axiom gate and lean4checker):

- `attempts/run-transitions-t1.sh` — tier A (ladder-A) over sampled theorems
  and their mutants (`scripts/attempt.py`).
- `attempts/run-ladderS.sh` — ladder-S stepping prover: pilot, ¬T, test on
  `controls-4242.json`.
- `attempts/run-pilot-B.sh` — tier B (Claude Opus 5 via Message Batches):
  maps `VALID`/`SPACE` from the gitignored `~/code/quod/.env` into the
  process environment and nothing else; `--cap-cents` is sealed in the
  pre-manifest before the first request; paid batches are reused by id.
- `attempts/run-pilot-L.sh` — tier L: starts llama-server on the table
  port, then `scripts/attempt_b.py --backend openai-compat`. Usage:
  `RUN_ID=<id> attempts/run-pilot-L.sh --which pilot|test --rounds N
  --prompt-style goedel-nocot [--presentation signature] [--negate]
  [--resume] [--prover-name …]`. Sets come from `controls-2026.json`
  (frame of 250 by seeded hash, depth-stratified pilot of 50, test = rest).
- Sealing convention: the driver writes `manifest-pre-<run>.json` before the
  first request (set, prover config, weights, pins, cap) and prints
  `manifest CID: …` at the end; `manifest-<run>.json` hashes `scripts/`.
  Exit records are `attempts/exit<N>-<tier>.json`; for tier L,
  `python3 scripts/seal_tierL.py attempts/<run> attempts/exit1-<tier>.json`
  computes P per level with the Wilson 80% lower bound (A1). Tracked per
  run: `attempts.jsonl`, `manifest-*.json`, `batches.log`, `driver.log`,
  `batch-results-r*.json`, `scripts-r*.jsonl`. Raw walker output and
  per-round shards stay local (`r<N>/`).
- Into lemma: `cd ~/AI/sandbox/lemma && uv run python
  scripts/wire_quod_run.py ~/code/quod/attempts/<run> --transitions
  [--note …]`; copies shards by CID (refuses a mismatch), handles the batch
  driver's per-round shard lists.

## Results on record (first 8 hex of the CID the file cites)

| record | result | file |
|---|---|---|
| Calibration | 12/12 controls at their required status | `calib/RESULTS.json` |
| Exit 5, tier A over mutants | 142 proven of 6,152 elaborated mutants | `exit5-tierA.json`, manifest 6f947412 |
| Exit 1, tier A | pilot 0.32 frozen, test 50/200 = 0.25: FAIL | `exit1-tierA.json` |
| Exit 3, tier A ¬T | 0/200 | `exit3-tierA.json`, 17e221c5 |
| Exit 1, ladder S | P_S 0.28 frozen (285ea472), test 89/200 = 0.445: PASS | `exit1-ladderS.json`, 91c94612 |
| Exit 3, ladder S ¬T | 0/200 | `exit3-ladderS.json`, 501ae3fe |
| Exit 1, tier B | pilot 0.74/0.86/0.92 at 1/4/16 rounds (eccfd342); test 160/200 after 3 rounds, 166/200 after round 4 (694381d9): FAIL at level 1 (0.685) and level 4 (0.83) | `exit1-tierB.json` |
| Exit 3, tier B ¬T | 0/50, one round | `exit3-tierB.json`, 78bf9c3c |
| Pilot-frame defect (Q-26) | seeded pilot shallower than seeded test; both tier A and B failed in the same direction; protocol amended (A1) | `pilot-frame-diagnostic.json`, 3b527442 |
| Exit 1, tier L v1 (Goedel, closed-∀ prompt) | 3/50; P_L frozen 0.0167/0.0294 (Wilson), points 0.04/0.06 | `exit1-tierL.json`, afb2bb21 |
| Exit 3, tier L v1 ¬T | 0/50 over 4 rounds | `exit3-tierL.json`, fc6618db |
| Exit 1, tier L v2 (signature presentation, Q-27/Q-28 fixes) | 10/50; P_L frozen 0.0167/0.1209/0.1376 at 1/4/8, points 0.04/0.18/0.20 | `exit1-tierL2.json`, 9d2352ec |
| test200-L2 | 34/200 over 8 rounds: 0.095 / 0.135 / 0.17 at 1 / 4 / 8 vs frozen 0.0167 / 0.1209 / 0.1376, PASS at every level; 67 self-proof rejections; manifest 1235765f | `attempts/exit1-tierL2.json` (test block) |
| OpenAI Navier–Stokes intake | both claims **proven**: lock equality, classical axiom triple, lean4checker exit 0 over 610 modules, closure grounded, fidelity to the DeepMind statement equal in 14 canonical forms | `intake/openai-ns/RESULTS.json` c570f56e; claims cd8f7864, 855e9285 |

Tier L v1's rate is a lower bound: the Goedel completion template
re-introduced the signature binders (`intro {α} [inst : C α]`) and 45 of 312
proposals died at step 0 (Q-27); 8 walker-accepted scripts failed the batch
build because simp's argument elaborator logs an unknown lemma instead of
throwing (Q-28). v2 changed only the presentation and the walker's recover
flag; the test on the v1 presentation was deliberately not run.

## Rules that are not in the code

- Every table the runner consults is a nomination; a gate verifies it.
  Do not add a table without its gate and a control.
- A positive control failing means the gates are wrong, not the theorem.
- Statuses are computed; reasons are descriptors. Do not edit `claims/*.yml`
  by hand; prose says nothing about authors.
- Never edit `scripts/` while a run is in flight: manifests hash the whole
  directory at the end, and the record must describe what ran. Stage the
  patch outside `scripts/` and apply it after the run exits.
- Never cross-pin. Crouzeix, Millennium and each intake have their own
  toolchains, Mathlib revisions and lean4checker builds; an external claim
  is built and gated at its own pin under `intake/<name>/`.
- P is frozen before a test and never revised after (decision 2). Under A1:
  the test frame first (sealed), the pilot a seeded depth-stratified
  subsample of it, P the lower bound of an 80% Wilson interval with the
  point estimate recorded beside it. 0.32 and 0.74 stay on record with
  their failures; a rerun is a new prover config.
- Paid runs only on Nick's own go, in session, never relayed from a peer;
  a cap in cents sealed before the first request; spend recorded from
  `usage`, voided runs included.
- Credentials: `~/code/quod/.env` (gitignored), keys `VALID` and `SPACE`,
  mapped by the launcher into that process's environment only; never
  printed, logged, or written into a manifest or the ket store. `SPACE` is
  not Admin-API authorized. Workers hold no secrets.
- Processes: find a pid by `comm`, never by a pattern over `args`
  (`pkill -f`, `fuser -k` and `grep '[a]ttempt'` have killed the operator's
  own session); stop by pid; llama-server ignores its first SIGTERM with busy
  slots, the launcher escalates. One Lean process per box; `lean4checker`
  with `--num-workers=2` on a 15 GB box.
- zsh: commit messages from a file (`git commit -F`), never `-m` with a
  backtick; `set --` does not word-split; `grep -c` exits 1 on zero; no
  apostrophe inside `${VAR:?msg}`.
- Statuses live in generated files; nothing pins them yet (Q-10). Until it
  is closed, trust a status only after a rerun or `verify_records.py`.

## Next work, in order

1. DONE 2026-09-16: `test200-L2` sealed (exit1-tierL2.json `test` block,
   34/200, PASS at every level) and wired into lemma.
2. DONE 2026-09-16: pilot-L2-neg, the ¬T control for the v2 config, 0/50
   over 4 rounds (exit3-tierL2.json, manifest 48ccca5e; the v1 control is
   fc6618db), wired into lemma.
   Q-27 and Q-28 close in `OPEN.yml` after the first clean run under the
   fixes (pilot-L2 had 0 binder re-introductions and 0 walker/build
   disagreements); lemma-side: nothing consumes `on_accepted_path` yet, so
   the 24 mislabeled v1 rows only matter if it starts to.
3. Anchor descriptors for the six un-anchored Clay wrappers, **Poincaré
   first** (owner decision, 2026-09-16, PR #6). The registry's Iff theorems
   end in registry definitions, not Mathlib names; that is the recorded
   state, and it was re-read for Poincaré at the pin (`fd52071`,
   `Problems/Poincare/Millennium.lean`):
   - The constant to anchor is `MillenniumPoincare.ClayPoincareConjecture`
     (a `def : Prop`). At the pin it is, by definition,
     `Formulations.SimplyConnectedClosed3Manifold`. The registry offers
     `ClayPoincareConjecture.iff_closed_curves` and
     `ClayPoincareConjecture.iff_fundamental_group`, whose right-hand sides
     are the registry's own `Formulations.ClosedCurves` / `TrivialPi1`.
     Neither ends in Mathlib names, so neither closes the chain on its own.
   - The chain can end in Mathlib. Every custom constant under the wrapper
     is a thin definition over a Mathlib notion: `EuclideanThreeSpace` /
     `EuclideanFourSpace` are `EuclideanCoordinateSpace R n` (itself a
     registry def in `Problems.Common.Euclidean`, over `EuclideanSpace`),
     `ThreeSphere` is `Metric.sphere 0 1` in the four-space,
     `ClosedCurvesContract M` and `TrivialFundamentalGroup M` are
     `SimplyConnectedSpace M`. Each needs its own `=` or `<->` lemma of the
     shape `anchor_check.py` admits (`c x1 .. xk = rhs`, `rhs` free of `c`),
     written in an intake module at the Millennium pin and nominated under
     `anchors:` in `millennium/PIN.yml`. Rows prove nothing: the gate
     verifies each nomination at import and `registry_import.py` recomputes
     the claim; the claim file is never edited by hand.
   - Post-pin fact, not an instruction: registry `main` (commit `1fdee4b`,
     after the pin) adds `Formulations.MathlibShape`, stated in Mathlib names
     only, with an equivalence to the wrapper. Re-pinning is an owner
     decision (decision 3: one pin per subproject; never cross-pin). If the
     owner re-pins, `MathlibShape` is the natural single anchor; until then
     the chain above is the work.
   Then the remaining five wrappers in the same way.
4. Pair the second GPU box: on it, `homeserv/bootstrap.sh --role worker`
   under WSL2 with `CONTROLLER_PUBKEY` from this box's `~/.ssh/homeserv_worker.pub`;
   the NUC with the AMD GPU the same way with `GPU_VENDOR=amd` (Vulkan).
   Queued for a worker: tier L serving, W0 v3 (lemma L-8 cost head), S4 v2
   rerun on the frame-first sets, distillation (LOCAL.md L4).
5. Other admissions are decisions, not defaults: DeepSeek-Prover-V2-7B
   (MIT per card, to verify), Kimina-Prover-Distill-8B, Qwen3-8B as the
   general control (`models/ADMISSIONS.md`).
6. Q-25: a non-vacuous form of exit condition 6 (agreed, not built).
   Q-10 (guarded claim files) remains the highest-value ledger item.
7. MCP integration (`quod-mcp` has a port name, nothing behind it): deferred.

## Owner decisions on record

quod stays the name; lean4checker required for `proven`; one pin per
subproject; proof requires a demonstrandum (2026-09-06). Both repos public
(2026-09-11). Tier B test round 4 accepted as a continuation run
(test200-B-r4). Frame-first protocol (A1, 2026-09-14). Goedel-Prover-V2-8B
admitted (Apache-2.0, Qwen3-8B base, official commit dfd02e62; converted
here, no third-party GGUF) (2026-09-15). The Y40 GPU (this 4070 box) is
allocated to this workstream; 5070 pairing rescheduled (2026-09-16). The
test on the v1 tier L presentation was not run (2026-09-16). Anchor work pivots to Poincaré: it is the next of the
six un-anchored Clay wrappers, ahead of the other five (2026-09-16, PR #6).

## Companion repos

- **lemma** (`~/AI/sandbox/lemma`, public): encoders and the W0 world model
  over quod's corpus. It never computes a label; corpora arrive by CID
  through `corpora/MANIFEST.yml` (sources: mutants, attempts, dag_depth,
  transitions for tier A, ladder S, tier B, tier L v1 and v2). Ledger
  doctrine: `src/lemma/ledger.py` is the only metrics writer and a metric
  without a `metrics_cid` does not exist. Gates and failures live in
  `OPEN.yml` (L-1..L-8; L-3 closed). CI: `.github/workflows/tests.yml`
  (`uv run pytest`, CPU torch, ket built from the `ket-cli` package). Rules:
  `AGENTS.md`.
- **homeserv** (`~/AI/sandbox/homeserv`, private): fleet bootstrap.
  `./bootstrap.sh --role host|client|worker|controller`; the worker is
  key-only, forced-command, firewalled to the controller, holds no secrets
  and never initiates; the controller installs `worker-push/run/pull/status`.
  Ports are named in `ports.conf` and claimed through `homeserv-port`
  (installed at `~/.local/bin/homeserv-port`, table at
  `~/.config/homeserv/ports.conf`); `lib/wsl-boot.sh` registers a logon task
  so the distro comes back after a reboot (auto-logon is the owner's step).
  The fleet rule set is `AGENTS.md` there; quod and lemma inherit it.
