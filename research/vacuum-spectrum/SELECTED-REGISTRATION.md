# Selected finite-rotor registration

The user selected all 42 SU(2) and corrected U(1) cells: seven couplings
`0.125, 0.25, 0.40, 0.60, 0.85, 1.25, 2.50`, each at eta `0, 0.5, 1`.
`selected-registration.json` is the machine authority. The earlier
`execution-contract.json` and `target-result-envelope.json` remain historical,
unselected drafts and do not authorize this run.

## Freeze and execution

The registration pins the complete transitive numerical source/schema closure,
registered runner and tests, installed dependency versions, and seven archived
baseline/provenance artifacts. A full Git commit containing the identical
registration, sources and baseline is mandatory before any selected solver.
The committed registration is checked again in a fresh process before execution.

SU(2) cutoffs are `20, 40, 80, 160, 320`; corrected U(1) cutoffs are
`40, 80, 160, 320, 640`. Both use grids `600, 1200, 2400, 4800` and both
registered tolerance pairs. Every rung is requested. The exact protocol in the
JSON freezes the sample schedule, error budgets, controls and clock formula.
Every cell uses its finest certificate to determine the clock; every adjacent
sample pair is assessed and all common qualifying pairs are retained. There is
no handpicked late-time window, finest-rung fallback, budget widening, or
schedule extension after inspecting target results.

Run with `OPENBLAS_NUM_THREADS=1`:

```sh
python3 scripts/vacuum_registered_run.py check --registration-commit COMMIT
python3 scripts/vacuum_registered_run.py run --registration-commit COMMIT
python3 scripts/vacuum_registered_run.py verify --registration-commit COMMIT
```

The output directory is exclusive to this run. Its index preallocates all 42
rows and distinguishes selected, attempted and terminal outcomes. Append-only,
deterministically compressed checkpoints preserve emitted stage snapshots;
final raw cells and checkpoint references carry compressed and JSON SHA-256
hashes. Ordinary numerical failures retain partial evidence and allow later
cells to proceed. Failed controls prevent all target attempts. Checkpoint
failure stops execution; source or dependency drift stops new work and
invalidates qualification. A stopped process must not silently restart or
overwrite this directory. Verification replays stored evidence without solving.

## Interpretation

`instrument_agreement` means the fixed finite-rotor scalar and temporal checks
meet their registered criteria. `unresolved` means the fixed instrument did not
establish all criteria; it does not mean a zero gap. `failure` preserves failed
or invalid evidence. The reused cell engine's internal `development_qualified`
enum is translated to `instrument_agreement` by the selected runner and has no
additional mathematical meaning.

Full spectral gaps and observable-accessible thresholds are separate quantities,
especially for reflection-even U(1) probes and eta-zero selection rules. The
archived development baseline is the provenance source. The original pilot's
script and results are permanently lost and its claims permanently
unverifiable. These finite-rotor results do not prove a uniform Yang–Mills gap.

## Pre-execution validation and independent review

The registered path is exercised on both free development calibrations, with
solver-free replay and injected checkpoint, inventory, commit-gate and scalar
failure tests. No selected target is used for validation. Independent agent
review repaired missing-checkpoint acceptance and required a successful final
source audit; the nine registered-run tests then passed. The full pre-execution
regression transcript is retained in `selected-validation.txt`. A complete-run
verification claim is deliberately unavailable for interrupted forensic-only
records; such evidence remains preserved and cannot qualify.
