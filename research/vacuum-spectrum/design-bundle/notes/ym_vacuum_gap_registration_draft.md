<!-- commentary -->
# Vacuum–spectrum two-axis study — registration draft

Date: 2026-09-08. Task: `ym-vacuum-gap-litcheck`.
State: **unregistered design; target cells unrun**. No P or LC ID assigned.
This note specifies the next finite-model instrument study. It does not
register a prediction, assert a repo status, or promise a continuum result.
Its source context is [the LITCHECK draft](ym_vacuum_gap_litcheck.md).

## Scope and proposed question

For the one-plaquette SU(2) model already implemented, which vacuum
moments and centered operators actually see the lowest excitation, and
which apparent connections disappear under derived nulls?

This is a calibration and diagnostic study. The exact identities below
are checks, not discoveries. The previously run pilot cells remain
replication data. No claim that a finite list of moments suffices for
a Yang–Mills gap is registered here.

The physical hypothesis a later mechanism study would need is of the form

\[
D(\nu_r,K_r)\Longrightarrow \Delta_r/s_r\geq\delta_*>0
\quad\text{for every regulator }r\text{ on a specified trajectory}.
\]

It must define D, the kinetic form K, reference energy s, a quantitative
delta_star and the theory class. An unspecified positive scalar diagnostic
is not such a hypothesis. In particular, finite gaps that decrease
along a finite ladder alone cannot disprove strict positivity in a limit.

## Method: lessons consulted before design

The actual repository tool was run on the inspected base with:

```sh
python3 scripts/tools/lessons.py vacuum spectrum scan observable gauge symmetry ratio scaling finite-size bound detector tolerance window decay mode reimplementation mutant held-out identity
```

Returned IDs: **L-1, L-2, L-3, L-5, L-6, L-8, L-11, L-13, L-15,
L-16, L-17, L-18, L-20, L-21**.

Application: derive centering and selection identities (L-2, L-20);
price resolution and time windows per cell (L-1, L-3, L-5, L-16, L-21);
compute ordered eigenpairs rather than scan for levels (L-6); count
every requested cell, including failures (L-11); distinguish premise
deformations from analysis bugs and duplicate mutants (L-8, L-13,
L-17); preserve holdouts (L-15); retain executable provenance for
any later registered numerical tolerance (L-18).

The finite calculation is deterministic. Random-seed checks are not a
substitute for independent discretizations; if sampling is introduced
later, its own seed and effective-sample requirements must be registered.

## Fixed model, units and cells

Let P = Tr(W)/2 = cos(x), x in [0,pi], acting on gauge-invariant class
functions with normalized Haar weight (2/pi) sin squared x dx. Use the
pilot's energy convention, with its additive constant omitted:

\[
H(g,\eta)=4g^2 C_2-\frac{2\eta}{g^2}P,
\qquad C_2\chi_j=j(j+1)\chi_j.
\]

The off-diagonal matrix element between j and j+1/2 is -eta/g squared.
Eta = 1 is the pilot model; eta = 0 removes magnetic hopping. Changing
eta defines a specified finite-model deformation, not a claim about the
same continuum pure Yang–Mills theory. U(1) is a different-theory control.

| Partition | Fixed cells | Role |
|---|---|---|
| Development / replication | Pilot g values: 0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 1.00, 1.50, 2.00, 3.00; eta = 1 | Reproduce archived gap convention; may be used to debug |
| Target characterization | g = 0.125, 0.25, 0.40, 0.60, 0.85, 1.25, 2.50; eta = 0, 0.5, 1 | 21 SU(2) cells, none run in this task |
| Matched Abelian targets | Same 21 cells with H = 4 g squared n squared - 2 eta cos(theta)/g squared on the periodic circle | Instrument discrimination and convention control |
| Analytic calibration | Controls below | Identities with stated exact responses; not counted as new predictive evidence |

These g values are model-characterization coordinates, not a presumed
asymptotic continuum window. No inference outside the listed domain is
licensed. A wider coupling, deformation or spatial-volume search needs
a separate frozen manifest.

## Outputs on the two axes

For each SU(2) cell retain E0, the first three ordered gaps, the normalized
ground vector, and the following quantities. Report moments in the fixed
Haar/trace convention; no string-tension normalization exists here.

\[
V=(\langle P\rangle,\langle P^2\rangle,
\operatorname{Var}(P),\operatorname{Var}(P^2),
\operatorname{Cov}(P,P^2)).
\]

This vector contains a known redundancy: Var(P) = mean(P squared) minus
mean(P) squared. Record the identity as a check, not an extra feature.
The corresponding spectral outputs are

\[
S=(\Delta_{10},\Delta_{20},m_P,m_{P^2},
 |\langle1|\widetilde P|0\rangle|^2,
 |\langle1|\widetilde{P^2}|0\rangle|^2).
\]

Also retain the connected 2-by-2 correlator matrix for (P,P squared),
spectral weights, usable time windows and each error component.
For U(1), report the analogous cos(theta) observables and distinguish
its full rotor gap from an even-operator threshold. No 0++/0-+ glueball
label is assigned to these one-coordinate excitations.

Compute polynomial multiplication before projection: P squared means
the projected multiplication operator for cos squared x, not blindly
the square of a cutoff P matrix. Use sufficient padding or exact
character-product identities, and include a cutoff-edge check. This
prevents changing the observable while increasing the basis.

## Derived null responses and mutations

| Control | Exact response / derivation | Failure it must expose |
|---|---|---|
| Observable offset | O -> O+cI changes the mean by c; the centered state and C_O(t) are identical | Uncentered correlator presented as connected, or a mean treated as a spectral measurement |
| Energy offset | H -> H+cI changes E0 but not E_n-E0 | Positive absolute energy floor reported as excitation gap |
| Overall clock | H-E0 -> alpha(H-E0), alpha > 0; same vacuum, gaps multiply by alpha, C(t) -> C(alpha t) | Units mistaken for a physical change of vacuum structure |
| Free SU(2), eta = 0 | Omega = chi_0; P Omega = chi_(1/2)/2; (P squared - 1/4)Omega = chi_1/4 | A gauge-invariant operator can miss the first excitation |
| Tensor-sum clock separation | H_eps = (I-X) tensor I + eps I tensor (I-X), 0 < eps <= 1; all terms positive, Omega = ++, eigenvalues 0, 2eps, 2, 2+2eps | Even the full unchanged ground state does not fix a uniform gap when the kinetic generator changes; the strong coefficient stays 1 |
| Hidden low state | H = diag(0,eps,1), O = |2><0| + |0><2|; C_O(t) = exp(-t) while Delta = eps | One correlator alone reported as the full gap |
| Gapless spectral support | dmu(E) = exp(-E)dE on positive E gives C(t) = 1/(1+t) | A finite-window positive effective mass reported as a positive limiting gap |
| Finite-time disconnected term | For Hermitian O, raw G(t) = mean(O) squared + C_O(t); if the mean is nonzero its late-time logarithmic slope tends to zero | Missing vacuum subtraction mistaken for physical gap closure |

For the free SU(2) row, Haar orthonormality gives explicitly

\[
\langle P\rangle=0,\quad\langle P^2\rangle=\tfrac14,
\quad C_P(t)=\tfrac14e^{-3g^2t},\quad
C_{P^2}(t)=\tfrac1{16}e^{-8g^2t}.
\]

Thus the two channels see 3g squared and 8g squared respectively, with
the same vacuum. The tensor-sum row is a non-Yang–Mills premise control;
its eps -> 0 limit acquires degeneracy. It demonstrates absence of a
uniform gap over that family, not a gapless pure Yang–Mills vacuum.

For the gapless row and a time step h > 0,

\[
m_{\rm eff}(t;h)=\frac1h\log\frac{1+t+h}{1+t}>0,
\qquad \lim_{t\to\infty}m_{\rm eff}=0.
\]

This is the required featureless positive-slope background: positivity
of a measured finite-time slope by itself is not a detection criterion.
The graph and hidden-state controls perturb different things: the former
changes dynamics at fixed vacuum; the latter changes operator coverage.

Analysis-bug mutants must include omitted centering, wrong Haar weight,
absolute E1 instead of E1-E0, and a missing target row. The comparator
must reject each for the specific identity or coverage condition it
breaks. A mutant that does not move its named check is non-discriminating
and cannot be pinned as a successful falsifier.

## Eigenpairs, truncation and temporal windows

Two independent implementations are required before target execution:

1. Character basis j = 0, 1/2, ..., J. Use the full ordered eigenbasis
   for the finite matrix, or certified ordered low eigenpairs plus a
   bound for omitted spectral weight.
2. Angle-space Dirichlet problem for phi = sin(x) psi:

\[
H_\phi=-g^2\partial_x^2-g^2-2\eta g^{-2}\cos x,
\qquad\phi(0)=\phi(\pi)=0.
\]

This multiplication by sin(x) handles the Haar measure; using a flat
measure directly for psi is a distinct, incorrect model. For U(1) use
both Fourier modes and a periodic angle implementation, retaining both
parities in the spectral comparison.

The fixed refinement ladders are J = 20, 40, 80, 160, 320; angle-grid
interiors = 600, 1200, 2400, 4800; U(1) Fourier n_max = 40, 80, 160,
320, 640. Use nested rungs, not a single selected cutoff. Reaching the
last rung without the error requirement is an unresolved cell, not a
pass and not a gap-collapse observation.

The proposed numerical accuracy goal is an absolute error of at most
10 to the minus 6 in a bounded moment and a relative error of at most
10 to the minus 6 in a resolved finite-model gap. This is a computation
budget for approximately six significant digits, not a physical signal
threshold. Before registration, the derive code must show how solver
residuals, cutoff tails, quadrature and mesh error attain that budget on
development cells and estimate the cost on the target domain. If they
cannot, amend the design before running targets; do not widen bands after
seeing target data. Any rigorous enclosure requires an actual enclosure
argument; adjacent-rung agreement alone is a numerical convergence check.

For spectral sums, verify sum of weights = C_O(0) = Var(O). An overlap
whose error includes zero is **unresolved**, unless an exact symmetry
sets it to zero. Discarding a small positive overlap changes the reported
asymptotic threshold. Retain that uncertainty, including cases in which
the lightest state becomes visible only beyond the available time window.

For a resolved leading weight w1 > 0 and next accessible energy m2 > m1,
the positive spectral sum has

\[
C(t)=w_1e^{-m_1t}(1+r(t)),\quad
0\leq r(t)\leq\frac{W_{\rm tail}}{w_1}e^{-(m_2-m_1)t}.
\]

Hence the finite-step logarithmic slope lies above m1, with bias bounded by

\[
0\leq m_{\rm eff}(t;h)-m_1
\leq h^{-1}\log(1+r(t)).
\]

Place a window from this per-cell bound and the chosen numerical error
budget. Do not set one universal late time. If weight or tail bounds
are unavailable, or numerical errors dominate C(t), return unresolved.
Do not borrow the interacting spectrum to price a free or deformed
cell's window. Finite periodic Euclidean-time data would additionally
require backward terms; the present Hamiltonian semigroup is at zero
temperature and has no periodic time extent.

An independent angle-space semigroup evaluation should be compared with
the character-basis spectral sum. Evaluating a correlator and fitting it
using the same eigenvalues is only an internal identity check, not an
independent spectral determination.

## Registered outcomes to freeze before execution

| Outcome | Decision rule | Permitted interpretation |
|---|---|---|
| Instrument failure | Any exact null fails beyond the derived numerical error; a requested row is missing; measure, domain or projection differs between implementations | Repair the derive layer; a registered target run would require a new registration |
| Numerical unresolved | Refinement cap, overlap uncertainty or temporal error budget prevents a comparison | Report missing precision explicitly; never replace with zero or count as held |
| Instrument agreement | Independent methods agree within the precomputed budgets; exact controls give their declared responses | Finite-model instrument calibration |
| Diagnostic separation | V or a channel threshold changes under a specified deformation; report the actual component and the Hamiltonian change | Empirical characterization within this model; no necessity/sufficiency conclusion without a predicate |
| Mechanism sufficiency failure, later study only | The preregistered D holds but its quantitative lower bound fails on an admissible, controlled system | Reject that implication in the stated theory class |
| Necessity failure, later study only | D is false while the specified gap condition holds | Reject necessity of D; sufficiency remains a different question |

Target numeric readings are intentionally not guessed. Every target row
must have values or an explicit failure/unresolved reason. Report the
numbers, numerical errors and missing overlap coverage; do not compress
the study into a single positive-gap flag. A finite operator-basis
Rayleigh minimum approaches the gap from above under its assumptions
and cannot be presented as a lower-bound certificate.

## Transition to a connected-lattice study

The following belongs in a separate registration after this instrument
exists, rather than masquerading as observables already implemented:

- Fix SU(2) or SU(3), spatial dimension, link Hamiltonian, Gauss-law
  implementation, boundaries, physical sector, and a connected lattice
  family. Independent plaquettes are not a thermodynamic Yang–Mills model.
- Fix the predicate D and admissible physical deformations. Changes of
  updating algorithm, smearing or operator basis are analysis controls;
  physical action/Hamiltonian changes have to be named separately.
- At each lattice spacing resolve representation/numerical truncation;
  study increasing physical volume; then compare continuum trajectories
  at a specified reference scale. Preserve the distinction between a
  dimensionless lattice gap and a physical mass.
- Measure spatial-loop/equal-time state data, physical temporal decay
  and operator coverage. Add four-dimensional chi_t only with a valid
  spacetime definition and sampling/flow prescription. Large temporal
  Wilson loops and chi_t already contain dynamical information.
- Freeze raw values plus dimensionless ratios, denominator covariance,
  all symmetry-channel coverage, and finite-size failure conditions.
  A sigma-based ratio is unavailable when sigma vanishes or cannot be
  resolved; select and freeze a valid alternative scale before analysis.
- A proposed lower bound must control the full physical form domain.
  Finite-basis variational estimates and ansatz fits alone do not do this.

## Before this draft becomes a registration

Allocate the P/LC identifiers through the repository assignment process;
implement and archive the derive code and its null responses; freeze
source/code hashes, all numerical error formulas, manifest, and result
schema; commit the registration before executing target cells. An
integrator can then use the existing serial PR and gate workflow.
These are outstanding execution prerequisites, not a request to approve
an unwritten experiment. This task delivers the complete design draft.
