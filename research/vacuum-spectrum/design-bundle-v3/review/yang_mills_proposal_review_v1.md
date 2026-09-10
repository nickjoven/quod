# Review of the informational and geometric Yang–Mills proposal

**Review version:** 1  
**Reviewed:** 9 September 2026  
**Document:** *An Informational and Geometric Architecture for the Yang–Mills Mass Gap Problem*, September 2026, two pages, supplied as yang_mills_proposal.pdf.  
**Disposition:** Concept note requiring substantial mathematical revision. No existence theorem, physical mass-gap theorem, or Lean proof is supplied.

## Assessment

The proposal identifies real subjects—causal geometry, gauge constraints, BRST cohomology, entanglement, and formal verification—but its central implications do not follow from those subjects. Several fail as general mathematical statements.

The most consequential error is identifying a positive minimum eigenvalue of an entanglement Hamiltonian with a gap in the physical Hamiltonian. An elementary construction below gives exactly the same vacuum, reduced density matrix, entropy, and entanglement spectrum to a gapped Hamiltonian and a gapless Hamiltonian. This rules out an unrestricted implication from those vacuum data to a physical gap when the generator is not specified.

That construction is not a local relativistic Yang–Mills model. It therefore does not disprove the Yang–Mills conjecture or a future theorem with additional Yang–Mills hypotheses. It identifies a bridge theorem that the proposal needs and currently does not state.

The PDF contains no bibliography, numbered references, explicit field construction, definition of its proposed infrared map, choice of subsystem for entanglement, or Lean source. This review checks the named mechanisms against external primary sources and official documentation. It does not authenticate a missing proof.

## Claim-by-claim findings

| Location and claim | Finding | Disposition |
|---|---|---|
| Abstract: a positive gap emerges from geometric restriction of degrees of freedom | No derivation or precise restriction is supplied. Causal and gauge constraints can coexist with gapless excitations. | General sufficiency claim fails; a specific new mechanism remains undefined. |
| Section 1: light-cone restrictions generate mass | Light cones constrain causal propagation. They do not determine the bottom of the energy spectrum. | Ruled out as a consequence of causality alone. |
| Section 1: asymptotic freedom avoids ultraviolet blow-ups | Small coupling does not make quantum fields regular pointwise functions. Even free fields have singular coincident-point correlations. | Claimed removal of ultraviolet singularities is false. |
| Section 1: Kugo–Ojima quartets implement infrared freezing and produce a gap | Quartet decoupling concerns unphysical states in BRST quantization. It is not itself a renormalization flow or a lower bound on physical singlet energies. | Attribution is unsupported; quartet removal alone is insufficient. |
| Section 2: infrared freezing is a dimensional transition function | Domain, codomain, action on observables, scale dependence, and preservation of dynamics are absent. | Not sufficiently defined to prove or falsify. |
| Section 2: the mass gap is a positive minimum eigenvalue of the vacuum entanglement Hamiltonian | This substitutes a different operator and a different spectral question for the physical mass gap. | Invalid identification; explicit counterexamples below. |
| Section 2: light cones are modeled by an inner product space | If this means mathlib's positive definite InnerProductSpace, its self-inner-product has no nonzero null vectors. A separate Lorentzian form can be added. | Conditional modeling error, readily repairable. |
| Section 3: compatibility with Wightman axioms establishes existence | A list of compatible abstract properties is not a construction of the required interacting Yang–Mills observables. | Missing existence argument. |
| Section 3: Lean checking guarantees protection from analytical errors | Lean checks formal consequences of definitions and assumptions. It does not independently establish that these describe Yang–Mills. No code was supplied. | Verification claim exceeds the evidence. |

## 1. The physical target and the entanglement substitution

With vacuum energy normalized to zero, the physical target concerns the generator of time translations:

$$
H_{\mathrm{phys}}\Omega=0,\qquad
\operatorname{spec}(H_{\mathrm{phys}})\cap(0,\delta)=\varnothing
\quad\text{for some }\delta>0.
$$

The zero-energy vacuum is retained. A positive *minimum eigenvalue of the whole Hamiltonian* is not the target. In infinite volume, the lower edge of nonvacuum spectral support need not be an eigenvalue. The official problem also requires construction of nontrivial Yang–Mills theory for every compact simple gauge group. [Jaffe–Witten, §4](https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf)

For a normalized reduced density matrix in a specified finite-dimensional factorization, the entanglement Hamiltonian is

$$
K_A=-\log\rho_A.
$$

Its eigenvalues are logarithms of probabilities, hence dimensionless. They generate modular evolution, which generally differs from physical time evolution. Entanglement spectra can be informative, but their interpretation requires the model and partition. [Li–Haldane](https://arxiv.org/abs/0805.0332)

For every mixed, finite-dimensional density matrix,

$$
\min\operatorname{spec}(K_A)
=-\log\lambda_{\max}(\rho_A)>0,
$$

where the logarithm is taken on the support if necessary. This follows from normalization and mixedness. It contains no reference to the physical generator. Nor is this positive minimum the same as a difference between entanglement levels.

A canonical field-theory example makes the distinction concrete: vacuum modular flow for a Rindler wedge is related to Lorentz boosts, rather than ordinary Minkowski time translations. Null-plane modular Hamiltonians are already an established research subject; their existence is not a mass-gap theorem. [Casini–Teste–Torroba, introduction and §2](https://arxiv.org/pdf/1703.10656)

### An exact counterexample with fixed vacuum and fixed energy normalization

On two qubits, define orthonormal vectors

$$
\Omega=\frac{2|00\rangle+|11\rangle}{\sqrt5},
\qquad
\chi=\frac{|00\rangle-2|11\rangle}{\sqrt5}.
$$

For \(0<\varepsilon\le1\), set

$$
H_\varepsilon=
\varepsilon|\chi\rangle\langle\chi|
+|01\rangle\langle01|
+|10\rangle\langle10|.
$$

The spectrum is \(0,\varepsilon,1,1\). The vacuum is uniquely \(\Omega\), and the operator norm is always one. Thus the change is not an overall rescaling of energy units.

For every member of this family,

$$
\rho_A=
\begin{pmatrix}
4/5&0\\0&1/5
\end{pmatrix},
\qquad
\operatorname{spec}(K_A)=\{\log(5/4),\log5\}.
$$

Consequently,

$$
\min\operatorname{spec}(K_A)=\log(5/4),\qquad
\text{entanglement-level gap}=\log4,
\qquad
\Delta_{\mathrm{phys}}=\varepsilon.
$$

The full vacuum and its entropy stay fixed as the physical gap tends to zero. This excludes any strictly positive uniform bound derived solely from those fixed vacuum data, even with the energy norm held fixed.

**Scope:** Every finite member is still gapped. This family alone is not an example of a single gapless system.

### A single gapless system with the same entanglement data

For the stronger statement, use the fixed Hilbert space
\(\mathcal H=\mathbb C^2\otimes\ell^2(\mathbb N_0)\), retain the same \(\Omega\), and choose an orthonormal basis \(\{e_n:n\ge1\}\) of \(\Omega^\perp\). Define

$$
H_{\mathrm g}=I-|\Omega\rangle\langle\Omega|,
$$

and define a second bounded operator by

$$
H_{\mathrm z}\Omega=0,\qquad
H_{\mathrm z}e_n=\frac1n e_n.
$$

Both operators are positive, self-adjoint, have norm one, and have precisely the same unique zero-energy vacuum. However,

$$
\operatorname{spec}(H_{\mathrm g})=\{0,1\},
\qquad
\operatorname{spec}(H_{\mathrm z})=\{0\}\cup\{1/n:n\ge1\}.
$$

Hence \(\Delta_{\mathrm g}=1\) and \(\Delta_{\mathrm z}=0\), while \(\rho_A\), \(K_A\), its positive minimum, its level spacing, and the entanglement entropy are identical.

This is an elementary spectral construction, not a proposed Yang–Mills theory and not a novelty claim. It disproves the unrestricted bridge. Additional dynamical restrictions could exclude this example; the proposal must state and use them. Here the fixed data are the state and equal-time observables in a fixed factorization. Time-separated correlation functions change with the Hamiltonian; this construction does not contradict reconstruction from sufficiently complete spacetime correlation data.

## 2. Causal geometry and removal of unphysical states

Free Maxwell theory in \(3+1\) dimensions has causal propagation and a physical state space with unphysical polarizations removed. Its transverse photons still satisfy

$$
E(\mathbf p)=|\mathbf p|,
$$

so arbitrarily small nonzero energies remain. An explicit modern BRST construction applies the Kugo–Ojima analysis to this massless theory and obtains the physical transverse subspace. [Dudal et al., §III](https://arxiv.org/html/2304.01028v2)

This is a counterexample to the sufficiency of causality plus quartet removal. Maxwell's Abelian gauge group is outside the compact-simple non-Abelian Clay target, so it does not settle that target.

The geometrical point can also be checked directly. The Klein–Gordon equations

$$
(\Box+m^2)\phi=0
$$

have the same principal symbol \(\eta^{\mu\nu}k_\mu k_\nu\) for every \(m\). Changing the mass does not change their characteristic cone. Thus that cone alone cannot select \(m>0\).

The PDF should distinguish:

- a characteristic surface used for initial data or propagation;
- null four-momentum of an elementary massless excitation;
- four-momentum of a composite excitation.

Even two future-directed null constituent momenta can have a timelike sum:
\(M^2=2E_1E_2(1-\cos\theta)\).
Consequently, neither “massless constituents forbid composite mass” nor “null geometry forces a positive gap” follows.

Kugo's own analysis treats BRST-exact charges, quartet representations, and an additional infrared condition for color confinement. It does not equate reducing gauge redundancy with progressively deleting physical low-energy states. Even a conclusion that physical particles are color singlets would require another argument to exclude arbitrarily low-energy singlet excitations. [Kugo, §§2 and 5](https://arxiv.org/pdf/hep-th/9511033)

## 3. Ultraviolet behavior, subsystems, and formalization

Asymptotic freedom concerns the high-energy behavior of a renormalized coupling and correlators. The original result is free-field asymptotics with logarithmic corrections, not pointwise regularity of quantum fields. [Gross–Wilczek](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.30.1343)

For an elementary check, a canonically normalized free massless scalar already has zero interaction coupling but has equal-time two-point function

$$
\langle\phi(0,\mathbf x)\phi(0,\mathbf 0)\rangle
=\frac1{4\pi^2|\mathbf x|^2}
\qquad(\mathbf x\ne0).
$$

Its coincident-point limit is singular. Accordingly, zero coupling does not eliminate the need for distributional fields and definitions of composite operators. The proposal provides no substitute construction.

There are also two distinct obstacles to using an entanglement “matrix”:

1. **Gauge constraints:** a physical gauge-theory Hilbert space need not factorize across spatial regions in the assumed way. One must specify an observable algebra, boundary treatment, or extended Hilbert space. [Casini–Huerta–Rosabal](https://arxiv.org/abs/1312.1183)
2. **Continuum local algebras:** under appropriate hypotheses, local observable algebras are type III and do not possess the intrinsic trace/density-matrix description assumed by elementary subsystem formulas. Fredenhagen establishes a relevant result for asymptotically scale-invariant theories. This is not asserted here as a consequence of every possible Wightman model without further assumptions. [Fredenhagen](https://link.springer.com/article/10.1007/BF01206179)

Algebraic modular theory can address continuum entanglement, but it introduces a different mathematical framework rather than validating the proposed finite matrix unchanged. If “vacuum's entanglement Hamiltonian” instead means the entire pure vacuum, its density operator is rank one: the logarithm is zero on its support and has no finite value on the orthogonal complement. The intended subsystem is indispensable.

For Lean, a spacetime Lorentzian quadratic or bilinear form must be distinguished from the positive definite inner product on the physical Hilbert space. In mathlib, positive definiteness implies \(\langle v,v\rangle=0\Rightarrow v=0\). A positive definite inner product can coexist with a separately defined Lorentzian form; the error would be using the former itself as the latter. [mathlib definitions](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Defs.html)

Lean verification is valuable once the mathematical statement is correct. It establishes a formal implication relative to its definitions and axioms. A complete assessment would need the actual theorem type, dependencies, source, toolchain, successful build, and an audit for unproved placeholders or custom assumptions importing the desired gap. Ordinary foundational axioms are not the same issue as assuming the physical conclusion. [Official Lean documentation](https://lean-lang.org/theorem_proving_in_lean4/Axioms-and-Computation/)

## 4. What this adds to the earlier investigation

| Candidate inference | What we can now say |
|---|---|
| Nonzero vacuum expectation value implies a gap | Insufficient in general. Shifting an observable by a constant changes its mean without changing the physical spectrum or its centered correlator. |
| Vacuum entanglement alone forces a gap | False when the generator can vary: the explicit pair above has identical vacuum data and different gap status. |
| Null-cone geometry or gauge-state removal forces a gap | False as a general statement; the massless Maxwell control survives both. |
| Asymptotic freedom removes ultraviolet singularities | False; free-field short-distance singularities already supply a counterexample. |
| Wightman axioms forbid a generated mass scale | Not established. Scale invariance is an additional condition, not one of those axioms. Classical Yang–Mills scale invariance must not be silently upgraded to exact quantum dilation symmetry. |
| A perturbative infrared divergence proves nonexistence | Invalid inference. Continuing a weak-coupling approximation outside its regime does not prove a failure of exact operators or Hilbert space. |
| Elitzur's theorem forces every gauge-invariant local expectation to vanish | Incorrect scope. The theorem addresses spontaneous breaking of local gauge symmetry without gauge fixing; it does not set invariant observables to zero. |
| Pure Yang–Mills needs an external Higgs or curvature “anchor” to have a gap | No such theorem follows from the arguments examined. |
| Every informational or geometric approach must fail | Not established. A more specific dynamical comparison theorem is still possible. |

For the scale discussion, a valid conditional observation is that exact unitary dilations satisfying
\(D(s)HD(s)^{-1}=e^{-s}H\), for all real \(s\), rescale the spectrum. If it contains any positive energy, it then contains positive energies arbitrarily close to zero. This excludes a positive gap under those extra hypotheses. It does not prove that dimensional transmutation violates Wightman axioms, and it does not apply automatically to a quantum theory with a running coupling. [Faddeev, discussion of dimensional transmutation](https://arxiv.org/abs/0911.1013)

The Elitzur correction follows from the distinction between invariant and non-invariant observables in the original theorem. [Elitzur](https://journals.aps.org/prd/abstract/10.1103/PhysRevD.12.3978)

None of the reviewed arguments establishes either existence or nonexistence of continuum four-dimensional pure Yang–Mills, or proves that its physical gap is positive or zero.

## 5. A useful revised research target

The proposal should first state a nontrivial dynamical inequality for a specified regulated physical Hamiltonian. With a unique normalized ground state and the relevant quadratic-form domain, a suitable target is

$$
\langle\psi,(H-E_0)\psi\rangle
\ge\delta\|\psi\|^2
\qquad(\psi\perp\Omega).
$$

This genuinely concerns the physical gap. Rewriting it in informational language is useful only if a simpler, independently established property supplies the lower bound. Defining the best constant by the gap itself would be circular as a proof strategy.

A finite-regulator route already compatible with our vacuum/spectrum distinction is the ground-state transform. Suppose on a compact connected configuration manifold

$$
H=-\kappa\Delta+V,\qquad \kappa>0,
$$

with the convention that \(-\Delta\ge0\), and a sufficiently regular strictly positive ground state \(\psi_0\). With \(d\nu=\psi_0^2\,dU\), integration by parts gives

$$
\langle f\psi_0,(H-E_0)f\psi_0\rangle
=\kappa\int|\nabla f|^2\,d\nu.
$$

A separately proved Poincaré inequality

$$
\operatorname{Var}_\nu(f)
\le C\int|\nabla f|^2\,d\nu
$$

then yields \(\Delta_{\mathrm{phys}}\ge\kappa/C\), provided it controls the whole physical form domain. This derivation fixes the kinetic generator; it therefore does not contradict the same-vacuum counterexample with freely varying generators.

This is a conditional finite-regulator bridge, not a four-dimensional Yang–Mills proof. A gauge-theory implementation must justify the physical domain and gauge invariance. A continuum program must also establish the theory and control the constants in the large-volume and regulator-removal limits in fixed physical units.

Recommended first deliverables are therefore:

1. A precise definition of the physical Hamiltonian, vacuum, gauge-invariant domain, and proposed informational quantity.
2. A lemma identifying exactly which extra dynamical hypotheses exclude the counterexamples in this review.
3. A proof of that lemma in a controlled model, with the massless Maxwell case as a null control where applicable.
4. Lean formalization of the resulting definitions and bridge, followed by an explicit account of the estimates still needed for the continuum problem.

The abstract's “we demonstrate” should be replaced with a statement that the program proposes to investigate such a bridge. The physical introduction should also distinguish pure Yang–Mills glueball excitations from nuclear binding in QCD with quarks; pion exchange and short-distance interactions are central to established nuclear-force descriptions. [Epelbaum–Meißner–Glöckle](https://arxiv.org/abs/nucl-th/0207089)

## Source audit

The PDF itself supplies no source citations. The following are external checks, not references attributed to its author.

| Source | Material checked and use | Scope limit |
|---|---|---|
| [Jaffe–Witten, Quantum Yang–Mills Theory](https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf) | Official target, physical spectrum, construction requirements. Full PDF. | Problem specification, not a proof. |
| [Li–Haldane, 2008](https://arxiv.org/abs/0805.0332) | Entanglement-spectrum definition and model-dependent diagnostic role. Author abstract and bibliographic record. | Fractional quantum Hall application; no Yang–Mills implication. |
| [Casini–Teste–Torroba, 2017; revised 2024](https://arxiv.org/pdf/1703.10656) | Modular Hamiltonians, null geometry, wedge boosts. Relevant full-text sections. | Modular evolution is not globally identified with physical time. |
| [Casini–Huerta–Rosabal, 2014](https://arxiv.org/abs/1312.1183) | Gauge constraints and subsystem ambiguity. Author abstract. | Does not prohibit every well-defined gauge-theory entanglement construction. |
| [Kugo, 1995](https://arxiv.org/pdf/hep-th/9511033) | Original author's quartet and confinement analysis. Relevant full-text sections. | The 1979 Kugo–Ojima publisher record was found, but its full text was not accessible here; conclusions use the accessible Kugo analysis. |
| [Dudal et al., 2023](https://arxiv.org/html/2304.01028v2) | Explicit BRST physical subspace for massless four-dimensional Maxwell theory, §III. Full text. | Abelian control, not pure non-Abelian Yang–Mills. |
| [Gross–Wilczek, 1973](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.30.1343) | Ultraviolet free-field asymptotics. Publisher abstract. | Not a constructive proof or removal of coincident singularities. |
| [Fredenhagen, 1985](https://link.springer.com/article/10.1007/BF01206179) | Type III local algebras under stated scaling hypotheses. Publisher abstract. | Full proof was not re-audited. |
| [Elitzur, 1975](https://journals.aps.org/prd/abstract/10.1103/PhysRevD.12.3978) | Scope of local gauge-symmetry statement. Publisher abstract. | Not a theorem setting invariant observables to zero. |
| [Faddeev, 2009](https://arxiv.org/abs/0911.1013) | Dimensional transmutation in Yang–Mills. Author account checked in the preceding literature review; record rechecked here. | Not a completed Clay solution. |
| [Lean: Axioms and Computation](https://lean-lang.org/theorem_proving_in_lean4/Axioms-and-Computation/) | Official documentation on formal assumptions. | No project supplied for an actual Lean audit. |
| [mathlib: InnerProductSpace definitions](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Defs.html) | Positive-definiteness requirements. Official generated documentation. | A separate indefinite form remains available as a modeling choice. |
| [Epelbaum–Meißner–Glöckle, 2002](https://arxiv.org/abs/nucl-th/0207089) | Nuclear force from pion exchange and local operators. Author abstract. | Context correction; not evidence about the Clay gap. |

**Verification performed:** Both PDF pages were extracted and visually inspected. The finite counterexample's eigenvectors were checked using exact rational arithmetic at \(\varepsilon=1,1/10,1/1000\); its general spectrum follows directly from its orthogonal projectors. The infinite-dimensional counterexample is established analytically above. No Lean verification, Yang–Mills simulation, or continuum construction was performed or claimed.
