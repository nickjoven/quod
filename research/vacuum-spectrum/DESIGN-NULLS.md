# Exact nulls from the recovered design

The new `design-nulls.json` implements the specific families in the recovered
registration draft. Earlier uniform-measure and degenerate-ground fixtures
remain additional controls; they do not replace these requested families.

| Null | Exact construction and response |
| --- | --- |
| Tensor sum | H=(I-X) tensor I + epsilon I tensor (I-X); eigenvalues 0,2epsilon,2,2+2epsilon; normalized ground (1,1,1,1)/2 is fixed |
| Hidden state | H=diag(0,epsilon,1), O couples vacuum only to the energy-1 state; full gap epsilon, C(t)=exp(-t) |
| Exponential spectral measure | density exp(-E) for E>0; C(t)=1/(1+t); mass below epsilon is 1-exp(-epsilon)>0 |
| Raw disconnected term | G(t)=9+exp(-2t); raw slope tends to zero while the centered single-mode slope is 2 |

The tensor matrix, eigenvectors and products use exact rational arithmetic
through NumPy object arrays. Epsilon samples 1,1/2,1/8,1/32 verify the formulas;
the stated limiting gap follows from the explicit 2epsilon formula, not an
extrapolation of finite data. The exponential measure's Laplace integral is
integral exp[-(1+t)E] dE = 1/(1+t). Its positive mass on every neighborhood
of zero establishes the support infimum; a finite positive fitted slope
cannot establish a gap. For h=1 its slope is log((t+2)/(t+1)), which tends
to zero. The raw slope is log((9+exp(-2t))/(9+exp(-2t-2))) and also tends
to zero. These formulas establish the limits; sampled outward intervals
check their numerical evaluation.

The report checks centered versus raw slopes at times 0,1,4,16,64, low-energy
mass intervals, the tensor eigensystem and hidden spectral weights. It
rejects four corresponding analysis mutations. These are analytic controls,
not new numerical solver mutants or target cells. The existing solver-level
Haar, centering, energy-offset and coverage checks remain separate evidence.

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_design_nulls.py --output research/vacuum-spectrum/design-nulls.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_design_nulls.py' -v
```

The archive pins computational and source-design hashes and is reproduced
by its regression test. All 42 targets remain unrun. No field-theory
conclusion or retrospective registration is implied.
