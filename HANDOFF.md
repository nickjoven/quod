# Handoff: taking over quod on another machine

State as of 2026-09-06 (see `git log` for the commit you are on).

## What this is

A ledger of theorems whose status is computed, never declared. Read in
this order:

1. `SEMANTICS.md` — the rule everything follows: proof requires a
   demonstrandum; `proven` means the demonstrandum's lock is discharged;
   everything else is a descriptor or a verdict on the offered proof.
2. `ARCHITECTURE.md` — layers, locks, gates, the calibration set and the
   three run records of 2026-09-06 (8/8 → 10/10 → 11/11 → 12/12 as the
   gates were tightened).
3. `OPEN.yml` — every known problem, Q-1 to Q-23, with severity and
   status. A known gap that is not in this file is a defect of the ledger.
4. `millennium/PIN.yml` — the registry pin, the seven demonstranda, the
   anchor nominations (Riemann only so far).

## Bootstrap

    git clone <this repo> ~/code/quod && cd ~/code/quod
    pip install pyyaml blake3            # blake3 optional (falls back to blake2b, and says so)
    scripts/bootstrap.sh                 # clones + builds both pins, ~30–60 min, ~20 GB

Everything heavy is gitignored and reproduced by the script from the
pins recorded in it. The ket store (`KET_HOME`, default
`~/code/handoffs/.ket`) holds evidence blobs by CID; without it, run the
tools with `--no-ket` and the claim files carry `null` evidence CIDs.

## Running

    python3 scripts/calibrate.py --only N2,N9 --no-ket   # smoke, ~2 min (Q-23: always first)
    python3 scripts/calibrate.py                          # full set, ~15 min, PASS 12/12 expected
    python3 scripts/registry_import.py                    # seven registry demonstranda, ~4 min

Per-declaration tools, all `<project_dir> <Module> <Decl>`-shaped:
`lock.py` (canonical type, lock, binders, custom constants),
`axiom_gate.py`, `anchor_check.py`, `refute_check.py`, `closure.py`,
`hyp_mutant.py`. Each prints a reason and exits non-zero on a rejection.

## Rules that are not in the code

- Every table the runner consults is a nomination; a gate verifies it.
  This was the class of hole found twice on 2026-09-06 (anchors, then
  refutations). Do not add a table without its gate and a control.
- A positive control failing means the gates are wrong, not the theorem.
- Do not edit the runner while a run is in flight (Q-23).
- Never cross-pin. The Crouzeix and Millennium subprojects have separate
  toolchains, Mathlib revisions, and lean4checker builds.
- Statuses live in generated files; nothing pins them yet (Q-10 is the
  highest-value open item). Until it is closed, trust a status only after
  a rerun.

## Next work, in order

1. Q-10: guard the claim files (recompute-and-diff mode, LAW pin of
   `scripts/*.py`, append-only ledgers ported from proslambenomenos).
2. Q-13: one Lean process per module for all checks; the run is 15 min
   for 12 controls and will not scale.
3. Anchor descriptors for the six un-anchored Clay wrappers, **Poincare
   first** (owner decision, 2026-09-16). The registry's Iff theorems end in
   registry definitions, not Mathlib names; that is the recorded state, and
   it was re-read for Poincare at the pin (`fd52071`,
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
4. Q-5: generate the gloss from the lock; sieve dimension for fidelity.

## Owner decisions on record

quod stays the name; lean4checker required for `proven`; one pin per
subproject; other provers via sieve from the start; proof requires a
demonstrandum (2026-09-06). Anchor work pivots to Poincare: it is the next
of the six un-anchored Clay wrappers, ahead of the other five (2026-09-16).
