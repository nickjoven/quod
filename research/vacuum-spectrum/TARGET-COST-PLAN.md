# Target-domain cost scenarios without target execution

## Measured basis and assumptions

`target-cost-plan.json` scales archived development work timings to the
42-row manifest: 21 cells per theory, nine representation requests, five
certificate rungs and eight direct evolutions per cell. That would mean
378 representation requests, 210 certificate rungs and 336 evolutions.
These are planning counts only; no target was selected or executed.

For each theory and stage, the code sums measured work duration per
development cell, then multiplies the mean and maximum by 21. The SU(2)
representation stage uses only character and fourth-order angle requests;
the historical second-order comparison is excluded. The temporal stage
includes the recorded fresh/cached ground preparation plus both evolutions.
Reusing a finest ground is already reflected in those measurements.

| Scenario | SU(2) seconds | U(1) seconds | Combined minutes |
| --- | ---: | ---: | ---: |
| Mean development cost per cell | 783.64 | 467.08 | 20.85 |
| Slowest observed development cell per stage | 1337.14 | 960.20 | 38.29 |
| Explicit 4x slowest-case stress assumption | 5348.57 | 3840.78 | 153.16 |

The factor four is a planning assumption, not a confidence interval or
runtime bound. Checkpoint I/O, review, registration and failure repair are
outside the measured-work estimate. Hardware and numerical behavior can
change runtimes. Only eta=1 development timings have been measured; the
eta=0 and eta=.5 timing behavior is unverified. The scenarios estimate
fixed-ladder cost; they do not promise the requested precision is achieved.

## Temporal and precision limits

Each cell must derive its own interval/overlap budget and retain unresolved
outcomes if the fixed refinement cap or sampled window cannot support an
estimate. Exact free-sector selection rules differ from interacting cells:
P^2 can miss the first excitation. The current development qualification
of both probes cannot be transferred to every target deformation. A
registered implementation must represent such exact zeros, accessible
thresholds and failures explicitly; it must not discard a small positive
overlap or infer a full gap from a probe that misses the lightest state.

All model bounds use exact endpoint/residual/tail arguments, not runtime
scenarios. The existing 1e-6 budget remains the proposed numerical goal.
If the target derive layer cannot demonstrate its applicability, amend the
design before execution or report unresolved within the registered rules.
No tolerance widening or target-window selection is authorized by this plan.

## Reproduction and checks

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_target_cost.py --output research/vacuum-spectrum/target-cost-plan.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_target_cost.py' -v
```

The report pins input/source hashes and retains exact rational versions of
measured binary64 durations and computed scenarios. Tests replay the archive,
check counts, and reject missing/nonfinite timing data and target-derived
inputs. This is cost planning, not execution or registration readiness.
