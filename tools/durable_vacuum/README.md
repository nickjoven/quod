# Durable vacuum calibration harness

This is a separate development instrument for replayable numerical evidence.
It does not modify, resume, or replace the selected 42-cell run. The original
pilot remains permanently unverifiable. No target execution or uniform
Yang–Mills gap claim is authorized by this harness.

## Durable boundaries

Each task is one grid and one tolerance. The harness uses the existing temporal
kernel and its independent stored-arithmetic verifier. It appends:

1. An attempt start, durably published before computation.
2. Complete raw propagation output, immediately after integration and **before**
   error/window assessment. This includes correlations and solver counters.
3. The full temporal output, including ground preparation, assessment, failures,
   and the replay verdict.

Files are immutable, linked into place without replacement, and protected by a
single-writer lock. Both files and containing directories are synchronized to
disk. Events have sequence numbers, a previous-event hash, and a specification
hash. A crash can leave temporary/orphan evidence; the harness preserves it and
refuses to proceed until it is inspected. It never silently deletes that evidence.
Durability depends on the filesystem and storage honoring fsync semantics.

## Replay and resume

Replay checks the complete event inventory, hashes, attempt state transitions,
raw/result equality, and existing certificate/error/window arithmetic. It does
not call the propagation solver. A verified failed outcome remains a failure;
it is not a successful numerical result. Hashes detect drift relative to retained
commitments; they do not authenticate execution against deliberate rewriting.

Completed and failed terminal tasks are skipped on subsequent execution. An
unfinished attempt requires `--retry-interrupted`, which records the interruption
and starts a new attempt without overwriting the old one. When raw propagation
survived, the adapter recomputes preparation and compares the exact matrix,
vacuum energy, centered vectors, clock, and tolerances before reusing the raw
output. Any mismatch stops the harness rather than silently recomputing it.

This saves work at **completed propagation boundaries**. It does not serialize
private BDF state or resume halfway through an integration. A crash inside an
unfinished propagation still loses that propagation's work. Checkpoints inside
BDF require a separately specified and validated numerical instrument.

Singleton calls prepare their ground independently, whereas the registered
multi-tolerance kernel shares a ground per grid. Consequently these task results
are not a bitwise continuation of that kernel. Per-task qualifying windows are
not combined into a full-ladder or full-run qualification claim.

## Fixed development schedule

The CLI accepts only built-in calibration specifications: SU(2) and corrected
U(1), g=1, eta=0, certificate cutoff 8, times 0, 1/8, 1/4, grids 32 and 64,
and tolerance pairs (1e-8,1e-12), (1e-10,1e-14). These eight small tasks are
outside the selected target manifest. Calibration does not predict target runtime.
The specification binds exact certificates, requests, local source closure,
Python/dependency versions, and thread settings. External native binaries and
hardware are not authenticated by package version pins.

## Commands

Run from the repository root. Set `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`,
and `MKL_NUM_THREADS=1` consistently for all commands. A low scheduling priority
keeps development work subordinate to the ongoing solver.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
nice -n 15 python3 -m unittest discover -s tools/durable_vacuum -p 'test_*.py'
python3 tools/durable_vacuum/harness.py prepare --spec /tmp/durable-spec.json
python3 tools/durable_vacuum/harness.py init --spec /tmp/durable-spec.json --ledger /tmp/durable-ledger
nice -n 15 python3 tools/durable_vacuum/harness.py run --spec /tmp/durable-spec.json --ledger /tmp/durable-ledger
python3 tools/durable_vacuum/harness.py replay --spec /tmp/durable-spec.json --ledger /tmp/durable-ledger
```

After inspecting an interrupted attempt, use the same `run` command with
`--retry-interrupted`. There is no automatic retry of terminal failures. Existing
specifications and ledger directories are never overwritten by prepare/init.
For future target use, create and validate a separate registration before
execution. This harness deliberately rejects edited target specifications.
