<!-- commentary -->
# Yang–Mills vacuum structure and spectral gap — LITCHECK draft

Date: 2026-09-08. Task: `ym-vacuum-gap-litcheck`.
Repository: `nickjoven/proslambenomenos`.
Base inspected: `da0084147986a97f355954be6b0eff4246b9d852`.

This is a literature synthesis and a proposed mathematical formulation, not
a claim-status entry. No LC, P, R, or LAW number has been allocated. The
companion [experiment draft](ym_vacuum_gap_registration_draft.md) has not
been registered or run. Source classifications below concern the cited
literature; they do not change any repository claim.

## Question and disposition

**What gauge-invariant information in the vacuum, together with specified
dynamics, can control the bottom of the nonvacuum spectrum uniformly?**

The distinction between a vacuum expectation and an excitation threshold
is standard. A generic nonzero expectation supplies no such bound. A
concrete intermediate target is a Poincaré inequality for the vacuum
measure with the physical kinetic form. Establishing it uniformly for
continuum four-dimensional pure Yang–Mills remains an obligation, not an
outcome of this review.

Two corrections to the preceding conversation matter for the experiment:

1. **Sufficiency and necessity require different counterexamples.** For a
   stated predicate D, sufficiency means D implies a gap. It fails when D
   holds but the gap conclusion fails. A gap surviving a change in the
   numerical diagnostic establishes neither failure of sufficiency nor
   failure of necessity. Failure of necessity requires the predicate to
   become false while the gap remains.
2. **The proposed vacuum vector mixed different kinds of information.**
   An equal-time configuration distribution, theta response, and temporal
   Wilson-loop decay are not disjoint sources of spectral information.
   Call these distinct diagnostics, not mathematically independent axes.

## Source table

Links point to primary papers or the official problem statement. The
Douglas review is explicitly secondary context. Access depth is recorded
so that an abstract is not passed off as a full-paper audit. Equations
derived later in this note stand on the displayed assumptions and algebra.

| Key | Source and inspected location | What it supports | Limit of the import |
|---|---|---|---|
| S1 | Jaffe–Witten, [Quantum Yang–Mills Theory](https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf), §§3–6, especially PDF pp. 5–7; full text | Vacuum normalization, gap definition, clustering, uniform-volume issue | A formulation of the problem; no construction or gap proof |
| S2 | Osterwalder–Schrader, [Axioms for Euclidean Green's functions II](https://doi.org/10.1007/BF01608978), CMP 42 (1975), 281–305; publisher abstract | Conditions for Euclidean data to continue to a relativistic theory; corrects/extends part I | Reflection positivity alone is not the complete reconstruction hypothesis |
| S3 | Hastings–Koma, [Spectral Gap and Exponential Decay of Correlations](https://arxiv.org/abs/math-ph/0507008), CMP 265 (2006), 781–804; abstract | Gap implies connected clustering in the stated lattice spin/fermion setting | The locality and interaction hypotheses cannot be silently transferred to an unbounded gauge Hamiltonian |
| S4 | Elitzur, [Impossibility of spontaneously breaking local symmetries](https://doi.org/10.1103/PhysRevD.12.3978), PRD 12 (1975), 3978; publisher abstract | Obstruction to spontaneous local gauge-symmetry breaking without gauge fixing | Use observables with nontrivial gauge transformation law and zero gauge average; an operator with an invariant component need not have zero expectation |
| S5 | Greensite–Olejník, [Dimensional Reduction and the Yang–Mills Vacuum State in 2+1 Dimensions](https://arxiv.org/abs/0707.2860), PRD 77 (2008), 065003; abstract | Approximate vacuum functional, confinement via dimensional reduction, numerical mass estimate after fixing a parameter by string tension | An ansatz in 2+1 dimensions, not a theorem in 3+1 dimensions |
| S6 | Greensite–Olejník, [Numerical study of the Yang–Mills vacuum wavefunctional in D=3+1 dimensions](https://arxiv.org/abs/1310.6706), PRD 89 (2014), 014506; full HTML, §§II–IV | Relative weights of prescribed time-slice configurations; tests of long-wavelength dimensional reduction | Restricted configuration families do not determine or certify the whole wavefunctional |
| S7 | Athenodorou–Teper, [SU(N) gauge theories in 3+1 dimensions: glueball spectrum, string tensions and topology](https://arxiv.org/abs/2106.00364), JHEP 12 (2021), 082; abstract | Separate lattice determinations and continuum extrapolations of spectrum, tension, topology and coupling | Numerical evidence; neither independence nor a theorem relating their values |
| S8 | Bali–Bauer–Pineda, [Model-independent determination of the gluon condensate](https://arxiv.org/abs/1403.6477), PRL 113 (2014), 092001; full HTML, equations (5)–(12) | Perturbative subtraction and prescription ambiguity of order Lambda to the fourth power | A bare plaquette expectation is not a prescription-independent continuum gluon condensate |
| S9 | Lüscher, [Properties and uses of the Wilson flow in lattice QCD](https://arxiv.org/abs/1006.4518), JHEP 08 (2010), 071; abstract and publication record | Flowed gauge-invariant observables and a controlled route to topology and scale setting | Flow time and continuum limits must be specified; smoothing does not itself establish a gap |
| S10 | Andrews–Clutterbuck, [Proof of the fundamental gap conjecture](https://arxiv.org/abs/1006.1686); abstract | Quantitative ground-eigenfunction geometry can control a spectral gap for suitable Schrödinger operators | Convex-domain/potential assumptions are not established for the Yang–Mills configuration space |
| S11 | [Clay's current Yang–Mills problem page](https://www.claymath.org/millennium/yang-mills-the-maths-gap/), read 2026-09-08 | The official problem is still listed as unsolved | Status source only; not an assessment of every claimed solution |
| S12 | Douglas, [The Yang–Mills Millennium problem](https://www.nature.com/articles/s42254-025-00909-2), Nature Reviews Physics 8 (2026), 86–97; [publisher listing](https://www.nature.com/natrevphys/articles?type=review-article&year=2026) and abstract | Review exists, published 12 January 2026; surveys the problem | Secondary context only. Full body was not accessible reliably; the preceding thread's stronger wording about no clear route is not imported as an exact statement |
| S13 | Morningstar–Peardon, [The glueball spectrum from an anisotropic lattice study](https://arxiv.org/abs/hep-lat/9901004), PRD 60 (1999), 034509; abstract | Operator-based glueball spectroscopy with finite-volume/discretization checks | One measured channel or finite operator basis does not certify the full Hilbert-space gap |

Search angles: official existence/gap formulation; reconstruction and
clustering; gauge invariance; 2+1 and 3+1 vacuum-functionals; glueball and
topology calculations; condensate subtraction; ground-state geometry and
gap bounds. The search did not identify a theorem making a generic
nonzero gauge-invariant VEV sufficient for the four-dimensional gap.
This records the search boundary, not a proof that no such theorem exists.

## Exact propositions and the assumptions they need

### 1. Centering removes the vacuum, not arbitrarily low positive energy

Let H be self-adjoint, H >= 0, with a unique normalized ground state
Omega and H Omega = 0. Let O be bounded, or suitably smeared with
O Omega in the required domain. Define

\[
v_O=(O-\langle O\rangle I)\Omega,\qquad
\mu_O(B)=\langle v_O,P_H(B)v_O\rangle.
\]

The spectral theorem gives

\[
C_O(t)=\langle v_O,e^{-tH}v_O\rangle
=\int_{(0,\infty)}e^{-tE}\,d\mu_O(E).
\]

If the vacuum is degenerate, subtracting one expectation need not remove
the whole zero-energy subspace: replace v by (I-P0)O Omega. Local fields
at a point are distributions, so unsmeared products need separate care.

For a nonzero finite measure, its long-time exponential rate is the
infimum of its support. A single channel can miss the lightest state.
No inference from the scalar mean to this support follows from centering.
For example, replacing O by O+cI changes its mean but leaves v_O and
the entire connected correlation unchanged. This is an observable
redefinition control, not a physical deformation of the vacuum.

S1 separately specifies H Omega = 0 and the spectral exclusion interval.
Its clustering statement additionally uses relativistic locality.
S3 supplies a corresponding result in its own lattice setting.

### 2. A complete temporal decay bound really would constrain the gap

If there is one delta > 0 such that, for every v in a dense subset of
Omega-perpendicular,

\[
\langle v,e^{-tH}v\rangle\leq K_v e^{-\delta t}
\quad\text{for all sufficiently large }t,
\]

then P_H((0,delta)) = 0. To see this, any nonzero spectral weight at
energies at most b < delta supplies a lower bound proportional to
exp(-bt), contradicting the asserted decay. Density then removes the
whole low-energy spectral projection. The exponent must be common;
separate positive exponents that approach zero do not suffice.

This is a spectral-theorem argument, not a result of fitting a finite
time window. A complete set of Euclidean correlations satisfying the
reconstruction axioms contains the dynamics (S2); a few equal-time
moments do not provide that data.

### 3. A useful bridge: the vacuum measure and its kinetic form

Here is a finite-regulator derivation, restricted to theta = 0. Work on
a finite product of compact link groups, with Haar measure dU, a real
smooth gauge-invariant potential V, and

\[
H=-\kappa\sum_{\ell,a}X_{\ell a}^2+V,\qquad\kappa>0.
\]

Normalize the invariant derivatives X so that their Casimir convention
is fixed. Assume a unique smooth, strictly positive, gauge-invariant
ground function psi0. Work in the gauge-invariant Hilbert space. Set
dnu = psi0 squared dU and use smooth gauge-invariant f in a form core.
Integration by parts and H psi0 = E0 psi0 give

\[
\langle f\psi_0,(H-E_0)f\psi_0\rangle
=\kappa\int\sum_{\ell,a}|X_{\ell a}f|^2\,d\nu
\equiv\mathcal E_\nu(f,f).
\]

Orthogonality to psi0 becomes integral f dnu = 0. Therefore

\[
\Delta=\inf_{\operatorname{Var}_\nu(f)>0}
\frac{\mathcal E_\nu(f,f)}{\operatorname{Var}_\nu(f)}.
\]

In particular,

\[
\operatorname{Var}_\nu(f)\leq C\,\mathcal E_\nu(f,f)
\quad\hbox{for every physical }f
\quad\Longrightarrow\quad\Delta\geq C^{-1}.
\]

The optimal C is the inverse gap. Naming that constant only reformulates
the problem. Research progress would require bounding it from simpler
vacuum information without inserting the desired gap as an assumption.

One elementary sufficient comparison condition makes this concrete. Let
nu_ref have Poincaré constant C_ref for the same gradient norm, and let

\[
0<a\leq d\nu/d\nu_{\rm ref}\leq b<\infty.
\]

Using variance = infimum over constants c of integral |f-c| squared,

\[
\operatorname{Var}_\nu(f)
\leq b\operatorname{Var}_{\nu_{\rm ref}}(f)
\leq\frac{bC_{\rm ref}}{a\kappa}\mathcal E_\nu(f,f),
\qquad
\Delta\geq\frac{a\kappa}{bC_{\rm ref}}.
\]

This is a self-contained bounded-density comparison, not a claim that
Yang–Mills satisfies useful uniform a/b bounds. Those ratios can
deteriorate severely with volume. S10 is a separate concrete example
of ground-state geometry controlling gaps under strong additional
assumptions; its theorem is not applied here.

The kinetic specification is essential. Changing the generator can
preserve the entire ground state while changing its gap. Conversely,
for a known Laplace-type kinetic term and a positive exact psi0,
V = E0 + kappa times (sum X squared psi0)/psi0 determines the potential
up to an additive constant. The information hierarchy in the preceding
thread is therefore conditional on what dynamics are already supplied.
At nonzero theta, phases and changed domains can invalidate this
positive-measure derivation. A finite representation truncation also
needs its own form identity; positivity cannot simply be presumed.

### 4. What the proposed diagnostics actually measure

| Diagnostic | Interpretation | Experimental qualification |
|---|---|---|
| A local VEV | One moment of a state for a defined operator | Normalization, identity mixing and subtraction convention matter |
| Equal-time spatial loops and covariances | Information about a time-slice state | Related observables may share the same information; do not count each as an independent test |
| A fitted wavefunctional kernel | Compressed description on a selected configuration family | Ansatz and coverage must be stated (S5–S6) |
| Topological susceptibility chi_t | Curvature of vacuum energy density with respect to theta; equivalently a spacetime-integrated topological correlation with its proper definition | It already contains dynamical information; contact terms and topological sampling matter |
| String tension from long temporal Wilson loops | Energy of external-source configurations | It is not a purely equal-time vacuum coordinate |
| A channel decay mass m_O | Lowest energy with nonzero O-vacuum overlap | m_O >= Delta; equality requires overlap with the lowest excitation |
| A Rayleigh quotient from f psi0 | Excitation-energy trial estimate above an exact vacuum | It bounds Delta from above, not below |

Near theta = 0, for a consistently normalized vacuum **energy density**,
e(theta)-e(0) = chi_t theta squared / 2 + higher terms. Here chi_t =
lim Var(Q)/four-volume. A one-plaquette quantum-mechanical model has
neither that four-volume limit nor the operator content needed for the
proposed four-dimensional susceptibility. No theta-dependent constant
may be arbitrarily subtracted when taking this derivative.

S7 treats spectrum, tension and topology as separately measured
quantities. This supports the diagnostic distinction without establishing
independence. S8 explains the condensate-subtraction issue; it does not
make ordinary finite-regulator plaquette moments unusable. S9 offers
flowed alternatives, with the flow prescription retained as part of
the observable.

## Finite size, continuum units and the previous pilot

An additive shift H -> H+cI changes an operator floor but leaves all
energy differences unchanged. An antiperiodic scalar-circle Laplacian
has lowest value 1/4 and a degenerate ground eigenspace; that positive
floor is not its excitation gap. Its next distinct eigenvalue is 9/4,
so the gap above the whole ground space is 2 in those units.

For a continuum limit, a positive physical mass generally means the
dimensionless lattice quantity a times m tends to zero. Thus a falling
lattice gap need not signal a vanishing physical mass. Track spacing,
physical volume, cutoff convergence, and an independently defined
reference scale. Dividing both axes by string tension can create shared
denominator correlations or become undefined in a nonconfining mutant.
Record raw quantities and joint uncertainties as well as ratios.

The recovered `ym-gap-pilot-artifacts.zip` contains the script and JSON
for the one-plaquette character/angle comparison. Its JSON labels the
run exploratory, not preregistered. At g = 0.10 it records SU(2)
3.987467769364457 and U(1) 3.989974834437078, and rejects specificity of
that weak-coupling gap to non-Abelian dynamics. These are prior readings,
not new results. The ZIP's README names two notes absent from the ZIP;
their contents are not reconstructed or treated as available evidence.
The handoff records the exact source hashes.

## Exclusions and next action

- No inference from a nonzero condensate, susceptibility or classical
  winding label to a four-dimensional mass gap.
- No identification of confinement with the mass-gap property.
- No treatment of a changed Monte Carlo update algorithm or frozen
  topological sampling as a physical change of Hamiltonian.
- No claim that independent correlator analysis produces statistically
  independent measurements when it reuses the same states or samples.
- No proof of a uniform lower bound from a finite operator-basis minimum,
  a finite-matrix energy difference, or a successful exponential fit.
- No topology-based mechanism or current claimed solution has been
  assessed exhaustively. S11 supplies the current official status;
  this draft makes no novelty claim.

The immediately specified next step is the finite-model two-axis
instrument study in the companion draft. It tests means, centering,
overlaps and gap extraction with controls that can fail. A subsequent
connected-lattice study must specify its physical Hamiltonian and
scaling path before it acquires continuum or mechanism language.
