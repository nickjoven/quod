# Disposition of the lost original pilot

## Authoritative update

On 2026-09-09 the user confirmed: “original script and results are lost.”
Original-pilot replication is therefore **unverifiable: source lost**, rather
than a pending recovery task. Stop requesting the pilot archive. The expected
hashes in the recovered handoff remain historical provenance; neither matching
a quoted number nor reconstructing a plausible script verifies those hashes.

This supersedes recovery requests in older status reports. The original bundle,
hash-locked numerical archives, and `design-readiness.json` remain unchanged.
The latter's `original_pilot_replication: unresolved` is a historical audit
state, refined by this disposition; it must never be interpreted as successful
replication. The user reported loss, not scientific approval or registration.

## Baseline for continued development

Use the independently implemented and archived SU(2) and corrected U(1)
development calculations as the reproducible baseline. Their authority is the
recovered explicit operator specification and their own source, certificate,
cross-representation and propagation checks. They are exploratory development
results, not recovered pilot results or a retroactively registered experiment.

`pilot-disposition.json` pins the recovered handoff, design, consolidated audit
and result contract. The contract in turn pins the six numerical archives and
their per-cell payloads. Twenty development cells retain their existing
qualification; this disposition adds no numerical evidence. All 42 target
cells remain unrun.

## Effect on the next steps

Recovery is no longer a useful prerequisite for continued development. Any
future registration must explicitly disclose the lost source and identify the
new baseline without asserting historical replication. The recovered design's
development/replication row is retained as source evidence; the future
registration must describe those cells as development and reproduction of the
stated model, with original-pilot comparison unavailable.

Owner-assigned P/LC identifiers, independent review, and a committed registration
of future work remain outstanding. Review must assess the archived instrument
and this provenance deviation. Neither the loss nor this disposition waives
those steps or authorizes target execution. Target selection is not yet the
next required user decision.

## Verification

From the repository root:

```sh
python3 -m unittest discover -s scripts -p 'test_vacuum_pilot_disposition.py' -v
```

The check verifies pinned provenance, the permanent unverified status, the
twenty-cell baseline and all 42 unrun target records. The existing design
readiness tests separately replay numerical bounds, overlaps and time windows;
the disposition check does not replace them.
