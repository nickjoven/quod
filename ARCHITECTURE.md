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
Mathlib notion. A claim whose type depends on an unanchored custom constant
can be at most `stated`, never `proven`, whatever its proof does.

An anchor row in the table is a nomination, not a fact. The shape gate
(`scripts/anchor_check.py`) admits a nominated lemma only if, under its
binders, it reads `c x₁ … xₖ = rhs` or `c x₁ … xₖ ↔ rhs` with the xᵢ
distinct bound variables and `rhs` free of `c`; every custom constant in
`rhs` must be anchored in turn, cycles count as unanchored, so the chain
ends in the pinned libraries or the claim stays `stated`. This was added
after the recheck of 2026-09-06 found that without it a single forged row
(any rfl lemma under any name) turned the AIX template into `proven`
(N6, N7 below).

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
- anchor gate: for each custom constant, the nominated anchor must pass
  the shape gate, its axiom set must be the triple, and its right-hand
  side's custom constants must be anchored recursively.

The proslambenomenos verify gate already runs every mutant in a script's
known set and requires each to fail; that gate ports with the mutant
generator swapped.

## 4. Status is computed (superseded in detail by SEMANTICS.md, 2026-09-06)

Owner's rule: proof requires a demonstrandum. A demonstrandum D is a
locked type registered before it is judged. A proof is offered against a
named D and discharges it iff the locks are byte-equal, the axiom set is
the standard triple, and lean4checker accepts the module. Status of D:
`stated` | `proven` | `refuted` | `drift-fail` (`inconsistent` halts the
pin). Verdicts on offered proofs (`accepted`, `incomplete: sorry`,
`rejected: lock mismatch | shape | extra axioms | lean4checker`) are
recorded on the proof and leave D `stated`. There is no `conditional`:
hypotheses are part of the lock and are listed as a descriptor.

Descriptors (computed, never gate status): hypotheses, custom constants,
grounded, anchored (per constant, gate reason kept), reduces_to_True,
registry_match, dedup, mutants. They say what D is worth. "Counts against
a Millennium problem" is exactly the registry lock relation. Under these
semantics the AIX template is `proven` as the implication it is, with
`step` listed and no registry match; offered against the registry
demonstrandum it is rejected at the lock. Full text: SEMANTICS.md.

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
- N6  N1 with a forged anchor row: `Tower.declInv` nominated to an
      unrelated rfl lemma (`QuodP2.anchor_J`) -> `stated`, reason: anchor
      lhs head is not the constant.
- N7  N1 with an anchor of admissible shape whose right-hand side is
      another private constant (`Tower7.declInv ↔ Tower7.declInv'`) ->
      `stated`, reason: unanchored via the chain.
- N8  N4 with a forged refutation row: an unrelated clean theorem
      (`QuodP2.sharp_two`) nominated as the negation -> `stated`, reason:
      refutation rejected (shape). `refuted_by` is a nomination;
      `scripts/refute_check.py` requires the nominated type to be `¬ T`
      with T's canonical form equal to the claim's (Q-8). N4 itself is
      now stated over `Type` so the strict match holds (Q-9).

Pass criterion (SEMANTICS.md table, 2026-09-06): 3/3 positives `proven`;
negatives at their required status AND descriptors. N1, N2, N6, N7 are
`proven` under the demonstrandum semantics with their descriptors
(hypotheses, reduces_to_True, anchor rejections) required; N9 (clean
theorem offered against another demonstrandum) is rejected at the lock. Only then
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

RECHECK 2026-09-06 (same day, fresh shell). Clean re-run of the 8-control
set: PASS 8/8, every status and every evidence CID identical to the first
run except the P1 mutant output, whose CID differed because the random
temp file name leaked into the compile error (fixed: scrubbed to
`<mutant>`). Then a probe the self-test had not covered: one forged row
in the anchor table (`Tower.declInv` -> `QuodP2.anchor_J`) turned N1
into `proven`. The anchor table was a hand-typed map that nothing
checked. Fix: `scripts/anchor_check.py` (shape gate) plus recursion
through anchor right-hand sides in `calibrate.py`; controls N6 (forged
row) and N7 (laundering chain) added. Run with the gate: PASS 10/10,
9m36s. P1's chain now reads maxPolynomialModulusOnNumericalRange ->
numericalRange -> Mathlib and is checked, not assumed.

SECOND RECHECK 2026-09-06 (after the owner's decisions and the rule that
every problem is brought into view; OPEN.yml opened with Q-1..Q-21). The
same class of hole existed for `refuted_by`: any axiom-clean theorem
under any name could mark any claim `refuted`. Fix: `refute_check.py`
(nominated type must be `¬ T` with T canonically equal to the claim) and
control N8 (forged refutation). N4 restated over `Type` so the strict
match holds (Q-9). Run: PASS 11/11, 12m37s (partly alongside the
registry builds).

## 7b. Grounded, anchored, matched (added 2026-09-06)

Three computed fields on every claim, none typed by hand:

- `grounded`: the definitional closure of every custom constant in the
  type ends in the pinned libraries, with no axiom, opaque constant or
  sorry inside any definition (`scripts/closure.py`). Says the notion is
  defined in library terms with nothing hidden. Says nothing about which
  named problem it is.
- anchored: a checked Iff/Eq chain to a Mathlib-named declaration
  (`scripts/anchor_check.py`, recursive). Strong fidelity. At the
  Millennium pin only Riemann has one.
- `registry_match`: the claim's lock equals a registry lock (or, later, is
  joined to one by a checked Iff). This, not a status, is what "counts
  against a Millennium problem" means.
- `hypotheses`: explicit Prop binders of the type, listed from the
  elaborated statement (Q-1). The AIX control's `step` appears here.

Which of grounded/anchored `proven` requires is owner decision Q-22.

THIRD RECHECK 2026-09-06, demonstrandum semantics (SEMANTICS.md): the
runner rewritten so status = "the demonstrandum's lock is discharged"
and everything else is a descriptor or a verdict on the offered proof.
Smoke test on two controls first (Q-23), then PASS 12/12 in 14m53s: N1,
N2, N6, N7 now `proven` with their descriptors required (hypotheses
[step], reduces_to_True, anchor rejections with reason); N9 added (clean
theorem offered against another demonstrandum: rejected, lock mismatch).

## 8. Millennium program (after calibration)

REGISTRY IMPORT 2026-09-06 (millennium/PIN.yml, gitignored clone at
millennium/registry): lean-dojo tip fd52071 "Fix Hodge and Yang-Mills
statement faithfulness"; Lean v4.31.0; mathlib fabf563a7c (verified from
the manifest, Q-18); PhysLean 3dddd61e for Yang-Mills. Facts found on
import, in view: `clay_prize_p_versus_np` is a `def` of type
`ClayPVersusNPResolution`, not a theorem (both outcomes represented);
Yang-Mills alone pulls PhysLean, which has no build cache; no lean4checker
release exists for v4.31.0, so the checker at this pin is upstream master
91a7f0e built with the toolchain overridden (Q-20). Import runs the same
gates (`scripts/registry_import.py` -> `calibrate.evaluate`) and writes
claims/millennium/*.yml with computed status.
Result: seven `stated`, lean4checker exit 0 on all, sorryAx the only
extra axiom. Each type is a single custom Clay wrapper (Q-21). The
Riemann wrapper is anchored through the registry's own theorems
`ClayRiemannHypothesis.iff_real_part` and
`...Formulations.RealPart.iff_mathlib` to Mathlib's `RiemannHypothesis`,
both links passing anchor_check and the axiom gate (nominated in
millennium/PIN.yml, verified at import, 4m23s). The other six are
unanchored; anchoring them is the next work item.


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

## 10. Decisions for the owner (DECIDED 2026-09-06)

1. Repo name: `quod` stays.
2. `lean4checker` is required for `proven`. Yes.
3. Pin policy: one pin per subproject recorded in LAW; never cross-pin a
   claim. Yes.
4. Provers other than Claude through sieve's protocol from the start. Yes.

Standing rule added the same day: every known problem is brought into
view in OPEN.yml, with an id, a severity and a status. A gap that is
known and unlisted is a defect of the ledger, not of the gap.

Sources consulted: jinshanmu/CrouzeixConjecture (tip f9d5c8d, Lean/ pins);
lean-dojo/LeanMillenniumPrizeProblems (README, pins); crouzeix-audit/
LEDGER.md; gnosis and sieve READMEs; the AIX Millennium-claims account at
postquantum.com (the `Tower` template and the `True` top-level case).
