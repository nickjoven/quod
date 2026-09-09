# Exact U(1) bounds for the recovered design

## Exact operator mapping

The coefficient-4 operator is exactly H_legacy(2g,4eta). The certificate
adapter first parses declared coordinates as rational decimal values, then
multiplies those Fractions. It does not scale a binary64 coordinate and
reinterpret the rounded decimal result. Thus the diagonal is exactly
4g^2 n^2, hopping -eta/g^2, first even squared hopping 2 eta^2/g^4,
and tail floor 4g^2(K+1)^2-2|eta|/g^2.

The shared exact integer Sturm counts, tail Schur complement, dyadic
bilateral residual bounds and padded polynomial moments apply without a
change to their mathematical arguments. The trusted analytic/arithmetic
base remains [U1-CERTIFICATES.md](U1-CERTIFICATES.md). Both parity sectors
are enclosed; even-probe overlaps cannot certify access to an odd state.

## Fixed requests and verification

The ten development cells use K=40,80,160,320,640. Each rung retains five
even eigenvalue enclosures, the first odd enclosure, four exactly
reflection-even candidate vectors, residual bounds, overlap intervals,
moments and correlation intervals. Times use the new scalar archive's
first-even gap; none of the old convention's bounds are reused as results.
Failures remain explicit and do not cancel later requests.

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_u1_design_certificate_run.py --output research/vacuum-spectrum/u1-design-certificates.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_u1_design_cert*.py' -v
```

Tests cover exact decimal coefficients, the corrected free spectrum and
Haar moments, both omitted tails, parity leakage, false endpoints and
vector bounds, and nonfinite failure continuation. The report pins the
new scalar archive and all computational sources. The original archives
remain historical evidence. Direct propagation and temporal qualification
must still be regenerated. Registration, pilot replication and independent
review remain outstanding; targets are unrun.
