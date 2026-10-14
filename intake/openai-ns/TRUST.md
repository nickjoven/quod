# What a passing check establishes: the trust-boundary map for the openai-ns intake

[N. Joven](https://github.com/nickjoven) — 2026 — CC0 1.0 — github #8, deliverable 1

This page answers one question for one released artifact: when quod reports
the two Navier–Stokes breakdown theorems in
[openai/NavierStokesAndEuler](https://github.com/openai/NavierStokesAndEuler)
as **proven**, what exactly was checked, by what, and what was not. It says
nothing about the authors and nothing about prize eligibility. Every number
on this page resolves to a sealed record; the historical run is
[`RESULTS.json`](RESULTS.json) (2026-09-13) and the fresh-checkout runs live
under [`runs/`](runs/), each with its own `RUN.json`.

## 1. The claim in two minutes

The Clay Mathematics Institute's
[official problem statement](https://www.claymath.org/wp-content/uploads/2022/06/navierstokes.pdf)
(Fefferman) offers four ways to settle "Navier–Stokes existence and
smoothness". (A) and (B) ask for global smooth solutions with **no** external
force, on ℝ³ and on the torus ℝ³/ℤ³. (C) and (D) ask for the opposite,
**with** an external force allowed: exhibit smooth initial data and a smooth
forcing for which no global smooth solution exists. OpenAI's repository
claims (C) and (D) for every positive viscosity, formalized in Lean 4 against
Mathlib, and ships its own independent-checker setup (Comparator).

The two Lean theorems say, in ordinary words:

> For every viscosity ν > 0 there exist an initial velocity u₀ and a force f
> such that: u₀ is smooth and divergence-free; f is smooth on space × [0, ∞);
> u₀ and f satisfy the decay (whole space) or periodicity (torus) conditions
> of the Clay text; and **there is no pair (v, p)** that is smooth on
> space × [0, ∞), solves the Navier–Stokes equation with that ν, u₀ and f,
> stays divergence-free, starts from u₀, and (whole space) has square-integrable
> velocity with uniformly bounded kinetic energy, or (torus) is 1-periodic in
> space together with its pressure.

What the theorems do **not** say: they are not a blow-up for the unforced
equation. The forcing f is part of the construction; the statement is
exactly the forced breakdown that (C)/(D) call for, and a forced breakdown
leaves (A)/(B) untouched as stated. Whether the Clay committee reads its own
(C)/(D) the way the DeepMind formalization does is a reading, not a
computation, and this page records readings only as descriptors.

## 2. The map: two declarations, four documents, one pin

Everything below is at commit
[`f9e8bc5b`](https://github.com/openai/NavierStokesAndEuler/tree/f9e8bc5b38b6e212696e8a30e3e91517af887bbd)
(2026-09-10), toolchain `leanprover/lean4:v4.34.0-rc2`, Mathlib `85e3a25e`,
as recorded in [`PIN.json`](PIN.json). Nothing is compared across pins.

| | (C) whole space | (D) periodic |
|---|---|---|
| Clay alternative | "Breakdown of Navier–Stokes solutions on ℝ³", [problem statement p. 2](https://www.claymath.org/wp-content/uploads/2022/06/navierstokes.pdf#page=2) | "Breakdown of Navier–Stokes solutions on ℝ³/ℤ³", same page |
| demonstrandum (the challenge, a `sorry` placeholder) | `NavierStokes.Comparator.navier_stokes_breakdown_R3` in [`ComparatorChallenges/NavierStokes.lean`](https://github.com/openai/NavierStokesAndEuler/blob/f9e8bc5b38b6e212696e8a30e3e91517af887bbd/ComparatorChallenges/NavierStokes.lean) | `…navier_stokes_breakdown_periodic`, same file |
| offered proof | same name in [`NavierStokes/ComparatorSolution.lean`](https://github.com/openai/NavierStokesAndEuler/blob/f9e8bc5b38b6e212696e8a30e3e91517af887bbd/NavierStokes/ComparatorSolution.lean), one line: `exact ComparatorBridge.navier_stokes_breakdown_R3 nu hnu` | same, `…_periodic` |
| definitions the proof's statement uses | [`NavierStokes/ComparatorDefinitions.lean`](https://github.com/openai/NavierStokesAndEuler/blob/f9e8bc5b38b6e212696e8a30e3e91517af887bbd/NavierStokes/ComparatorDefinitions.lean), a copy of the challenge file's definitions; the solution never imports the challenge module | same |
| upstream formalization the challenge was adapted from | [google-deepmind/formal-conjectures `FormalConjectures/Millenium/NavierStokes.lean` @ `8bf45ed7`](https://github.com/google-deepmind/formal-conjectures/blob/8bf45ed70d48b2b2a501de9c00b26bfa38c573ee/FormalConjectures/Millenium/NavierStokes.lean) (the commit the challenge file's header cites) | same |
| the paper | ["Finite time blowup for Navier–Stokes"](https://cdn.openai.com/pdf/32d9f210-8b73-45e0-91bc-82a30aef8a9a/navier-stokes.pdf), linked from the repository README | same |

### Hypotheses and quantifiers, in order

Both theorems have the shape `∀ ν, ν > 0 → ∃ u₀ f, H₁ u₀ ∧ H₂ f ∧ ¬ ∃ v p, S ν u₀ f v p`.

- `nu : ℝ`, `hnu : nu > 0` — the only explicit hypotheses (the lock records
  them; [`claims/openai-ns/openai-ns-r3.yml`](../../claims/openai-ns/openai-ns-r3.yml) `descriptors.hypotheses`).
- `u₀ : ℝ³ → ℝ³` with `InitialVelocityConditionDecay` (C) /
  `InitialVelocityConditionPeriodic` (D): divergence-free (the divergence is
  the trace of the Fréchet derivative, with the junk value 0 where the field is
  not differentiable), `C^∞`, and either every derivative decays faster than
  any polynomial in |x| (Clay condition 4) or the field is 1-periodic in each
  coordinate (condition 8).
- `f : ℝ³ → ℝ → ℝ³` with `ForceConditionDecay` / `ForceConditionPeriodic`:
  `C^∞` on ℝ³ × [0, ∞) (as a function of the pair, with `ContDiffOn` on that
  set), and every derivative decays faster than any polynomial in |x| + t
  (condition 5) or, periodically, in t alone (condition 9) with f 1-periodic in
  space for every t ≥ 0.
- The negated existential: no `v : ℝ³ → ℝ → ℝ³`, `p : ℝ³ → ℝ → ℝ` with
  `NavierStokesExistenceAndSmoothnessRn` / `…Periodic`: the PDE
  `∂ₜv + (v·∇)v = νΔv − ∇p + f` holds for every x and every t ≥ 0, where the
  time derivative is `derivWithin` on `[0, ∞)` and the transport term is the
  Fréchet derivative of `v(·, t)` applied to `v(x, t)`; `v(·, t)` is
  divergence-free for every t ≥ 0; `v(·, 0) = u₀`; v and p are `C^∞` on
  ℝ³ × [0, ∞); and, whole space, `‖v(·, t)‖` is in L² for every t ≥ 0 with
  `∃ E, ∀ t ≥ 0, ∫ ‖v x t‖² dx < E` (condition 7), or, torus, v and p are
  1-periodic in space for every t ≥ 0 (condition 10 and the Clay errata for the
  pressure).

A candidate solution therefore refutes the theorem only if it meets **every**
clause; the theorem is refuted by nothing less. Conversely the theorem is
established by any u₀, f meeting the hypotheses for which every candidate fails
at least one clause. The Lean statement is general in the dimension n; the
theorems instantiate n = 3.

## 3. Five things, kept separate

quod's status `proven` is the conjunction of exactly three computed gates
(statement identity, permitted axioms, independent replay). Build success is a
precondition of all three, and correspondence to prose is never a gate.

### 3.1 Statement identity (the lock)

`scripts/lock.py` elaborates the declaration inside the project's own
environment, prints its type with `pp.all` (every implicit argument, instance
and universe written out), erases binder names and renames universes, and
hashes the string with BLAKE3. The demonstrandum's lock and the offered
proof's lock are equal: `3608c95f…` (C), `486545e2…` (D). This is equality of
what the two declarations **say**, with every constant written by full name.

What the lock does not cover, and what this intake adds: the three custom
constants in each statement (`InitialVelocityConditionDecay`,
`ForceConditionDecay`, `NavierStokesExistenceAndSmoothnessRn`, and their
periodic counterparts) are declared **twice** in the repository under the same
names, once in the challenge module and once in `ComparatorDefinitions`, and
the solution imports only the latter. Lock equality says the two statements
read the same; it cannot say the words mean the same, because a name is a
name. `scripts/defs_digest.py` closes that gap: in each environment it walks
every non-standard constant reachable from the statement through types,
definition values and constructor types, prints each one's canonical type and
value, and hashes the sorted rows. The fresh-checkout run computes the digest
on both sides and `write_claims.py` requires them to be equal when the record
is present (`definitions_identical`); a textual diff of the two files shows the
definitions module is the challenge file minus the two `sorry` theorems, but
the digest is the record, the diff is not. The historical 2026-09-13 run did
not make this check; its status rests on lock equality alone and is preserved
as such (OPEN.yml Q-32).

### 3.2 Permitted axioms

`scripts/axiom_gate.py` runs `#print axioms` on the two solution theorems
inside the environment and fails unless each axiom set is a subset of
`{propext, Classical.choice, Quot.sound}`. `sorryAx` fails it. Result:
exactly the classical triple for both ([`evidence/axioms-solution.json`](evidence/axioms-solution.json)).
This is quod's own run; the solution file prints the same lines at the end of
`ComparatorSolution.lean`, and the Comparator challenge spec names the same
three as permitted.

### 3.3 Elaboration and build

`lake build NavierStokes.ComparatorSolution ComparatorChallenges.NavierStokes`
exits 0: the Lean elaborator and kernel accepted every declaration in the
proof's import closure while compiling it. Historical wall time 12 minutes
after the Mathlib cache (9,372 jobs including Mathlib's cached ones). A build
that exits 0 is the precondition for every other gate, not a result on its
own: the compiler that built the proof is the same program whose output the
replay re-checks.

### 3.4 Independent replay

The replay re-sends every declaration of every non-standard module in the
proof's import closure to the kernel from scratch, in a separate process that
never ran the elaborator on that code. Two checkers are recorded:

- **lean4checker**, upstream commit `91a7f0e8` (written for v4.29.0-rc8),
  built on v4.34.0-rc2 with a one-line patch
  ([`evidence/lean4checker-v4.34-patch.diff`](evidence/lean4checker-v4.34-patch.diff)).
  The patch supplies the `maxRecDepth` argument (512) that this toolchain
  added to the kernel entry point `Environment.addDeclCore`, and changes
  nothing else; `doCheck` stays true. A bound that is too small can only make
  the kernel reject a declaration (a non-zero exit), never accept one, so the
  patch cannot turn a rejection into acceptance. The toolchain's own checker
  (next item) passes 0 for the same argument. Historical: 610 modules,
  `--num-workers=2`, exit 0, 79 minutes, binary sha256 `f2fb235a…`.
- **leanchecker**, shipped inside the pinned toolchain itself
  (`~/.elan/toolchains/…/bin/leanchecker`, source `src/lean/LeanChecker.lean`):
  lean4checker upstreamed into Lean, needing no patch. Its own docstring says it
  is "not an external verifier, simply a tool to detect environment hacking":
  it is built from the same source tree and kernel as the compiler. It spawns a
  task per module with no worker cap, so the fresh run drives it in chunks of
  four modules per process. Recorded as a descriptor.

The module set is derived, not pasted: the fresh run reads
`env.header.moduleNames` of an environment importing the two targets and keeps
every module outside the pinned standard libraries
(`Init Lean Std Mathlib Batteries Aesop Qq ProofWidgets Plausible ImportGraph LeanSearchClient Lake Cli`);
[`evidence/closure-modules.txt`](evidence/closure-modules.txt) is the historical
list, and `RUN.json` records whether the derived set equals it.

What the replay trusts and does not re-check:

| inside the replay | outside it (trusted as shipped) |
|---|---|
| every constant of the 610 non-standard modules, re-added to a kernel environment one by one | **Mathlib and the other standard libraries**: their `.olean` files are imported, not replayed; they come from Mathlib's build cache (`lake exe cache get`), content-addressed by Mathlib's own tooling, from leanprover-community's Azure store |
| the kernel's type checking of each declaration, including inductive types and recursors | **the Lean kernel itself** (C++, inside the elan-downloaded toolchain), the `.olean` deserializer, and the operating system |
| constructor and recursor identity against the kernel's own generation | **the toolchain binaries** downloaded by elan for `v4.34.0-rc2`, verified by elan's channel mechanism, not by quod |
| exit code 0 only if no declaration throws a kernel exception | **the checker's build**: lean4checker was compiled on this box by the same Lake/Lean; the binary's sha256 is recorded and compared with the historical one, but a different-but-honest build is not a failure |

Comparator, the checker OpenAI ships with the challenge (lean4export to a
text format, then nanoda, a separate kernel implementation in Rust, inside a
`landrun` sandbox), is a stronger independence claim than either checker above
because it re-implements the kernel. quod has not run it; it is outside this
record and listed in OPEN.yml as a follow-up.

### 3.5 Correspondence to the mathematical prose (descriptor only)

Three different gaps live here, and quod closes exactly one of them:

1. **Challenge file ↔ DeepMind's formalization.** The challenge header says it
   was adapted from formal-conjectures at `8bf45ed7` with imports, attributes,
   namespace and notation changed. quod fetched that file at that commit
   (git blob `6fd45b55…`), ported it into **this** pin with the same four
   kinds of change ([`evidence/port-diff.txt`](evidence/port-diff.txt), 22
   changed lines), compiled it as `Intake.UpstreamNavierStokes`, and locked
   all 14 canonical forms on both sides: the two theorems, the six structures'
   type formers and their six constructors. All 14 are equal once the
   namespace prefix `NavierStokes.Upstream.` / `NavierStokes.Comparator.` is
   normalized ([`evidence/fidelity.json`](evidence/fidelity.json)). This is a
   **same-pin port**, not a cross-pin lock: the upstream repository lives at
   another toolchain, and quod never compares locks across pins (decision 3).
   The upstream file's `main` at pin time (`2ff75e1a`) differs from `8bf45ed7`
   only in comments and attributes ([`evidence/upstream-8bf45ed7-vs-2ff75e1a.diff`](evidence/upstream-8bf45ed7-vs-2ff75e1a.diff)).
2. **DeepMind's formalization ↔ the Clay text.** Not computed and not
   computable here: whether `derivWithin` on `[0, ∞)`, the junk-value
   divergence, `ContDiffOn` on the half-space, the errata's periodic pressure
   and the bounded-energy clause are *the* Clay conditions is a reading by
   specialists. The formalization's own docstrings cite Fefferman's numbered
   conditions; quod records that as a descriptor.
3. **The paper's prose ↔ the Lean lemmas it says it formalizes.**
   arXiv:2610.08144 (Bastounis, Circelli, Hansen, 2026-10-06) argues that
   parts of the Lean development prove different or weaker lemmas than the
   paper's prose states. That paper does not dispute the Lean proofs, and
   nothing in quod's gates touches it: the gates check that the Lean theorems
   as stated are proven, not that the paper describes them faithfully. It is
   recorded as a descriptor on the intake and it changes no status.

## 4. The checker's dependency closure, concretely

The proof's closure is 610 modules: the challenge module plus 609 under
`NavierStokes.*` (the `Euler` library is not in it). Every one is replayed.
Everything they import from Mathlib (and from Batteries, Aesop, Qq,
ProofWidgets, Plausible, ImportGraph, LeanSearchClient, Comparator's own
dependencies as resolved in `lake-manifest.json`) is trusted as cached
`.olean` bytes. That is the same boundary Mathlib users accept daily, and it is
the boundary a reader who wants more would push on next, with a `--fresh`
replay of one module into an empty environment (Q-7) as the next step and
Comparator's nanoda run after that.

## 5. Historical record and fresh reproduction

The 2026-09-13 run ([`README.md`](README.md), [`RESULTS.json`](RESULTS.json)
CID `c570f56e…`) is preserved byte for byte;
`python3 intake/openai-ns/reproduce.py integrity` re-hashes every cited file
against its CID and passed on 2026-10-14. That check is artifact integrity: it
proves the bytes on disk are the bytes the records describe and nothing about
the proof. The fresh-checkout reproduction (`reproduce.py run`) re-derives
every gate from a new clone, and its `RUN.json` carries a
`historical_agreement` block: whether the locks, the module set, the checker
binary, the port diff and the statuses came out the same. The first such run, [`runs/r-20261014T194322Z`](runs/r-20261014T194322Z/RUN.json)
(2026-10-14), came out **proven** for both claims with every comparison in
agreement: identical locks, the same 610-module closure derived from the
environment, a lean4checker binary with the same sha256 as September's, the
definitions digests equal on both sides, the toolchain's own `leanchecker`
exiting 0 over all 610 modules, and all 14 fidelity forms equal. The runs and
their outcomes are listed in [`README.md`](README.md) § Fresh runs.
