# U(1) implementation of the recovered design

## Operator and reuse

The recovered experiment specifies H=-4g^2 d_theta^2-2 eta cos(theta)/g^2
with Haar measure dtheta/(2pi). `vacuum_u1_design.py` uses the exact parameter
identity H_design(g,eta)=H_legacy(2g,4eta) for both independently assembled
Fourier and periodic-angle operators. In binary arithmetic multiplication by
2 and 4 is exact when representable; nonfinite mapped inputs are rejected.
The physical report coordinates remain the original g and eta. This mapping
is internal algebra, not execution of new physical cells.

A direct bilateral dense matrix independently checks kinetic diagonal
4g^2 n^2 and hopping -eta/g^2. The free full gap is 4g^2. The interaction
checks preserve the potential coefficient and demonstrate that vacuum
moments differ from the earlier convention; this is not an overall clock
change. The legacy instruments and archives remain unchanged.

## Development execution

Ten original development g values at eta=1 use Fourier cutoffs
40,80,160,320,640 and periodic grids 600,1200,2400,4800. Both parity sectors
are retained. The first even gap and full rotor gap remain distinct.
The runner has 90 representation requests, checkpoints every request,
continues after failures, pins source/design hashes and keeps all 42 targets
unrun. Its command-line output is restricted to the new report path.

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_u1_design_run.py --output research/vacuum-spectrum/u1-design-development.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_u1_design*.py' -v
```

Scalar agreement retains the 1e-6 budget and both adjacent-rung and
cross-representation comparisons. Agreement alone is not an enclosure.
Exact residual/tail/overlap certificates and independent propagation must
be regenerated for this coefficient and cutoff ladder before claiming
qualified sampled windows. Pilot replication additionally needs the missing
pilot code/JSON; quoted handoff values alone do not establish its convention.
