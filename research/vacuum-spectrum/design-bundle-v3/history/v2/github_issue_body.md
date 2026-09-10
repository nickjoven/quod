<!-- ym-vacuum-gap-litcheck:v2:2026-09-09 -->
Archive of the Yang–Mills vacuum/spectrum documents, artifact **v2**, revised **2026-09-09**, with literature reviewed through **2026-09-08**.

This version adds the 2026 glueball developments: the BESIII X(2370) composition claim and September criticism, scalar-glueball form factors, exploratory scalar mixing, and a quasi-one-dimensional SU(3) continuum benchmark. The existing experiment remains an unregistered design with target cells unrun.

These documents originated in `nickjoven/proslambenomenos`; this issue stores a discussion copy in `nickjoven/quod`. It does not register predictions or report a Yang–Mills mass-gap proof.

The complete documents are included below. Companion links and display-math delimiters are adapted for GitHub rendering; the document text is otherwise retained.

- [Literature check](#litcheck-document)
- [Experiment design](#registration-document)
- [Handoff and provenance](#handoff-document)


## LITCHECK document

<details>
<summary>ym_vacuum_gap_litcheck.md — expand full document</summary>

<!-- commentary -->
# Yang–Mills vacuum structure and spectral gap — LITCHECK draft v2

Artifact version: **2**, revised 2026-09-09; first issued 2026-09-08.
Literature cut-off for this revision: 2026-09-08.
Task: `ym-vacuum-gap-litcheck`.
Repository: `nickjoven/proslambenomenos`.
Base inspected: `da0084147986a97f355954be6b0eff4246b9d852`.

This is a literature synthesis and a proposed mathematical formulation, not
a claim-status entry. No LC, P, R, or LAW number has been allocated. The
companion [experiment draft](#registration-document) has not
been registered or run. Source classifications below concern the cited
literature; they do not change any repository claim.

Revision 2 adds sources S14–S18 and a dated glueball update: the BESIII
identification claim and its direct criticism, scalar structure and
mixing calculations, and an SU(3) plaquette-chain continuum benchmark.
The conditional mathematical propositions remain those of version 1.
The companion design adds a follow-on benchmark note; no target cells,
numerical tolerances, or execution status change in this revision.

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
| S14 | BESIII, [Lightest 0−+ Glueball as Dominant Constituent of X(2370)](https://arxiv.org/abs/2607.20366), submitted 22 July 2026; abstract and main HTML text | Combined production/decay evidence for the collaboration's composition claim | Preprint; composition inference is distinct from resonance measurements |
| S15 | Ben–Yang–Zou, [On the Nature of X(2370)](https://arxiv.org/html/2609.01342v1), 1 September 2026; abstract and argument on suppressed decay | Direct challenge to S14 and a competing molecular interpretation | Preprint; the proposed alternative is not an established identification |
| S16 | Abbott et al., [Lattice Evidence that Scalar Glueballs Are Small](https://doi.org/10.1103/67xg-qxhz), PRL 136 (2026), 041901, published 26 January; published abstract and [preprint main text](https://arxiv.org/html/2508.21821v1) | Scalar-glueball gravitational form factors in pure SU(3) | One lattice spacing; the radius is a defined form-factor quantity |
| S17 | Gui et al., [Scalar glueball–s-sbar mixing in one flavor lattice QCD](https://arxiv.org/abs/2607.17294), submitted 19 July 2026; abstract | Exploratory scalar mixing calculation | One dynamical flavor and one spacing; continuum and quark-mass dependence remain open |
| S18 | Siew–Chandrasekharan–Bhattacharya, [Continuum limit of a qubit-regularized SU(3) lattice gauge theory with glueballs](https://arxiv.org/abs/2603.01215), submitted 1 March 2026; main HTML text | A massive continuum benchmark on a plaquette chain | Quasi-one-dimensional, with a different critical theory from four-dimensional Yang–Mills |

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

$$
v_O=(O-\langle O\rangle I)\Omega,\qquad
\mu_O(B)=\langle v_O,P_H(B)v_O\rangle.
$$

The spectral theorem gives

$$
C_O(t)=\langle v_O,e^{-tH}v_O\rangle
=\int_{(0,\infty)}e^{-tE}\,d\mu_O(E).
$$

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

$$
\langle v,e^{-tH}v\rangle\leq K_v e^{-\delta t}
\quad\text{for all sufficiently large }t,
$$

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

$$
H=-\kappa\sum_{\ell,a}X_{\ell a}^2+V,\qquad\kappa>0.
$$

Normalize the invariant derivatives X so that their Casimir convention
is fixed. Assume a unique smooth, strictly positive, gauge-invariant
ground function psi0. Work in the gauge-invariant Hilbert space. Set
dnu = psi0 squared dU and use smooth gauge-invariant f in a form core.
Integration by parts and H psi0 = E0 psi0 give

$$
\langle f\psi_0,(H-E_0)f\psi_0\rangle
=\kappa\int\sum_{\ell,a}|X_{\ell a}f|^2\,d\nu
\equiv\mathcal E_\nu(f,f).
$$

Orthogonality to psi0 becomes integral f dnu = 0. Therefore

$$
\Delta=\inf_{\operatorname{Var}_\nu(f)>0}
\frac{\mathcal E_\nu(f,f)}{\operatorname{Var}_\nu(f)}.
$$

In particular,

$$
\operatorname{Var}_\nu(f)\leq C\,\mathcal E_\nu(f,f)
\quad\hbox{for every physical }f
\quad\Longrightarrow\quad\Delta\geq C^{-1}.
$$

The optimal C is the inverse gap. Naming that constant only reformulates
the problem. Research progress would require bounding it from simpler
vacuum information without inserting the desired gap as an assumption.

One elementary sufficient comparison condition makes this concrete. Let
nu_ref have Poincaré constant C_ref for the same gradient norm, and let

$$
0<a\leq d\nu/d\nu_{\rm ref}\leq b<\infty.
$$

Using variance = infimum over constants c of integral |f-c| squared,

$$
\operatorname{Var}_\nu(f)
\leq b\operatorname{Var}_{\nu_{\rm ref}}(f)
\leq\frac{bC_{\rm ref}}{a\kappa}\mathcal E_\nu(f,f),
\qquad
\Delta\geq\frac{a\kappa}{bC_{\rm ref}}.
$$

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

## 2026 glueball update

The following are cited results and research implications, not new
calculations performed for this artifact. Publication and access status
are recorded in S14–S18. A headline describing a discovery is not used as
a substitute for the underlying measurement or inference.

### X(2370): separate the measurement from the composition argument

S14 combines approximately ten billion J/psi events with the established
pseudoscalar quantum numbers, a mass near 2.37 GeV, production information
and decay patterns. A central new input is the absence of a significant
K*(892)-Kbar signal in the selected decay channel. The authors infer
flavor-singlet character and argue for a dominant glueball component.
The resonance's observation predates this 2026 composition claim.

S15 disputes the inference and proposes a predominantly Sigma–anti-Sigma
molecule. In particular, a symmetry forbidding a decay does not establish
that every state with a suppressed decay has that symmetry. Nor does
flavor-singlet character by itself uniquely specify gluonic composition.
The competing model is also an interpretation requiring further tests.

The working literature classification is therefore **a substantial
experimental identification claim with disputed composition**, rather
than an agreed determination of a pure glueball. Keep measured channels,
upper limits and quantum numbers separate from model interpretation.
This is the same logical discipline as the predicate D discussion:
compatibility with a predicted consequence is not a sufficiency theorem.

Even an eventual definitive identification would concern a resonance in
QCD with dynamical quarks. It would not construct pure Yang–Mills or
exclude all lower-energy physical spectral support. The pseudoscalar
0−+ channel must also remain separate from the scalar 0++ channel (S1,
S13). A resonance peak is not automatically the lower endpoint of a
positive spectral measure; lighter multiparticle states can contribute.

### Scalar structure: information beyond a mass

S16 reports a first scalar-glueball gravitational-form-factor calculation
in pure SU(3), with mass radius 0.263(31) fm. It uses one lattice spacing;
the quoted error does not replace a continuum extrapolation. These form
factors parameterize matrix elements of the energy–momentum tensor
between glueball states, schematically <G(p')|T_mu_nu|G(p)>. They are
obtained using vacuum-subtracted two- and three-point correlations.
The terminology does not mean dynamical gravity or curvature supplied
the mass. The radius definition and scale-setting convention must travel
with the number.

Our classification places this on the excitation-structure side. It
describes the identified state, not a one-point vacuum expectation.
It suggests a later discrimination test for mechanisms that reproduce
similar masses but predict different internal structure. That suggestion
is a research-design inference, not a gap bound or a task to implement
form factors in the current one-plaquette instrument.

### Mixing: the pure-gauge-to-QCD comparison has extra obligations

S17 finds substantial scalar glueball–strangeonium mixing, approximately
40.7(2.7) degrees in its two-state analysis. This is a one-flavor,
single-spacing lattice study. It is not a quantitative determination of
the composition of physical scalar resonances with all relevant quark
flavors and decay channels. The authors leave continuum and quark-mass
dependence for further investigation.

For a later full-QCD comparison, our inference is to retain the operator
basis, normalization conventions, cross-correlators and overlaps, rather
than match one mass to a pure-gauge prediction. Mixing angles depend on
the stated analysis and should not be relabeled universal percentages
of constituent glue. Adding quark operators is appropriate to that
different theory; it is not required in the current pure-gauge pilot.

### A plaquette-chain continuum benchmark

S18 maps an SU(3) plaquette chain to a three-state clock model. Its
massive continuum theory is a relevant perturbation of the Z3
parafermion critical theory. Reported continuum ratios are

$$
m^-/m^+=1.459(2),\qquad \sqrt{\sigma}/m^+=0.2648(2),
$$

where the signs denote charge conjugation. The study includes scaling
and relativistic-dispersion checks. These are published-in-preprint
benchmark readings, not measurements by this project. The model is
quasi-one-dimensional: its critical theory and relevant deformation
must not be equated with four-dimensional Yang–Mills running or its
dimensional-transmutation mechanism.

Our proposed follow-on use is instrument validation on a connected
family with explicit scaling, after the current calibration. Known
ratios would be development/replication targets, never held-out
predictions. The companion design records the remaining choices before
any such benchmark could be registered.

### What this revision changes in the research direction

| Input | Use in this project | Inference excluded |
|---|---|---|
| X(2370) production and decay studies | Update the evidence map and track competing explanations | A resonance establishes the full pure-Yang–Mills gap |
| Glueball form factors | Consider internal structure when comparing mechanisms in a later model | A measured radius or a tensor matrix element alone supplies a uniform lower bound |
| Scalar mixing calculation | Require explicit composition and operator-coverage analysis for full-QCD comparisons | A mixing angle in an exploratory model identifies a physical resonance |
| Plaquette-chain continuum study | Candidate benchmark for scaling, channel separation and extraction methods | A continuum limit in one theory establishes the desired four-dimensional universality class |

The constructive target remains a quantitative bound derived from a
specified vacuum property and kinetic form, with control of the full
physical domain and regulator limits. None of these imports completes
that target. They improve the evidence map and the available calibration
models without converting a conditional proposition into a Yang–Mills
existence or mass-gap result.

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

</details>


## Registration document

<details>
<summary>ym_vacuum_gap_registration_draft.md — expand full document</summary>

<!-- commentary -->
# Vacuum–spectrum two-axis study — registration draft v2

Artifact version: **2**, revised 2026-09-09; first issued 2026-09-08.
Task: `ym-vacuum-gap-litcheck`.
State: **unregistered design; target cells unrun**. No P or LC ID assigned.
This note specifies the next finite-model instrument study. It does not
register a prediction, assert a repo status, or promise a continuum result.
Its source context is [the LITCHECK draft](#litcheck-document).

## Scope and proposed question

For the one-plaquette SU(2) model already implemented, which vacuum
moments and centered operators actually see the lowest excitation, and
which apparent connections disappear under derived nulls?

This is a calibration and diagnostic study. The exact identities below
are checks, not discoveries. The previously run pilot cells remain
replication data. No claim that a finite list of moments suffices for
a Yang–Mills gap is registered here.

The physical hypothesis a later mechanism study would need is of the form

$$
D(\nu_r,K_r)\Longrightarrow \Delta_r/s_r\geq\delta_*>0
\quad\text{for every regulator }r\text{ on a specified trajectory}.
$$

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

$$
H(g,\eta)=4g^2 C_2-\frac{2\eta}{g^2}P,
\qquad C_2\chi_j=j(j+1)\chi_j.
$$

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

$$
V=(\langle P\rangle,\langle P^2\rangle,
\operatorname{Var}(P),\operatorname{Var}(P^2),
\operatorname{Cov}(P,P^2)).
$$

This vector contains a known redundancy: Var(P) = mean(P squared) minus
mean(P) squared. Record the identity as a check, not an extra feature.
The corresponding spectral outputs are

$$
S=(\Delta_{10},\Delta_{20},m_P,m_{P^2},
 |\langle1|\widetilde P|0\rangle|^2,
 |\langle1|\widetilde{P^2}|0\rangle|^2).
$$

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

$$
\langle P\rangle=0,\quad\langle P^2\rangle=\tfrac14,
\quad C_P(t)=\tfrac14e^{-3g^2t},\quad
C_{P^2}(t)=\tfrac1{16}e^{-8g^2t}.
$$

Thus the two channels see 3g squared and 8g squared respectively, with
the same vacuum. The tensor-sum row is a non-Yang–Mills premise control;
its eps -> 0 limit acquires degeneracy. It demonstrates absence of a
uniform gap over that family, not a gapless pure Yang–Mills vacuum.

For the gapless row and a time step h > 0,

$$
m_{\rm eff}(t;h)=\frac1h\log\frac{1+t+h}{1+t}>0,
\qquad \lim_{t\to\infty}m_{\rm eff}=0.
$$

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

$$
H_\phi=-g^2\partial_x^2-g^2-2\eta g^{-2}\cos x,
\qquad\phi(0)=\phi(\pi)=0.
$$

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

$$
C(t)=w_1e^{-m_1t}(1+r(t)),\quad
0\leq r(t)\leq\frac{W_{\rm tail}}{w_1}e^{-(m_2-m_1)t}.
$$

Hence the finite-step logarithmic slope lies above m1, with bias bounded by

$$
0\leq m_{\rm eff}(t;h)-m_1
\leq h^{-1}\log(1+r(t)).
$$

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

## Version 2 follow-on benchmark note

The [LITCHECK v2](#litcheck-document) adds five sources on 2026
glueball developments. Its SU(3) plaquette-chain source, S18, is a
candidate follow-on benchmark because it supplies a connected model and
a specified continuum scaling target. This is a recommendation for a
later design; the cells, controls, tolerances and unrun status above are
unchanged. Literature ratios are replication inputs, not fresh predictions.

Before making that benchmark executable, specify the exact link
Hamiltonian and representation content, physical sectors, mapping to
the comparison model, and the chosen critical trajectory. Then freeze
the chain lengths, numerical refinement and uncertainty budgets,
space/time conversion, operator selection identities, and treatment of
finite-volume and multiparticle contamination. Derive the detector nulls
and window bounds for that model; do not reuse this rotor's bounds by
analogy. Consult the lessons tool again for those concrete choices.

Any success would calibrate an instrument within the selected theory.
It would not establish four-dimensional universality or a uniform
Yang–Mills lower bound. The new structure and mixing papers belong in
later model-comparison designs. The experimental X(2370) composition
claim supplies no target value for this one-plaquette Hamiltonian.

## Before this draft becomes a registration

Allocate the P/LC identifiers through the repository assignment process;
implement and archive the derive code and its null responses; freeze
source/code hashes, all numerical error formulas, manifest, and result
schema; commit the registration before executing target cells. An
integrator can then use the existing serial PR and gate workflow.
These are outstanding execution prerequisites, not a request to approve
an unwritten experiment. This task delivers the complete design draft.

</details>


## Handoff document

<details>
<summary>ym_vacuum_gap_handoff.md — expand full document</summary>

<!-- commentary -->
# Vacuum–spectrum LITCHECK handoff v2

Artifact version: **2**, revised 2026-09-09; first issued 2026-09-08.
Task: `ym-vacuum-gap-litcheck`.
Repository: `nickjoven/proslambenomenos`.
Base: `da0084147986a97f355954be6b0eff4246b9d852`.
Owned worktree branch: `ym-vacuum-gap-litcheck`.

## Deliverables

Version 2 adds five primary sources and the 2026 glueball update to the
LITCHECK. The registration draft adds a follow-on benchmark note. The
existing mathematical derivations, numerical cells and target status
are preserved. Literature reviewed through 2026-09-08 is incorporated;
this revision does not purport to audit later publications.

- [LITCHECK draft](#litcheck-document): primary-source table,
  exact conditional propositions, corrected necessity/sufficiency
  logic, vacuum-measure/kinetic-form bridge, exclusions.
- [Registration draft](#registration-document): explicit
  finite SU(2)/U(1) models, development and target cells, derived nulls,
  operator coverage, numerical refinement, temporal-window budgets,
  decision rules and requirements for a later connected-lattice study.

The source results are cited literature; the formulas in the design are
displayed derivations or analytic controls. No scientific target cells
were executed. The study has no allocated ledger number and has not
been preregistered. The terms theorem and bound refer to their stated
mathematical assumptions, not to any computed repository status.

## Prior-pilot provenance

The recovered archive is `ym-gap-pilot-artifacts.zip`.

| Item | SHA-256 |
|---|---|
| Prior archive | `064976b9954a6d2c83c9dc24a94a3cfda64f3673fafc3d9f2976a5198b35c0a4` |
| Archived `scripts/experiments/ym_gap_pilot.py` | `9f5cd7cda74cb5623c8e20b07b34671f7cd52eb3ff9a89721571ffe356fe238a` |
| Archived `scripts/experiments/ym_gap_pilot_results.json` | `0e1a529828409cddf4ab3c1a78c5b0ccd82450e7c329c86bd93a8d88ff1b6025` |

The archive README lists `notes/ym_gap_pilot.md` and
`notes/ym_gap_next_registration_skeleton.md`, but neither is in the ZIP.
The pilot script is also absent from the inspected repo base. The
available script and JSON, not the absent notes, ground this handoff.
Their prior numerical readings retain the exploratory qualification.

## Suggested ledger-entry text for assignment

The following is an unnumbered content draft, not an append to LITCHECKS.md:

> Vacuum-state diagnostics versus excitation thresholds (2026-09-08).
> Checked the official Yang–Mills definition, Euclidean reconstruction,
> connected clustering, vacuum-functionals, lattice spectra/topology,
> condensate subtraction and ground-state geometry. The vacuum/threshold
> distinction and the centered spectral representation are classical.
> Detailed state information with a specified kinetic form can control a
> gap through a Poincaré inequality; no uniform four-dimensional bound
> follows from this review. No generic nonzero-VEV sufficiency theorem was
> identified in the checked sources. The draft corrects sufficiency versus
> necessity, operator-coverage omissions and physical-unit normalization.
> Source table and assumptions: notes/ym_vacuum_gap_litcheck.md. Proposed
> instrument study: notes/ym_vacuum_gap_registration_draft.md. This is a
> synthesis and search record, with no novelty or claim-status change.

## Landing boundary

AGENTS.md requires assignment of ledger IDs and serial integrator landing.
Accordingly these are namespaced commentary notes. No append-only ledger,
claim YAML, gate-covered script, catalog, public page or existing result
was edited. There is no unresolved mathematical claim being promoted.
The integrator should rebase onto current main, allocate an ID if a
ledger append is desired, run the existing gates and use the normal PR
process. Target execution still waits for a real registration and its
implemented derive layer.

## Checks and delivery

For version 1, the notes gate and commit-message gate passed. Local Markdown
links, display-math delimiters, code fences and whitespace were checked.
The tensor-sum null's eigenvectors were checked in exact rational
arithmetic; SU(2) Haar moments were checked with Gauss–Chebyshev U
quadrature, exact for these polynomial degrees up to roundoff. These
checks concern the document and analytic controls, not target results.
The full repository gate suite was not run for this commentary-only
handoff; it remains part of integrator landing.

The version-1 source work had a local commit, but no remote branch was
created. The shell push lacked GitHub credentials; authenticated branch
creation separately returned HTTP 403. The version-2 bundle retains the
source repository and base above as provenance and includes a patch
against that base. Its manifest distinguishes current document checks
from the analytic checks inherited from version 1. No numerical targets
were executed for version 2.

The user requested an issue in `nickjoven/quod` as a document archive.
That issue destination is separate from the source/design repository.
The prepared issue text contains the documents themselves; it does not
depend on temporary file links. The bundle records the posting outcome
separately in `github_delivery.json`.

</details>
