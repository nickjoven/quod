# Recovered-design U(1) development execution

Instrument commit: `a976041`. State: **unregistered development**.

## Results

All 90 representation requests completed in 6.72 seconds without failures,
using the recovered coefficient 4g^2 and Fourier ladder 40..640. Both parity
sectors were retained. All ten development cells meet the existing 1e-6
scalar agreement criterion across independent representations and adjacent
finest rungs. This is convergence evidence, not yet a rigorous error bound.

At g=0.10, the finest Fourier full gap is 3.9899748344357704 and the first
even gap is 7.969892777016213. The full gap agrees within 1.4e-12 with the
prior pilot number quoted in the recovered LITCHECK. That agreement is
limited to one quoted scalar: the missing pilot code and JSON are still
needed for complete replication and provenance verification.

The historical coefficient-1 U(1) reports remain unchanged. They do not
supply certificates for these new results. First-even overlaps, exact
spectral bounds and direct-propagation windows must be regenerated.

## Verification and provenance

All 94 numerical tests passed; `git diff --check` passed.
The six new instrument tests cover: free dispersion and Haar checks,
independent dense interacting matrix, rejection of the old kinetic
coefficient, unchanged potential, recovered ladder and independent angle
comparison, invalid inputs, calibration failure and nonfinite-result
continuation. The archive regression recomputes every stored adjacent and
cross-method difference and checks the source and design hashes.

Report: `u1-design-development.json`. SHA-256:
`92c81bdbfa4422ca7ad85b96326416cd00c1da41009b2350294623f727b3591b`.
Source hashes were unchanged during the run and request accounting passed.
Reproduction commands and the exact parameter mapping are in
[U1-DESIGN.md](U1-DESIGN.md). All 42 target rows remain unrun.
