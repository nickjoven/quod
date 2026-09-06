# quod — a ledger of theorems whose status is computed, not declared

Working name (rename freely). *Quod* as in *quod erat demonstrandum*: the
only thing that enters is what was actually demonstrated.

## 0. What this is for, and the bar it must clear

Target program: iterate on the Millennium Prize problems. Expected output:
no solutions. Real output: a shared, content-addressed corpus of locked
statements, checked reductions and lemmas, and a gate suite that is
calibrated on BOTH polarities, so that a claim marked correct is correct
and a claim of the AIX / "P = NP was `True`" kind is rejected with the
reason attached.

The bar, set by the owner: *that nothing could be claimed as correct is a
failure.* Every prior audit in this stack (harmonics, proslambenomenos)
produced demotions and no positive control. A gate suite that has only ever
said no is uncalibrated. So the first deliverable is not a gate; it is a
**calibration set** with positive controls that MUST pass and negative
controls that MUST fail, run on a solved problem (Crouzeix) before a single
Millennium statement is touched.

Rule of the house: **no intuition, only mathematical requirement.** Nothing
is a claim unless it has a Lean type. Prose is a projection (a label on a
node), never an identity and never a status.

## 1. Verifier layer (L0)

- Lean 4 kernel + Mathlib at a pinned revision. One pin per subproject
  (Crouzeix calibration: `leanprover/lean4:v4.28.0`, mathlib `8f9d9cff`,
  Jin's tip `f9d5c8d`; Millennium: lean-dojo/LeanMillenniumPrizeProblems,
  `v4.31.0`, mathlib `fabf563a`). Pins are LAW entries; changing one is a
  ledger event with hashes, exactly as gate files are in proslambenomenos.
- Three independent checks per declaration, each with a captured output
  that is stored by CID:
  1. `lake build` of the declaring module, zero errors.
  2. **Axiom gate that can fail**: `#print axioms` output parsed; anything
     outside `{propext, Classical.choice, Quot.sound}` fails; `sorryAx`
     fails. (This is the ten-line fix Jin's repo never had; its
     `AxiomAudit.lean` could not fail.)
  3. `lean4checker` replay of the environment through an external kernel
     (catches environment manipulation, `implemented_by`, unsafe
     declarations that `#print axioms` does not see).
- Source scan: `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by`,
  `extern`, `unsafe`, `set_option` in a claim's transitive module closure
  are listed, not merely grepped; any hit outside Mathlib downgrades status.

## 2. Statement locks (L1) — identity by structure

A claim IS a Lean declaration's type. Its identity is

    lock = BLAKE3( canonical elaborated type )

where canonical means `pp.all`, fully qualified constants, universe
parameters normalized, no names of hypotheses (binder names are
projection). This is gnosis's thesis with a real canonicalizer: the
elaborator solves the "language problem" gnosis flagged, for this domain.
Two people who state the same theorem under different names produce one
node.

**Custom definitions are the trapdoor** (the AIX `Tower` namespace; the
`def Claim : Prop := True` case). So the lock also records the transitive
set of constants in the type that are NOT in pinned Mathlib. Each such
constant needs an **anchor**: a checked `Iff` or `=` lemma relating it to a
Mathlib notion, or a reviewed definition edge in the corpus. A claim whose
type depends on an unanchored custom constant can be at most `stated`,
never `proven`, whatever its proof does.

**Target fidelity for the Millennium problems**: the registry types are the
lean-dojo `clay_prize_*` declarations at the pinned revision. A claim
counts against a Millennium problem only if it discharges that exact lock
or a lock joined to it by a checked `Iff`. There is no other route to the
word "solved" in this ledger, and nobody can type it by hand.

## 3. Claim ledger (L2) — status is computed

Ported from proslambenomenos (`scripts/check_claims.py`: "statuses are
computed, never declared"), with the physics fields replaced:

    claims/<slug>.yml
      statement: >          informal projection, for humans
      lean: Module.decl     the declaration
      lock: <cid>           pinned canonical type
      custom_constants: []  transitive non-Mathlib constants + anchor ids
      hypotheses: []        machine-extracted, each with mutant result
      controls: []          calibration role, if any (positive|negative)
      status: <computed>

Statuses, in order of strength:

- `stated`      type elaborates; body may be `sorry`.
- `conditional` sorry-free proof whose premises include named claim ids or
                explicit hypotheses not discharged (the AIX template
                `(step : ∀ n, T n → T (n+1)) : ∀ n, T n` lands here, with
                `step` listed, and can never be promoted by wording).
- `proven`      all three L0 checks pass, axiom set exact, every custom
                constant anchored, every hypothesis mutant killed, witness
                present.
- `refuted`     the negation is `proven`.
- `superseded`  replaced by a stronger lock, edge kept.

**Mutants** (the falsifier discipline, transposed to proofs):

- hypothesis-deletion: for each hypothesis, the same proof with it removed
  must FAIL to compile. A hypothesis whose removal changes nothing is
  flagged (dead premise), which is also how vacuous strengthening is caught.
- satisfiability witness: an `example` instantiating all hypotheses must
  compile (kills theorems true only because their premises are
  contradictory, `[Fact (1 = 2)]` and its subtler cousins).
- anchor mutants: for each custom constant, the anchor lemma must compile
  and must fail if the constant's definition is replaced by `True`/`False`.

The proslambenomenos verify gate already runs every mutant in a script's
known set and requires each to fail; that gate ports with the mutant
generator swapped.

## 4. Corpus (L3) — gnosis identity, ket storage, sieve verdicts

- Store: one ket store (`.ket`) shared by every agent and subproject.
  Nodes: statement (`context`, identity = lock), proof (`code`),
  verification (`score`: CIDs of build log, axiom output, lean4checker
  output, mutant table), review (`reasoning`, from sieve), pin (`context`:
  toolchain, mathlib rev, Clay PDF sha).
- Edges: `proves`, `depends_on` (Mathlib constants used, by name and pin),
  `reduces_to` (a checked implication or Iff between locks),
  `refutes`, `supersedes`, `anchors`, `grounds` (verification -> outputs).
- Names live in labels only (gnosis `Gnosis.labels`). The encyclopedia
  entry for a statement is its grounded closure: everything it depends on,
  everything checked about it, and nothing said about it.
- sieve runs after every landing with Lean-specific dimensions: statement
  fidelity against the informal projection, definitional trapdoors,
  hypothesis load, pin drift, prose-vs-lock drift (Jin's finding 1: docs
  pinned a superseded manuscript). Verdicts are typed edges, corrections
  supersede, nothing is overwritten.
- catbus packs a handoff at every landing; the next agent starts from the
  ledger root CID.

## 5. Process gates (L4) — ported verbatim where possible

From proslambenomenos: message gate (no "proves", "solves", "settles",
"resolves" in a commit without `[claim <id>]`); append-only ledgers
(CLAIMS log, LAWCHANGES, LESSONS); LAW ledger hashing every gate script AND
the toolchain/mathlib pins; serial landing via `land.sh`; one checkout per
actor; IDs allocated at assignment; report, don't conclude. Lessons L-9
(runner error), L-16 (tuned check), L-18 (numbers from repo scripts),
L-20 (an exact clause is an identity) carry over unchanged; L-20 becomes
the rule that a claim whose type reduces to `True` is not a claim.

## 6. Agents (L5)

Provers: any model with Lean in the loop (sieve's agent protocol is
model-agnostic: prompt in, JSON out). Reviewers: sieve dimensions.
Integrator: one, serial. The "no intuition" rule is enforced at intake:
a note may argue anything; a claim file without a `lean:` field is
rejected by the intake gate.

## 7. Calibration protocol — the first deliverable

All runs at the Crouzeix pin. Every output stored by CID; the run is a
ledger entry with the outcome per control.

Positive controls (MUST reach `proven`; if one does not, the gates are
wrong, not the theorem):

- P1  `crouzeixConjecture` in jinshanmu/CrouzeixConjecture at `f9d5c8d`:
      rebuild; failing axiom gate; lean4checker; lock; hypothesis mutant
      (drop `[Nonempty n]` must fail); fidelity (norm identity by `rfl`,
      already verified 2026-08-15 and recorded in crouzeix-audit/LEDGER.md).
- P2  a theorem proven here from scratch through the whole pipeline:
      sharpness of the constant 2 at the 2x2 nilpotent
      (A = [[0,1],[0,0]], ‖A‖ = 1, W(A) the closed disk of radius 1/2, so
      p(z) = z gives ‖p(A)‖ = 2·sup). Exercises every gate on a small,
      independently checkable object.
- P3  a Mathlib theorem restated under another name: tests that the lock
      dedups against Mathlib's own node and that status is `proven` by
      dependency, not by re-proof.

Negative controls (MUST be classified as shown, with the reason attached):

- N1  the AIX template (`step` hypothesis, custom `Tower.declInv`) ->
      `stated`: the anchor rule catches it before status ever reaches
      the hypotheses, because the statement is about an unanchored private
      predicate. (`conditional` remains the status for sorry-free proofs
      whose premises are named claim ids; the run showed it is not what
      catches this template.)
- N2  `def Claim : Prop := True; theorem t : Claim := trivial` -> `stated`,
      reason: type reduces to `True`; no Mathlib anchor.
- N3  a proof resting on an uninterpreted `axiom` -> axiom gate FAIL.
- N4  Crouzeix with constant 1 -> `refuted`, by P2's witness.
- N5  a claim file whose recorded lock differs from the recomputed lock
      (the statement changed, the prose did not) -> drift gate FAIL.

Pass criterion: 3/3 positives `proven`, 5/5 negatives as listed. Only then
does the Millennium registry get imported.

RUN 2026-09-06 (scripts/calibrate.py, calib/RESULTS.json, claims/*.yml,
every gate output stored in ket by CID): PASS 8/8, 5m17s.
- P1 proven: Jin's build 2m34s from cache; axiom set exactly the triple;
  lean4checker on FinalTheorems 17 s; lock
  edcf6289...; three custom constants in the type, six rfl anchors; the
  `[Nonempty n]` mutant killed (instance synthesis fails, goals unsolved).
- P2 proven from scratch (calib/Quod/P2.lean): `2 * sup <= ||J||` at the
  2x2 nilpotent with p = X, via `||J|| >= 1` (e1 -> e0) and
  `|conj(x0) x1| <= 1/2`; N4's negation follows.
- P3: the restated theorem's lock equals `Nat.exists_infinite_primes`'s
  lock bit for bit; one node.
- N1 stated (unanchored `Tower.declInv`); N2 stated (type unfolds to
  `True`; unanchored); N3 axiom-fail (`oracle`); N4 refuted by
  `QuodP2.N4_refuted`; N5 drift-fail.
- Self-test that the gates can fail: with the anchor table emptied, P1
  computes `stated`, not `proven`.
- Observation kept: lean4checker exits 0 on N3 and N4. It certifies
  kernel consistency of the environment, not axiom freedom; the axiom
  gate is a separate check by necessity, not by taste.

## 8. Millennium program (after calibration)

- Import lean-dojo's seven `clay_prize_*` locks at `fabf563a` as the
  registry; they are `stated` (bodies `sorry`) by construction.
- Work items are reductions and lemmas: `Y -> clay_prize_X`,
  `clay_prize_X <-> Y`, and `proven` pieces of Y. Each is a claim with a
  lock; each lands through the same gates. The corpus grows as checked
  structure around each problem, deduped by lock, so two agents proving
  the same lemma under different names add one node.
- What the ledger will say at any time, for each problem: the registry
  lock, the checked reductions to it, the proven lemmas beneath them, and
  the named hypotheses that remain. That table is the deliverable. It is
  the thing the AIX release and the P = NP repo could not produce.

## 9. Costs and first moves

- Toolchain: elan has v4.28.0 installed, no default set (one command).
- P1 rebuild from cache: about 12 minutes measured in August; lean4checker
  builds against the same toolchain.
- Gate port: the proslambenomenos scripts with a Lean mutant generator,
  one to two days of work.
- sieve dims for Lean: a JSON file.
- Millennium registry build at `fabf563a`: a cache download and a build.

## 10. Decisions for the owner

1. Repo name (this directory is `quod`).
2. Is `lean4checker` required for `proven`? Recommendation: yes.
3. Pin policy: one pin per subproject recorded in LAW. Recommendation: yes;
   never cross-pin a claim.
4. Provers other than Claude through sieve's protocol? Recommendation: yes,
   from the start, so the ledger is about the system and not this session.

Sources consulted: jinshanmu/CrouzeixConjecture (tip f9d5c8d, Lean/ pins);
lean-dojo/LeanMillenniumPrizeProblems (README, pins); crouzeix-audit/
LEDGER.md; gnosis and sieve READMEs; the AIX Millennium-claims account at
postquantum.com (the `Tower` template and the `True` top-level case).
