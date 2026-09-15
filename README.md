# quod

[N. Joven](https://github.com/nickjoven) — 2026 — [ORCID 0009-0008-0679-0812](https://orcid.org/0009-0008-0679-0812) — CC0 1.0

[![records](https://github.com/nickjoven/quod/actions/workflows/records.yml/badge.svg)](https://github.com/nickjoven/quod/actions/workflows/records.yml)

A ledger for Lean 4 theorem claims in which status is **computed by gates, never
typed by hand**. A claim is a Lean type identified by a lock (a hash of its
canonical elaborated form); a proof discharges it only if the locks match
byte-for-byte, the axiom set is exactly `{propext, Classical.choice,
Quot.sound}`, and `lean4checker` replays the module. The gate suite is
calibrated on **both polarities**: positive controls that must reach `proven`
(a published Crouzeix-conjecture proof, a theorem proven here from scratch, a
Mathlib theorem restated under another name) and negative controls that must
be rejected *with the reason attached*, including a forged anchor row, an
anchor-laundering chain, a forged refutation, and a stale lock. Alongside the
ledger: a single-process Mathlib walker that produced a 296,187-declaration,
gate-labeled corpus, and an `Expr`-level statement-mutant generator over
sampled Mathlib theorems.

The name is *quod erat demonstrandum*: the only thing that enters is what was
actually demonstrated.

## Results, in one table

Every number is read from a sealed record named in its row; the record's CID
is the citation. Rates are prover-relative (the named prover, its recorded
budget) and never a statement about truth.

| what | result | record |
|---|---|---|
| Calibration, both polarities | 12/12 controls at their required status, with reasons | [`calib/RESULTS.json`](calib/RESULTS.json) |
| External claim: OpenAI's Navier–Stokes blow-up (Clay C and D) at its own pin | both **proven**: lock equality, classical axiom triple, independent lean4checker replay of 610 modules; statement equal to the DeepMind original in all 14 canonical forms (descriptor) | [`intake/openai-ns/`](intake/openai-ns/README.md), CID `c570f56e…` |
| Tier A automation ladder on sampled Mathlib theorems | pilot 0.32 frozen, test 0.25 (fails its own gate; see Q-26) | [`attempts/exit1-tierA.json`](attempts/exit1-tierA.json) |
| Tier B, a frontier model with the theorem's name hidden and search tactics forbidden, every proof replayed and gated | pilot 0.74 / 0.86 / 0.92 at 1 / 4 / 16 rounds; test 0.685 / 0.83 at 1 / 4 rounds (below the frozen P at both levels: Q-26); 0 of 50 negated statements accepted; $76 all-in | [`attempts/exit1-tierB.json`](attempts/exit1-tierB.json), [`exit3-tierB.json`](attempts/exit3-tierB.json) |
| Statement mutants with a prover-relative verdict | 6,152 elaborated mutants, 142 proven, every attempt lock-verified against the mutant corpus | [`attempts/exit5-tierA.json`](attempts/exit5-tierA.json) |
| Proof-state transitions (the world-model corpus) | 107,626 tactic steps over goal states identified by lock, three provers, censored budget steps marked | run manifests under [`attempts/`](attempts/), consumed by [lemma](https://github.com/nickjoven/lemma) |
| Pilot-frame defect found by the controls themselves | the seeded pilot is shallower than the seeded test; protocol amended (A1) | [`OPEN.yml`](OPEN.yml) Q-26, diagnostic CID `3b527442…` |


## What is here

| piece | path | what it does |
|---|---|---|
| Statement lock | [`scripts/lock.py`](scripts/lock.py) | Canonical type = binder names erased, universes renamed `u_0..`, printed under `pp.all` + `pp.universes` + `pp.fullNames`; lock = BLAKE3 of that string. Also lists explicit `Prop` hypotheses, custom (non-library) constants, and whether the type unfolds to `True`. |
| Axiom gate | [`scripts/axiom_gate.py`](scripts/axiom_gate.py) | `#print axioms` parsed; anything outside the standard triple is a rejection, `sorryAx` is "incomplete". This gate can fail. |
| Anchor shape gate | [`scripts/anchor_check.py`](scripts/anchor_check.py) | An anchor for a custom constant `c` is admissible only as `c x₁ … xₖ = rhs` or `↔ rhs` over distinct bound variables with `rhs` free of `c`; the runner recurses through `rhs` so the chain must end in the pinned libraries. |
| Refutation gate | [`scripts/refute_check.py`](scripts/refute_check.py) | A nominated refutation must have type `¬ T` with `T` canonically equal to the claim. |
| Closure survey | [`scripts/closure.py`](scripts/closure.py) | Definitional closure of every custom constant; `grounded` iff it ends in the pinned libraries with no axiom, opaque, or sorry inside. |
| Hypothesis mutant | [`scripts/hyp_mutant.py`](scripts/hyp_mutant.py) | Delete a hypothesis; the proof must stop compiling, else the premise is dead. |
| External kernel | `lean4checker` (cloned by bootstrap) | Replays the declaring module through an independent checker. |
| Calibration runner | [`scripts/calibrate.py`](scripts/calibrate.py) | Runs the 12 controls under [`SEMANTICS.md`](SEMANTICS.md), computes status and descriptors, writes `claims/*.yml` and `calib/RESULTS.json`, stores every raw gate output by content hash. |
| Corpus walker | [`scripts/CorpusWalk.lean`](scripts/CorpusWalk.lean) + [`scripts/corpus_extract.py`](scripts/corpus_extract.py) | One Lean process imports Mathlib once and walks the environment: per-declaration heartbeat budgets, a fold-to-`Name`s selection (the earlier `toList` spiked to 14.9 GB RSS and was OOM-killed), an explicitly flushed output handle, and a driver watchdog that kills a stalled walker and resumes past exactly the hung declaration. `--selftest` holds the walker field-exact against `lock.py` before any full run. |
| Mutant walker | [`scripts/MutantWalk.lean`](scripts/MutantWalk.lean) + [`scripts/mutant_extract.py`](scripts/mutant_extract.py) | `Expr`-level statement mutants (binder-level hypothesis deletion, `And`/`Or`, `Eq`/`Ne`, `0`/`1` swaps) plus proof-side `sorry`/axiom injection with verdicts fixed by construction. |
| Attempts harness | [`scripts/AttemptWalk.lean`](scripts/AttemptWalk.lean) + [`scripts/attempt.py`](scripts/attempt.py), [`scripts/attempt_b.py`](scripts/attempt_b.py) | Provers in the loop (a tactic ladder, a stepping search, a frontier model through the Batches API), each proof kernel-checked, screened for self-proof (no constant with the demonstrandum's lock), replayed through the gates, and every tactic step recorded as a transition. Controls per prover: frozen P, a test set, and ¬T with halt-on-accept. [`ATTEMPTS.md`](ATTEMPTS.md). |
| Claim intake | [`intake/openai-ns/`](intake/openai-ns/README.md) | An external Lean claim pinned by commit and file hash, built at its own toolchain, and run through the same gates with an independent checker; statement fidelity to an upstream formalization as a descriptor. |
| Consumer | [lemma](https://github.com/nickjoven/lemma) | The declarations corpus and the mutant corpus, verified by these manifest CIDs, are the training data for lemma: self-supervised statement encoders whose every metric is content-addressed against these labels. |
| From-scratch proof | [`calib/Quod/P2.lean`](calib/Quod/P2.lean) | Sharpness of the Crouzeix constant 2 at the 2×2 nilpotent Jordan block, and the refutation of the constant-1 variant from the same witness. |
| Registry import | [`scripts/registry_import.py`](scripts/registry_import.py), [`millennium/PIN.yml`](millennium/PIN.yml) | One application: the seven lean-dojo `clay_prize_*` statements imported as demonstranda at their own pin. All seven are `stated`; Riemann is anchored to Mathlib's `RiemannHypothesis` through the registry's own `Iff` theorems; the other six are unanchored because Mathlib has no named statement for them. |

For depth, read in this order: [`SEMANTICS.md`](SEMANTICS.md) (the rule
everything follows), [`ARCHITECTURE.md`](ARCHITECTURE.md) (layers, gates,
the run records), [`OPEN.yml`](OPEN.yml) (every known problem, with severity
and status), [`HANDOFF.md`](HANDOFF.md) (taking over on another machine).

## Calibration

Every control's demonstrandum, what is offered against it, and the outcome
it must reach on status *and* descriptors. From `SEMANTICS.md`.

| id | demonstrandum | offered | required |
|---|---|---|---|
| P1 | `crouzeixConjecture` (jinshanmu/CrouzeixConjecture @ `f9d5c8d`) | itself | proven; grounded; 3/3 anchored; hyps 0 |
| P2 | `QuodP2.sharp_two` | itself | proven |
| P3 | restated infinitude of primes | itself | proven; dedup = Mathlib lock |
| N1 | induction template (a `step` hypothesis over a private predicate) | itself | proven; hyps = [step]; registry_match none; anchored none |
| N2 | `True` behind a name | itself | proven; reduces_to_True |
| N3 | theorem on an `axiom` | itself | stated; proof rejected: extra axiom |
| N4 | Crouzeix with constant 1 | refutation `N4_refuted` | refuted |
| N5 | P1 with a stale recorded lock | itself | drift-fail |
| N6 | N1 with a forged anchor row | itself | proven; anchor rejected: shape |
| N7 | N1 with a laundering anchor | itself | proven; anchor rejected: chain |
| N8 | N4 with a forged refutation | `sharp_two` as refutation | stated; refutation rejected: shape |
| N9 | P1's demonstrandum | `sharp_two` as proof | stated; proof rejected: lock mismatch |

Recorded result: **PASS 12/12** on 2026-09-06 (14m53s), every control at its
required status and descriptors; the SHA-256 of every runner script is
recorded alongside in [`calib/RESULTS.json`](calib/RESULTS.json). The
positive controls are the point: a gate suite that has only ever said no is
uncalibrated.

## Run / reproduce

```sh
pip install pyyaml blake3          # blake3 optional (falls back to blake2b, and says so)
scripts/bootstrap.sh crouzeix      # or: millennium | all. ~30–60 min, ~20 GB.
```

Everything heavy (the pinned Mathlib builds, Jin's repository, the lean-dojo
registry, both `lean4checker` builds) is gitignored and reproduced by
`bootstrap.sh` from the pins recorded in it.

```sh
python3 scripts/calibrate.py --only N2,N9 --no-ket   # smoke first, ~2 min
python3 scripts/calibrate.py                          # full set, ~15 min, PASS 12/12 expected
python3 scripts/registry_import.py                    # seven registry demonstranda, ~4 min
python3 scripts/corpus_extract.py --selftest          # walker vs lock.py, field-exact, before any full run
python3 scripts/corpus_extract.py --run-id <id>       # full corpus walk (hours)
```

Per-declaration tools are all `<project_dir> <Module> <Decl>`-shaped and
exit non-zero with a printed reason on rejection: `lock.py`,
`axiom_gate.py`, `anchor_check.py`, `refute_check.py`, `closure.py`,
`hyp_mutant.py`.

**Evidence.** The `evidence:` CIDs in `claims/*.yml`, `calib/RESULTS.json`
and the corpus manifests point into a local content-addressed store
([ket](https://github.com/nickjoven/ket)) that is not published with this
repository. The claim files, `RESULTS.json`, and the manifests *are* the
run record; the raw gate outputs behind each CID are reproduced by rerunning.
Without a ket store, pass `--no-ket` and the CIDs are written as `null`.

## Decisions

Each row is a design decision I made, the alternative it displaced, and the
rationale as it is recorded in this repository.

| decision | alternative rejected | objective rationale (as recorded) | where |
|---|---|---|---|
| Proof requires a demonstrandum: `proven` means the registered lock is discharged; descriptors never gate status | Cap status at `stated` until every custom constant is anchored | Under the cap, six of seven registry problems were unreachable by any proof at their pin; under the demonstrandum rule the induction template is `proven` as the implication it is, and the mismatch is caught by `hypotheses`, `registry_match`, and the lock relation instead of a status | `SEMANTICS.md`; `OPEN.yml` Q-22 (option B) |
| Hypotheses are part of the lock; no `conditional` status | A `conditional` status for sorry-free proofs with undischarged premises | `conditional` was promised but never computed; the mutant list was hand-typed for one control; a `(step : …) : …` theorem computed `proven` with the premise silently inside the lock. Listing binders from the elaborated type makes them a descriptor on every claim | `OPEN.yml` Q-1; `SEMANTICS.md` |
| `lean4checker` is required for `proven`, and the axiom gate is a separate check | Trust `#print axioms` alone, or the checker alone | Recorded observation: the checker exits 0 on N3 (an `axiom`) and N4 (a false statement); it certifies kernel consistency of the environment, not axiom freedom | `ARCHITECTURE.md` §7 run record, §10 decision 2 |
| One pin per subproject; never cross-pin a claim | Compare locks across Lean/Mathlib versions | The canonical form is a pretty-printer string at one version; cross-pin dedup is impossible by construction and is stated as a limit rather than papered over | `ARCHITECTURE.md` §10 decision 3; `OPEN.yml` Q-15 |
| Every table the runner consults is a nomination verified by a gate | Hand-typed maps (anchor table, `refuted_by`) | Found twice on 2026-09-06: one forged anchor row turned N1 into `proven` (fixed by `anchor_check.py` + N6/N7); any axiom-clean theorem could mark any claim `refuted` (fixed by `refute_check.py` + N8) | `ARCHITECTURE.md` §7 rechecks; `OPEN.yml` Q-8, Q-16; `HANDOFF.md` |
| `grounded` and `anchored` are separate descriptors | One "anchored" bit | At the Millennium pin all seven wrappers are grounded (closure ends in Mathlib, nothing hidden) but only Riemann has an `Iff` to a Mathlib-named statement; conflating the two either blocks six problems or overstates fidelity | `OPEN.yml` Q-21, Q-22; `ARCHITECTURE.md` §7b |
| One Lean process per walk, not one per check | Spawn a Lean process (importing Mathlib) per gate per claim | 10 controls took 9m36s that way; hundreds of thousands of declarations need one environment load. `CorpusWalk.lean` walks 296k declarations in one process | `OPEN.yml` Q-13; `scripts/CorpusWalk.lean` header |
| `readable_pp` is the encoder input; `pp.all` stays the lock identity | Feed the canonical `pp.all` string to downstream models | `pp.all` p50 ≈ 479 tokens put 47.5% of statements over a 512-token sequence; the readable form is far shorter and the lock is unchanged | `scripts/CorpusWalk.lean` (`emitDecl` comment) |
| Smoke test before any full run; runner SHA-256 recorded with the run | Edit the runner while a run is in flight | A refactor shipped with its main loop broken while a run was live; the run had loaded the old file. Nothing was misrecorded, but nothing could have proven that without the hashes | `OPEN.yml` Q-23; `HANDOFF.md` |
| Refuse to compute statuses when `lake`/`lean` are off `PATH` | Let every gate degrade to `lock-fail` | Observed live 2026-09-06: with `~/.elan/bin` off `PATH`, every control degraded and overwrote the recorded claim files | `scripts/calibrate.py` preflight comment |
| Per-declaration heartbeat cap and wall-clock watchdog in the walker; hung declarations are listed, not swallowed | Unbounded per-declaration work | `ppExpr` is not reliably heartbeat-checked; one exploding type stalls the whole walk. Announcing each declaration before processing lets the driver resume past exactly that one; skips go in the manifest as a finding | `scripts/CorpusWalk.lean`; `scripts/corpus_extract.py` docstring |
| A ket failure aborts the run rather than degrading to `null` CIDs | Treat a store failure like `--no-ket` | Evidence was promised; its silent absence would be indistinguishable from a deliberate `--no-ket` run | `scripts/calibrate.py` (`ket_put`) |

## What is not here / open

[`OPEN.yml`](OPEN.yml) lists every known problem with an id, a severity, and
a status; a known gap that is not listed there is a defect of the ledger.
The ones that matter most for reading this repository:

- Statement-mutant gate verdicts (`gate_verdict`) are `null` in the mutant
  corpus; only proof-side mutants carry a verdict, fixed by construction.
  Labeling statement mutants needs a proof attempt per mutant (Phase 3b).
- Six of the seven Clay wrappers are unanchored to a Mathlib-named
  statement, because Mathlib has none; their fidelity rests on the registry's
  definitions (all grounded) plus review (Q-21).
- `claims/*.yml` and `RESULTS.json` are unguarded plain files; a status can
  be edited by hand and nothing notices until a rerun (Q-10). Trust a status
  only after a rerun.
- `lean4checker` at the Millennium pin (Lean v4.31.0) is an unreleased
  upstream build, because no matching release existed (Q-20).
- `OPEN.yml` is read by humans; one entry's `status:` line contains an
  unquoted colon and does not parse under a strict YAML loader.

## Authorship

The code and documentation were written with Claude (Claude Code) as a
co-author; the `Co-Authored-By` trailers are kept on every commit. The design
decisions are mine and are the table above.

## License

[CC0 1.0 Universal](LICENSE). To the extent possible under law, the author
has waived all copyright and related rights to this work.
