# Exact U(1) parity-sector certificates

State: **unregistered model certificates; no target selected or executed**.

## Operator and sector endpoints

The convention is the same explicit development model as [U1.md](U1.md).
Even cosine modes start at n=0, with first hopping sqrt(2)b and subsequent
hoppings b=-eta/g^2. Odd sine modes start at n=1 and have hopping b throughout.
Both have diagonal g^2 n^2. The source-pilot normalization remains unverified.

The characteristic-determinant recurrence uses the squared hoppings, which
are exactly 2b^2 and b^2. Clearing positive rational denominators makes every
Sturm sign calculation an integer operation without approximating sqrt(2).
Zero hoppings split the matrix into independent blocks; strict endpoint
counts handle free degeneracies explicitly.

For either sector truncated at mode K, the omitted tail starts at K+1 and
has lower bound T=g^2(K+1)^2-2|b|. Its boundary hopping is b. The same Schur
argument as in [CERTIFICATES.md](CERTIFICATES.md) gives a lower count matrix
A-x-b^2/(T-x)e_last e_last^T for x<T. Finite-sector Ritz bounds give upper
endpoints. The global floor -2|b| follows from the cosine multiplication
operator's norm, including in the even sector with its larger first hopping.
It does not rely on applying an incorrect uniform-row Gershgorin bound there.

The first five even energies and the lowest odd energy are enclosed. Every
endpoint is checked afresh without relying on the floating-point eigensolver
or bisection history. Inadequate cutoff bounds remain broad or unresolved.

## Exact parity and overlap propagation

Numerical cosine eigenvectors are embedded into the bilateral Fourier basis
n=-K,...,K. Their stored binary64 coefficients are treated as exact dyadic
numbers. The certificate requires q_n=q_-n exactly. Thus the candidate and
its residual lie in the even sector, and even-sector neighbor separation can
be used in the residual-to-eigenvector bound. A tiny unaccounted odd component
would invalidate that shortcut and is explicitly rejected.

Residual arithmetic uses the full bilateral Hamiltonian and includes both
omitted coefficients b q_-K and b q_K. All observable multiplications pad
both ends before projecting. Normalization, eigenvector distance, moments,
transition amplitudes and weights use rational/outward calculations as in
the SU(2) instrument, but with bilateral P rather than half-line P.

Odd transition weights for these even observables are zero by exact reflection
symmetry. A small numerical odd overlap is not interpreted as physical overlap.
The retained even weights and omitted even covariance then enter the existing
interval semigroup sum with the next even-energy tail bound.

## Full gap and observable reference

The certificate first verifies that the even ground lies below the lowest odd
state. The full gap is the minimum of the first even and first odd excitation
energies, relative to that ground. Disjoint sector intervals can prove that
the odd state sets the full gap. At free degeneracy, overlapping intervals
retain the degeneracy/ordering uncertainty rather than inventing a parity
ordering.

The observable reference is the first even gap, conditional on a certified
nonzero overlap for the observable. It is never replaced by the lower odd
gap. Scalar budgets check both the full gap and first three even gaps, as well
as the five vacuum components, using the original 1e-6 midpoint-radius goals.

Correlation certificates are evaluated on the existing extended tau ladder,
with times set by the archived finest first even gap. Those binary64 times are
treated as exact dyadic sample coordinates. Direct U(1) propagation and window
qualification are subsequent work; this run does not assign a window.

## Reproduce and verify

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_u1_certificate_run.py --output research/vacuum-spectrum/u1-certificates.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum_u1_cert*.py' -v
```

All 50 fixed Fourier rungs are preallocated and checkpointed. Exact endpoint,
residual, overlap and correlation data and hexadecimal candidates are retained
for replay. Nonfinite failures do not cancel later requests. The arithmetic
and analytic trusted base remains explicit; these checks are not an independent
formal proof or a registered field-theory conclusion.
