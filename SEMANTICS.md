# quod semantics

Fixed 2026-09-06 on the owner's rule: proof requires a demonstrandum.
Everything below is computed. Nothing here is a matter of wording.

## Objects

**Pin.** A Lean toolchain, a Mathlib revision, and the other library
revisions of one Lake project. Every object below lives at exactly one
pin. Nothing is compared across pins (decision 3).

**Demonstrandum** D. A Lean type T at a pin, identified by
`lock(T)`: BLAKE3 of the canonical elaborated type (`pp.all`, universe
parameters renamed, binder names erased). D is registered before it is
judged. Its record carries the lock, the pin, and a gloss. The gloss is
free text and has no authority; the identity of D is its lock.

**Proof** P. A declaration at the same pin, offered against a named D.
A declaration offered against nothing is not a claim; it may register a
new D (its own type) and is then a proof of that D and of nothing else.

**Refutation.** A proof offered against D whose type is `¬ T'` with
`lock(T') = lock(T)`.

## Discharge

P discharges D iff all of:

1. `lock(type(P)) = lock(T)` (same pin, byte-equal canonical types), or
   `type(P) ↔ T` is itself a discharged demonstrandum (an edge, later);
2. the axioms of P are a subset of `{propext, Classical.choice, Quot.sound}`;
   `sorryAx` means P is incomplete, anything else means P is rejected;
3. `lean4checker` accepts the module declaring P (decision 2).

A refutation discharges `¬D` by the same three tests, with the shape
gate `refute_check.py` supplying test 1.

## Status of a demonstrandum (computed)

| status | when |
|---|---|
| `stated` | registered, no discharging proof or refutation on record |
| `proven` | a proof discharges D |
| `refuted` | a refutation discharges ¬D |
| `drift-fail` | the recorded lock differs from the recomputed lock; nothing on record applies to D any more |

`proven` and `refuted` together at one pin is an inconsistency of the
pin and halts the ledger. There is no `conditional`: a hypothesis is part
of T, so a D with hypotheses is proven as the implication it is.
`axiom-fail` and `checker-fail` are verdicts on a proof, recorded on the
proof; they leave D `stated`.

## Descriptors of a demonstrandum (computed, never affect status)

- `hypotheses`: explicit Prop binders of T, from the elaborated type.
- `custom_constants`: constants in T outside the pinned libraries.
- `grounded`: the definitional closure of every custom constant ends in
  the pinned libraries with no axiom, opaque constant or sorry inside a
  definition (`closure.py`).
- `anchored`: per custom constant, a checked Iff/Eq chain to a
  Mathlib-named declaration (`anchor_check.py`, recursive). A nominated
  anchor that fails the shape gate is recorded as rejected with reason.
- `reduces_to_True`: T unfolds to `True` under all transparency.
- `registry_match`: `lock(T)` equals the lock of one of the seven
  registry demonstranda at the same pin.
- `dedup`: `lock(T)` equals the lock of a library declaration; D is then
  proven by dependency.

These say what D is worth and what it is about. They are for the human,
for sieve, and for the label. They are not for `proven`.

## What counts against a Millennium problem

Exactly one relation: the demonstrandum is one of the seven registry
locks at the registry pin, or is joined to one by a discharged Iff
demonstrandum. A proof of any other D, however named, counts against
nothing. This is where the induction-template control lands: its D is proven as the
implication it is, its `hypotheses` lists `step`, its `registry_match` is
none, and the registry demonstrandum stays `stated`. Offering their proof
against the registry demonstrandum is rejected at test 1, lock mismatch.

## Process

- A proof cannot enter the ledger without naming its demonstrandum.
- A demonstrandum's lock is written once; a change is a new D and the old
  record shows `drift-fail` until re-registered (`superseded` edge).
- Every table the runner consults (anchors, refutations, dedup targets,
  proof-to-demonstrandum pairings) is a nomination verified by a gate.
- The gloss may be generated from the lock. It may never be the identity.

## Calibration under these semantics

Positive controls must be `proven`; negative controls must land where the
table says, on status and on descriptors:

| id | D | offered | required |
|---|---|---|---|
| P1 | Jin's `crouzeixConjecture` | itself | proven; grounded; 3/3 anchored; hyps 0 |
| P2 | `QuodP2.sharp_two` | itself | proven |
| P3 | restated infinitude of primes | itself | proven; dedup = Mathlib lock |
| N1 | induction template | itself | proven; hyps = [step]; registry_match none; anchored none |
| N2 | `True` behind a name | itself | proven; reduces_to_True |
| N3 | theorem on an `axiom` | itself | stated; proof rejected: extra axiom |
| N4 | Crouzeix with constant 1 | refutation `N4_refuted` | refuted |
| N5 | P1 with a stale recorded lock | itself | drift-fail |
| N6 | N1 with a forged anchor row | itself | proven; anchor rejected: shape |
| N7 | N1 with a laundering anchor | itself | proven; anchor rejected: chain |
| N8 | N4 with a forged refutation | `sharp_two` as refutation | stated; refutation rejected: shape |
| N9 | P1's demonstrandum | `sharp_two` as proof | stated; proof rejected: lock mismatch |

N1, N2, N6, N7 change from `stated` to `proven` under these semantics.
That is the point: they are proofs of what they state. What they are
not is proofs of anything registered, and the record says so.

RUN 2026-09-06: `scripts/calibrate.py` PASS 12/12 (14m53s), every control at
its required status and descriptors; registry re-imported, seven `stated`
with verdict `incomplete: sorry`, Riemann anchored.
