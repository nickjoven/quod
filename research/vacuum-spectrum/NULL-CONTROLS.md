# Remaining analytic null controls

State: **development analysis fixtures; targets unrun; unregistered**.

## Controls and expected distinctions

The exact fixtures complete the named hidden-state, tensor-sum, gapless and
disconnected analysis controls, alongside offset, clock and centering checks.
They are distinct from the existing solver-level calibration mutants.

| Control | Exact construction | Required interpretation |
| --- | --- | --- |
| Hidden state | Energies 0,1,2; probe couples only to energy 2 | Full ordered gap 1; observed threshold 2 |
| Tensor sum | Energies of A are 0,epsilon; B are 0,3; probe acts only on B | Full gap epsilon can shrink while the observed threshold stays 3 |
| Gapless | Vacuum plus L2([0,1]); excited H multiplies by E; probe creates the constant function | Uniform spectral measure has support down to zero and no positive gap |
| Disconnected vacuum | Energies 0,0,1; probe couples the selected vacuum to both other states | Subtracting its mean leaves zero-gap weight 1; gap above the whole ground space remains 1 |
| Offset | Add 7 to every energy | Every gap and centered spectral weight is unchanged |
| Clock | Multiply every energy by 3 | Gaps scale by 3; weights do not |

In the disconnected fixture, the first ordered gap, the gap above the ground
space, and the observable threshold are different quantities. The report
retains ground multiplicity and zero-gap weight rather than collapsing these
quantities into a single gap field.

## Gapless analytic reference

On C direct-sum L2([0,1]), the distinguished vacuum has energy zero. The
excited operator is multiplication by E, and the probe maps the vacuum to
the normalized constant function. Its spectral mass on [0,epsilon] is exactly
epsilon for every 0<epsilon<=1. Thus its spectral support reaches zero.
The correlation is

```text
C(0)=1,
C(t)=integral_0^1 exp(-Et)dE=(1-exp(-t))/t  for t>0.
```

Its long-time decay is algebraic, not a positive-rate exponential. The code
uses outward exponential intervals to check finite-time effective-gap
behavior. Those samples do not establish the gapless limit; the exact
spectral construction and mass formula establish it. The dyadic mass fixtures
test the implementation of that formula without claiming that finitely many
tests prove a limiting theorem.

## Executable checks

The four analysis mutants assign the full gap to a dark observable, omit
centering, drop a degenerate zero mode, and assert a positive floor below
which the uniform measure demonstrably has positive mass. All must fail
their relevant control. These are analytic analysis mutations, not new
mutations of the SU(2) or U(1) numerical solvers.

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_null_controls.py --output research/vacuum-spectrum/null-controls.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_null_controls.py' -v
```

The deterministic report retains exact rational quantities and source hashes;
the regression test reproduces the archive. It executes no development or
target solver cells. These controls do not substitute for U(1), source-pilot
conventions, registration, or the outstanding independent review.
