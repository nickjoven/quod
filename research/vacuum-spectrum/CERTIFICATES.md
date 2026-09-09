# Rational character certificates and angle error bounds

State: **unregistered development instrument; no target selection or execution**.

## Mathematical scope

The operator is the self-adjoint Jacobi operator on l2 of the nonnegative
integers, with diagonal d_n = g^2 n(n+2) and hopping b = -eta/g^2. Couplings
are exact rationals given by their declared decimal spellings. The diagonal
tends to infinity; the hopping is bounded, with norm at most 2|b|. Thus the
operator is bounded below and has discrete spectrum with compact resolvent.
The calculations below concern this stated single-angle character model.
They are not a Yang-Mills field-theory bound or a Lean-registered theorem.

Character multiplication P is (S+S*)/2 on this half-line, hence ||P||<=1.
The two observables are P and P^2. Multiplication retains all padded
coefficients before projection, so no quadrature is used in the certificate.
The candidate eigensolver is only a source of approximate vectors. Its
eigenvalues, residual estimates, and floating-point ordering are not trusted
as certificate endpoints.

## Ordered eigenvalue enclosure

Split H at dimension N into a finite tridiagonal A, an infinite tail D, and
the single boundary hopping b. Since d_n increases,

```text
D >= T I,  T = g^2 N(N+2) - 2|b|.
H >= -2|b| I.
```

For a rational x<T, D-x is positive and its inverse is bounded above by
1/(T-x). Completing the square in the block quadratic form gives the Schur
complement S(x)=A-x-B(D-x)^(-1)B*. Consequently,

```text
S(x) >= A-x - b^2/(T-x) e_last e_last^T = S_lower(x).
```

The number of eigenvalues of H strictly below x equals the negative inertia
of S(x), which is at most the negative inertia of S_lower(x). Therefore,
if the latter count is at most k, x is a lower bound for lambda_k(H).
Conversely the variational principle gives lambda_k(H)<=lambda_k(A).
An exact finite-matrix count greater than k at an upper endpoint u proves
lambda_k(H)<u. The global floor -2|b| supplies a fallback lower bound.
When a finite upper endpoint is not below T, the instrument retains that
fallback rather than pretending the tail is separated.

Both counts use the integer characteristic-determinant recurrence after
clearing positive denominators:

```text
p_0=1, p_1=a_0-x,
p_(i+1)=(a_i-x)p_i - b^2 p_(i-1).
```

Count sign changes after deleting zeros. For a nonzero hopping, adjacent
minors cannot both vanish, and at an interior zero the surrounding signs are
opposite. A zero final determinant is excluded, giving the strict-below
convention. Zero hopping is handled directly as a diagonal matrix, including
repeated diagonal values. This convention is tested separately; it differs
from some LAPACK endpoint conventions. [LAPACK's Sturm-count routines](https://www.netlib.org/lapack/explore-html/d7/d17/group__larrc_ga3231a0223469285220d5dfd3b35c9c7c.html)
are the standard floating-point counterpart; the certificate uses Python
integers to avoid uncertain pivot signs.

The first five eigenvalues are enclosed on each existing character rung.
Bisection stops at a rational search width <=2^-44 for each endpoint search.
This does not promise that the combined infinite-operator interval is that
narrow: the coarse cutoff may leave a large upper/lower separation.
`verify_enclosures` checks the endpoints afresh without bisection history.

## Eigenvector and overlap uncertainty

A stored candidate q is interpreted as an exact dyadic vector, extended by
zero into the tail. Its norm and full residual are computed with Fraction
arithmetic, including the omitted hopping component b q_(N-1). For the
midpoint mu of its certified eigenvalue interval, let

```text
rho^2 = ||Hq-mu q||^2 / ||q||^2.
```

Neighboring eigenvalue enclosures give a lower separation s between mu and
all eigenvalues other than the desired lambda_k. If s<=0, the vector remains
unresolved. Otherwise the spectral expansion of the residual gives
sin(theta)<=rho/s. Choosing the sign of the exact normalized eigenvector u
to align with v=q/||q|| gives ||u-v||<=sqrt(2)sin(theta)<=2rho/s. The code caps
this distance at 2, a universal normalized-vector bound. Rational square-root
enclosures use integer square roots, rounded outward to a dyadic grid.

For either observable O, ||O||<=1. Thus the transition-amplitude error obeys

```text
|<u_k,O u_0> - <v_k,O v_0>| <= delta_k + delta_0.
```

The approximate amplitude normalization is itself enclosed outward. Squaring
its signed interval yields a nonnegative weight interval. An interval that
contains zero does not establish a zero or nonzero overlap; only a strictly
positive lower weight establishes a nonzero overlap. Signs of different
eigenvectors do not matter, but both observable amplitudes use the same sign
for each eigenvector, preserving signed cross weights.

## Vacuum moments and correlation enclosure

For m=1,...,4, the expectation <v_0,P^m v_0> is computed exactly with full
padding. Its difference from the exact ground expectation is at most
2 delta_0. Interval products/subtractions then enclose both means and the
full 2-by-2 vacuum covariance V. Even moments and variances are intersected
with their known nonnegative domains.

The retained first three excited states have weight and signed cross-weight
intervals and gap intervals. Summing their interval exponential contributions
encloses their part of C(t). For the omitted states, positivity implies

```text
R_aa(0) <= V_aa.upper - sum(retained weight lower bounds),
|R_01(t)| <= sqrt(R_00(0).upper R_11(0).upper) exp(-Delta_4.lower t),
R_aa(t) <= R_aa(0).upper exp(-Delta_4.lower t).
```

Here Delta_4.lower uses the fifth ordered eigenvalue enclosure and the
ground upper endpoint. If any required gap is not positive, correlation
certification remains unresolved. At t=0, the direct vacuum covariance
interval is used instead of the looser retained/tail split.

All interval algebra is rational except the exponential. Python's
[Decimal.exp contract](https://docs.python.org/3.10/library/decimal.html#decimal.Decimal.exp)
specifies correct rounding. The implementation converts the rational argument
in both directed rounding modes, exploits monotonicity, then expands each
correctly rounded exponential by one adjacent Decimal number. The endpoints
are converted back to exact rationals. Independent rational alternating-series
tests check these enclosures. No floating-point exp result is promoted to a
certificate endpoint without this rounding allowance.

## End-to-end angle error and limits

The archived binary64 time samples are treated as exact dyadic times. For
an archived angle entry y(t) and a certified model interval [L(t),U(t)],

```text
|y(t)-C(t)| <= max(|y(t)-L(t)|, |y(t)-U(t)|).
```

This bounds the total angle result error at that time, encompassing grid,
ground, quadrature, parameter-rounding, and propagation discrepancies without
adding unvalidated estimates for those components. It does not separately
identify each component or bound unsampled times. Normalization uses a lower
bound on sqrt(V_aa V_bb), so the normalized error remains conservative. If
that denominator is not positive, the normalized bound remains null.

The original 1e-6 scalar goals are checked using interval midpoint radii:
absolute moment radius <=1e-6 and gap radius/lower gap <=1e-6. Correlation
error bounds are retained as numbers; no new detection tolerance or accepted
channel window is silently introduced. Nonzero-overlap evidence in this model
does not complete the registration, source-pilot, U(1), or control prerequisites.

The trusted base comprises these analytic arguments and Python integer,
Fraction, Decimal, and serialization correctness. Endpoint and replay tests
are executable checks, not an independent formal proof of the analytic
arguments. Inadequate cutoffs, failed solves, and unresolved intervals remain
visible. Original development and semigroup sources and reports are preserved.

## Run and verify

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/vacuum_certificate_run.py --output research/vacuum-spectrum/certificates.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s scripts -p 'test_vacuum*.py' -v
```

The runner preallocates the same 50 character requests, checkpoints each
request, retains exact rational endpoints and hexadecimal candidate vectors,
and records source/input hashes. A failed request does not cancel later
requests. No target interface exists. The exact replay verifies stored
endpoints, residual bounds, overlaps, moments, and correlation intervals.
