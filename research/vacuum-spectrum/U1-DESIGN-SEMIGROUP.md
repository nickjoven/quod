# Direct propagation for the recovered U(1) design

The runner uses the corrected full periodic matrix from `vacuum_u1_design`
and independently evolves centered P and P^2 vectors using sparse BDF.
Its inputs are `u1-design-development.json` and `u1-design-certificates.json`;
it never substitutes legacy-convention numerical results. Both source and
input hashes are checked before work starts.

The ten development g values at eta=1 retain four periodic grids and two
tolerance settings, for 80 evolutions. Thirty ground preparations are fresh;
ten finest-grid grounds are explicitly reused from the corrected scalar
archive. The physical sample times come from the corrected certificate
archive, with tau=0,.125,.25,.5,1,2,4,8,12,16,20,24 divided by each cell's
first-even gap. The full rotor gap is separately reported.

Calibration uses the corrected free dispersion 4g^2(lambda+h^2 lambda^2/12),
Haar variances 1/2 and 1/8, and rtol=1e-10, atol=1e-13. Production retains
(rtol,atol)=(1e-8,1e-18) and (1e-10,1e-20). Tolerance differences are diagnostic;
combined errors use exact model correlation intervals and conservative
mixture-plus-numerical slope bounds. Every adjacent sampled pair is assessed
for both observables against the original 1e-6 budget. No unsampled window
is inferred and none is registered or chosen for target execution.

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_u1_design_semigroup_run.py --output research/vacuum-spectrum/u1-design-semigroup.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_u1_design_semigroup*.py' -v
```

The original-method rationale and limitations in [U1-SEMIGROUP.md](U1-SEMIGROUP.md)
apply to this corrected operator. The analytic/arithmetic trusted base is
unchanged; these remain finite-model development findings. Failure handling,
parity-specific gap mapping and dense exponential agreement are tested.
All 42 target rows remain unrun.
