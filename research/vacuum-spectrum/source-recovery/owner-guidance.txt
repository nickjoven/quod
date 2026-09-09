# Working in this repository with more than one actor

1. **One checkout per actor.** The primary checkout stays on `main` and
   is read-only for everyone. Every task - agent or human - works in a
   git worktree: `make wt TASK=name` (creates `../wt-name` on branch
   `name` from `main`), `make wt-done TASK=name` when merged. The Agent
   tool's `isolation: "worktree"` does the same thing.
2. **Never, in a tree you do not own:** `git checkout`, `git switch`,
   `git stash`, `git reset --hard` (LAW-2), or edits of any kind.
3. **Gate-covered files are integrator-only**: `scripts/check_*.py`,
   `scripts/run_all.py`, `scripts/*.js`, `scripts/verify/*`,
   `tests/run_spec.py`, `tests/spec/*`, `catalog/_common.py`,
   `kernels/*.py` (LAW-34). A task that needs a gate change reports
   it; the integrator writes the LAWCHANGES entry last, after
   rebase, with the hashes as they will be on `main`.
   (`tests/test_checks.py` retired at LAW-20.)
4. **IDs are allocated at assignment.** A task prompt that may produce a
   litcheck, prediction, or law entry is told its number (LC-n, P-n).
   The append-only ledgers merge by union (`.gitattributes`), so two
   appends never conflict textually; numbering is the only shared state.
5. **Namespaced outputs.** Results go to
   `scripts/experiments/<task>_results.json`; scratch to a per-task
   directory. Never write another task's file. Catalog entries that
   read results pin them by sha256.
6. **Landing is serial.** The integrator rebases each branch onto
   current `main`, runs all gates, opens the PR, merges (rebase-only),
   and packs the handoff. `main` is PR-only with CI on the PR head.
7. **Report, don't conclude.** Commit messages describe; the message
   gate rejects conclusive vocabulary without a `[claim id]` tag.
8. **Instrument nulls are part of the derive layer.** Physics nulls
   (closed forms, amplitudes, congruences) have never been the
   problem; the fired clauses of 2026-08-28 (R-26 bracket, R-29
   smear, R-30 telescoping) all came from underived INSTRUMENT
   nulls. Before a registration commits, its derive layer must
   state, for every registered detector and observable:
   (a) the detector's null response - what a tolerance-based
       detector reads on featureless background (e.g., a locking
       detector's smear width 2*TOL/slope), so "signal present"
       is always a comparison against a derived null, never a
       bare floor;
   (b) the observable's conservation identities - any exact
       algebraic constraint (telescoping sums, gauge freedoms,
       symmetries) that makes a registered outcome trivial or
       impossible, checked BEFORE positive controls are
       registered on that observable;
   (c) the search domain's validity - brackets and scan windows
       argued from bounds (per-step displacement, monotonicity),
       not from typical-case guesses;
   (d) the lessons ledger consulted: run
       `python3 scripts/tools/lessons.py <domain keywords>` and
       cite the matching L-n ids in the registration's method
       block; `scripts/tools/rentry.py` runs the same query on the
       results' own key vocabulary at the R entry, so the ledger
       is read at both ends of a line. Case knowledge lives COLD
       in LESSONS.md (triggers, rules, citations), surfaced
       mechanically - this file stays small and invariant.
   A clause that fires on any of these three is an instrument
   failure, not a finding, and it costs a re-registration; the
   checklist exists to spend that cost before the run instead.
