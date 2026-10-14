# Intake: OpenAI's Navier–Stokes blow-up formalization

[N. Joven](https://github.com/nickjoven) — 2026 — [ORCID 0009-0008-0679-0812](https://orcid.org/0009-0008-0679-0812) — CC0 1.0

The first external claim run through quod's gates: the two Clay breakdown
alternatives (C) and (D) as formalized in
[openai/NavierStokesAndEuler](https://github.com/openai/NavierStokesAndEuler)
(Apache-2.0). Everything below was computed at the claim's own pin; nothing
was typed by hand, no gate was modified, and the statement-file bytes were
hashed and compared to a record made before the toolchain was installed.
This page states what was computed. It says nothing about the authors.

## Result

| | (C) `navier_stokes_breakdown_R3` | (D) `navier_stokes_breakdown_periodic` |
|---|---|---|
| status | **proven** | **proven** |
| lock (demonstrandum) | `3608c95f…` | `486545e2…` |
| lock (offered proof) | equal | equal |
| axioms (quod's run) | `propext`, `Classical.choice`, `Quot.sound` | same |
| independent replay | lean4checker, 610 modules, exit 0 | same run |
| closure | grounded; 3 custom structures; no custom axioms or opaques | same shape |
| fidelity to the DeepMind statement | equal in all 14 canonical forms | (descriptor) |

Claim files: [`claims/openai-ns/openai-ns-r3.yml`](../../claims/openai-ns/openai-ns-r3.yml)
and [`openai-ns-periodic.yml`](../../claims/openai-ns/openai-ns-periodic.yml).
Sealed summary: [`RESULTS.json`](RESULTS.json) (CID `c570f56e…`); every
evidence file's CID in [`evidence/CIDS.json`](evidence/CIDS.json).

## What was computed, in order

1. **Pin.** [`PIN.json`](PIN.json): commit
   `f9e8bc5b38b6e212696e8a30e3e91517af887bbd` (2026-09-10), toolchain
   `leanprover/lean4:v4.34.0-rc2`, mathlib `85e3a25e…`, Comparator
   `19e111e2…`, lean4export `cacf989b…`; the challenge file and spec by
   bytes, sha256 and blake3. `PIN-verified.txt` records that HEAD and every
   hash matched before anything was built.
2. **Build.** Only the closure of the two targets (`NavierStokes.ComparatorSolution`,
   `ComparatorChallenges.NavierStokes`): 9,372 jobs including the cached
   Mathlib, 12 minutes.
3. **Locks.** `lock.py` on the challenge statements (module
   `ComparatorChallenges.NavierStokes`, `sorry` placeholders) and on the
   same-named theorems in `NavierStokes.ComparatorSolution`. Equal for both.
   This is the offer: the proof discharges exactly the stated lock.
4. **Axiom gate.** `axiom_gate.py` on the two solution theorems: the classical
   triple and nothing else. (The solution file prints the same; this is quod's
   own run of it.)
5. **Independent checker.** No lean4checker release exists for this toolchain.
   Master `91a7f0e8…` (built for v4.29.0-rc8) was built on v4.34.0-rc2 with a
   one-line patch for a changed kernel-API signature
   ([`evidence/lean4checker-v4.34-patch.diff`](evidence/lean4checker-v4.34-patch.diff),
   binary sha256 `f2fb235a…`). It replayed every one of the 610 non-Mathlib
   modules the proof depends on: exit 0, 79 minutes with two workers (the
   default eight exhaust 15 GB).
6. **Closure.** `closure.py` from each statement: the custom constants are
   three structures per statement, all in the challenge module; no custom
   axiom, opaque, or `sorry` in the statements' closure.
7. **Fidelity (descriptor).** OpenAI's file says it was adapted from
   google-deepmind/formal-conjectures at commit `8bf45ed7`. That file was
   fetched at that commit (blob `6fd45b55…`; the later revision `2ff75e1a`
   differs only in comments and attributes), ported into this pin with
   import, attribute, notation and namespace changes only
   ([`evidence/port-diff.txt`](evidence/port-diff.txt), 22 lines), compiled,
   and locked. All 14 canonical forms — both breakdown statements and every
   custom structure's type former and constructor — are equal after the
   namespace prefix is normalized ([`evidence/fidelity.json`](evidence/fidelity.json)).
   This is recorded as a descriptor because the upstream file lives at a
   different toolchain; quod never compares locks across pins.

## What this does and does not establish

It establishes that, at the pinned commit and toolchain, the Lean
development proves the two stated theorems from the three classical axioms,
under an independent kernel replay, and that the theorems as stated are the
DeepMind formalization of the Clay alternatives up to naming. Whether that
formalization is the Clay problem is a reading, and quod records readings as
descriptors, never as status. The checker carries a recorded one-line patch;
a reader who wants zero patches can wait for a lean4checker release matching
the toolchain and replay with it.

## Reproduce

Three commands, three different assurances. None of them consults the
historical `PIN-verified.txt`; a run re-derives everything from bytes.

```
python3 intake/openai-ns/reproduce.py preflight    # can this host run it? (toolchain manager, memory, disk, no other Lean job, pin reachable)
python3 intake/openai-ns/reproduce.py integrity    # ARTIFACT INTEGRITY ONLY: every cited byte vs its CID; no Lean runs; says nothing about the proof
python3 intake/openai-ns/reproduce.py run [--toolchain-checker]   # FULL REPLAY into runs/<id>/ (about 2 h; 3.5 h with the second checker)
```

`run` clones the pinned commit into `runs/<id>/repo`, verifies commit,
toolchain, dependency revisions and the statement-file hashes afresh
(`evidence/pin-check.json`; any drift exits 2), builds the two targets,
derives the proof's non-standard import closure from the environment
header rather than a pasted list, locks the four statements, runs the axiom
gate and the closure survey, clones lean4checker at `91a7f0e8`, applies the
recorded one-line patch, builds it, replays the whole closure with two
workers, optionally replays again with the `leanchecker` binary the pinned
toolchain itself ships (no patch; chunked because it spawns one task per
module), re-fetches the upstream DeepMind file at `8bf45ed7` and locks all
14 canonical forms on both sides, then writes `claims/` and `RESULTS.json`
from that evidence alone. `RUN.json` records every command, exit code,
wall time, log CID, host and resource setting, the runner's hashes and the
quod commit, and how each result compares with the historical record. CIDs
are BLAKE3 of the bytes, so `b3sum` verifies the package without any store.
A failed command, a stale pin, an absent checker result, or a replay that
does not cover the closure fails the run with a recorded reason; `--resume`
reuses a checkout or a passing replay already in the directory. The run
holds the fleet's `flock` on `lock.lean` so it never overlaps another Lean
job on the box.

Prerequisites, measured on the recording host: 24 cores, 23 GB RAM, Lean
toolchain via `elan`, Python ≥ 3.10 with `blake3` and `pyyaml`, about 12 GB
of disk per run (Mathlib cache 6.6 GB, closure build, two checker builds).

Historical scripts (`build.sh`, `checker.sh`, `checker-chunked.sh`,
`fidelity.sh`, `supervise.sh`) are kept as the record of how the 2026-09-13
evidence was produced; they are not the reproduction path.

## Fresh runs

| run | quod commit | outcome | lean4checker | leanchecker (toolchain) | definitions | agreement with 2026-09-13 |
|---|---|---|---|---|---|---|
| [`runs/r-20261014T194322Z`](runs/r-20261014T194322Z/RUN.json) (2026-10-14) | `9fe6a00` | **proven**, **proven** | 610 modules, 2 workers, exit 0, 37.7 min; binary sha256 `f2fb235a…` | 610 modules in 153 chunks of 4, exit 0, 51.2 min; binary sha256 `ccef1bfe…` | 15 + 16 constants, digests equal | locks equal; same 610-module set; checker binary byte-identical; port diff identical; all 14 fidelity forms equal |

Measured on this host for that run (24 cores, 23.5 GB, Mathlib cache
already on disk): clone and pin check under a second, Mathlib cache 77 s,
full build 16.2 min on six CPUs (`taskset -c 0-5`; Lake has no jobs flag
in this version), each gate 4–6 s, lean4checker replay 37.7 min, leanchecker
51.2 min, port and 28 fidelity locks 2.5 min; 10.5 GB on disk for the run
directory. The run took three attempts, each recorded under
`prior_attempts` in `RUN.json`: the first stopped when the two targets
could not be imported together (Q-32, now walked per target), the second
when lean4checker's test library failed to compile on this toolchain (the
executable alone is built now). The historical replay took 79 min on the same
box with less free memory.

Every sealed record of that run: `RESULTS.json` CID `73c51b4b…`, claims
`96b4632c…` (C) and `0b8feb4e…` (D), 218 evidence files indexed in
`evidence/CIDS.json` (`0bae9fab…`); `reproduce.py integrity --run runs/r-20261014T194322Z`
re-hashes all of them, and `fixtures.py --run runs/r-20261014T194322Z` runs the failure
fixtures against that evidence.
