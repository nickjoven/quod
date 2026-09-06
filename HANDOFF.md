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
3. Anchor descriptors for the six un-anchored Clay wrappers where the
   registry offers Iff theorems among its own formulations (they end in
   registry definitions, not Mathlib names; that is the recorded state).
4. Q-5: generate the gloss from the lock; sieve dimension for fidelity.

## Owner decisions on record

quod stays the name; lean4checker required for `proven`; one pin per
subproject; other provers via sieve from the start; proof requires a
demonstrandum (2026-09-06).
