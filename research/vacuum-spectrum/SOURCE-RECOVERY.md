# Recovered design provenance and owning workflow

## Sources recovered

Update: the companion design and handoff are now recovered in the user-supplied
ZIP. See [DESIGN-ALIGNMENT.md](DESIGN-ALIGNMENT.md) for material differences and
the current remaining work. The account below records the earlier recovery.

The Windows Downloads file `ym_vacuum_gap_litcheck.md` is now preserved
unchanged in this directory. It identifies `nickjoven/proslambenomenos` as
the original repository. A fresh read-only clone at
`/home/njoven/codex/proslambenomenos` resolves to
`da0084147986a97f355954be6b0eff4246b9d852`, exactly the base cited by the draft.
The clone contains the actual lessons tool, lessons ledger and registration
rules. Earlier statements about their absence concerned the inspected
`quod` and local AI checkouts; they did not establish absence from this
original repository.

The recovered draft references `ym_vacuum_gap_registration_draft.md` and
`ym-gap-pilot-artifacts.zip`. Neither is present in the current owner checkout,
its available matching filename history, or Windows Downloads. The draft's
reported pilot values are prior readings, not a substitute for its code or
operator conventions. In particular, its U(1) number cannot validate our
separately declared even/full gap conventions without the pilot itself.

## Actual lessons query

Executed in the original repository:

```sh
python3 scripts/tools/lessons.py vacuum spectrum gap eigenvalue overlap correlation truncation normalization preregistration window covariance time cutoff solver tolerance integration observable null parity
```

Exit status: 0. Returned **L-1, L-2, L-3, L-6, L-11, L-16, L-18, L-21**.
The complete output, exact tool and ledger snapshots, owner guidance,
source commit and SHA-256 manifest are in `source-recovery/`.

| Lesson | Application to this study |
| --- | --- |
| L-1 | Derive detector null behavior; a bare tolerance floor is not evidence of a signal |
| L-2 | Center observables and account for reflection symmetry; even U(1) probes are blind to odd states |
| L-3 | Support numerical bands by bounds; retain convergence and unresolved outcomes |
| L-6 | Exact ordered eigenvalue counts and tail bounds replace scan-only spectral detection |
| L-11 | Fixed request and sample accounting must reject missing data |
| L-16 | Assess time windows per cell using its own rates and certified errors |
| L-18 | Preserve executable sources for every numerical tolerance or mutant claim |
| L-21 | Use the operator and parity sector actually probed when assessing decay |

This is a retrospective development consultation. These citations still need
to be included in the eventual registration's method block; running the query
now does not preregister the already completed development calculations.

## Owning process and remaining decisions

The owner's `AGENTS.md` item 4 assigns P/LC numbers at task assignment.
Item 8 requires detector nulls, observable identities, valid search domains,
and the lessons query before registration. `PREDICTIONS.md` requires a
registration commit to precede the work it covers. Development results must
therefore remain exploratory; any future registration must cover future,
unrun work. No P or LC number has been allocated here.

The owner also requires task worktrees, an integrator for gate-covered files,
and serial PR landing. The recovered clone remains on main and unmodified;
no ledger was appended and no registration was created. Source snapshots in
`quod` are evidence, not changes to the owning process.

Still required: the companion experiment draft, pilot ZIP/code and its
source hashes, assignment of P/LC identifiers through the owning process,
and independent review. Target selection is not yet the next step.
All 42 target cells remain unrun.

The earlier `readiness.json` is an immutable pre-recovery snapshot. Use this
page and `AUTONOMOUS-STATUS.md` for the updated external-input status; its
numerical bounds and test evidence remain unchanged.

## Automated verification

```sh
python3 scripts/verify_vacuum_source_recovery.py
```

The verifier checks local snapshot, draft and query-output hashes, then runs
the original captured lessons tool against the captured ledger in a temporary
Git fixture and requires byte-identical output and exit status. It does not
execute any physics solver or target. The manifest pins the full original
registration ledger by hash and Git commit; it is not copied into the
numerical result schema or silently treated as a registration.

## Reproduction of the recovered draft's original query

After recovery of the complete experiment draft, its exact original keyword
query was run in the owning repository at the same pinned commit. It returned
L-1, L-2, L-3, L-5, L-6, L-8, L-11, L-13, L-15, L-16, L-17, L-18, L-20,
and L-21, exactly matching the draft. `source-recovery/draft-lessons-query.json`
records the arguments, expected IDs, exit code and output hash; the complete
output is in `draft-lessons-query.txt`. The same verifier now reproduces both
queries using the unchanged captured tool and ledger. This completes the
query-reproduction requirement; registration must still apply its clauses.
