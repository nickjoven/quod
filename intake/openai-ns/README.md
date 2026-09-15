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

```
intake/openai-ns/build.sh        # pin check, toolchain, cache, build (12 min)
python3 scripts/lock.py intake/openai-ns/repo ComparatorChallenges.NavierStokes NavierStokes.Comparator.navier_stokes_breakdown_R3 --json
python3 scripts/axiom_gate.py intake/openai-ns/repo NavierStokes.ComparatorSolution NavierStokes.Comparator.navier_stokes_breakdown_R3 NavierStokes.Comparator.navier_stokes_breakdown_periodic --json
intake/openai-ns/fidelity.sh     # the port and the 28 locks
intake/openai-ns/checker.sh      # lean4checker over the 610-module closure (79 min)
python3 intake/openai-ns/write_claims.py
```
