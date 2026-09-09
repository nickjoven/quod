# U(1) exact certificate execution

Date: 2026-09-09 UTC. Instrument commit: `7ce122a`.
State: **unregistered; parity-specific model bounds available; windows unresolved**.

## Results

All 50 fixed Fourier rungs completed in 48.4 seconds without instrument
failures. Exact endpoint checks passed in both parity sectors. Forty-seven
rungs supplied isolated even-vector/correlation bounds; 46 met the original
scalar radius budgets. Coarse unresolved and imprecise results are preserved.

At K=320, every development cell:

- Meets the original 1e-6 scalar radius budgets for the full gap, first three
  even gaps and five vacuum components.
- Proves the even ground lies below the odd sector and that the lowest odd
  excitation sets the full gap.
- Establishes a nonzero first-even overlap for both P and P^2. Odd overlaps
  vanish by reflection symmetry, so the even threshold differs from the full gap.

The largest finest-rung aligned eigenvector-distance upper bound is 1.49e-14.
These are certificates for the explicit development operator under the
analytic/arithmetic trusted base in [U1-CERTIFICATES.md](U1-CERTIFICATES.md).
The source-pilot convention remains unverified; this is not a registered
field-theory result or a target result.

## Verification and provenance

All 77 numerical tests passed, including exact squared-hopping Sturm checks,
free parity degeneracy, bilateral Haar moments, rejection of parity leakage,
both-tail residual accounting, false-certificate mutants, failure continuation,
and replay of every archived rung's endpoints, overlaps and correlations.
Source hashes were unchanged and exact request accounting passed.
`git diff --check` passed.

Report: `u1-certificates.json`. SHA-256:
`337f9e89800bbd3524b38cff13572afeb769c704da813d762b1531cc51c10f84`.
The report retains rational endpoints and bounds, hexadecimal candidates,
source/input hashes, timings and all failure/unresolved states. The archive
test verifies this document's checksum and recomputes the scalar flags as
well as the exact certificate calculations.

## Next step

Result commit: `d90c594`. Packet:
`27509748ada151ac86b39c4819b7d9af53b87447a36c10f1a6b22dae7f0490e3`.
Artifact validation passed and ket projection was clean. The packet includes
the run document before this provenance paragraph, avoiding self-reference.

Run direct periodic-angle propagation and assess sampled effective gaps
against these intervals, using the first even gap as the observable reference.
The full odd gap must remain separately reported. All 42 target rows remain
unrun. Registration, source-pilot conventions and independent review are
still outstanding.
