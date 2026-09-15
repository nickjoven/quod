# Durable harness development results

## Outcome

The separate development harness saves complete propagation output before
assessment, resumes from that boundary after an explicitly acknowledged
interruption, and replays stored arithmetic without integration or certificate
generation. The live 42-cell registration and completion monitor were checked
after development: their frozen source and dependency pins remain valid.
No selected target cell was run by this harness.

The implementation and small calibration specification were committed as
`7c5433e` before the retained demonstration. Source hashes, exact certificates,
requests, dependencies, and thread settings are in [spec.json](spec.json).
All 17 focused tests passed in 6.567 seconds; the reviewer independently ran
the same suite successfully. The original four failing audit mutants and their
repairs remain recorded in [review-history.json](review-history.json).

## Retained crash and failure experiment

The demonstration deliberately raised an in-process interruption immediately
after the first propagation was published and before assessment. It then opened
the ledger anew, acknowledged the interruption, reused the saved propagation,
and deliberately failed the next fresh propagation. Subsequent tasks continued.
This is exception injection, not a physical power-loss experiment.

| Observation | Retained outcome |
| --- | --- |
| Before recovery | One raw propagation, zero terminal tasks, one pending attempt |
| After recovery | Eight terminal tasks: seven completed, one deliberately failed |
| Reused propagation | One; no integration call for that recovered task |
| Fresh propagation calls during recovery | Seven, including the injected failure |
| Evidence inventory | 26 chained events; interruption and failure preserved |
| Recovery execution time | 1.354 seconds |
| In-process evidence replay time | 0.188 seconds |
| Fresh-process CLI replay | Passed; [cold-replay.json](cold-replay.json) |

Full metrics are in [demonstration.json](demonstration.json). The executable
experiment is [demonstrate.py](../../../tools/durable_vacuum/demonstrate.py);
its source hash is recorded with the metrics. Raw results, attempts, and full
per-task assessments remain in [recovery-ledger](recovery-ledger/).

## Reproduce the evidence check

From the repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 tools/durable_vacuum/harness.py replay \
  --spec research/vacuum-spectrum/durable-harness-development/spec.json \
  --ledger research/vacuum-spectrum/durable-harness-development/recovery-ledger
```

To reproduce the injected experiment, run `tools/durable_vacuum/demonstrate.py`
with the same `--spec` and a **new** `--ledger` directory. Existing evidence
cannot be overwritten. Full commands and storage semantics are in the
[harness documentation](../../../tools/durable_vacuum/README.md).

## Limits and next decision

These timings are for eight small calibration tasks, not predictions for the
current target run. A checksum-consistent replay validates retained arithmetic,
not execution authenticity or a standalone BDF error bound. Singleton tasks
prepare grounds independently; their windows do not establish full-ladder
qualification. The original pilot remains permanently unverifiable. No uniform
Yang–Mills gap proof follows from these finite-rotor data.

An interrupted **unfinished** propagation still loses its internal BDF work.
Persisting private BDF state, or introducing propagation segments, needs a new
numerical contract and equivalence/error tests. Before using this harness for
targets, register the new execution path, full schedule, restart rules, and
qualification procedure separately. The current run remains unchanged.
