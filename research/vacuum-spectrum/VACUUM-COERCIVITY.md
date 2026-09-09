# Vacuum reduction and the missing uniform coercivity estimate

## Scope and conclusion

This develops the finite-regulator, theta-zero Hamiltonian in the recovered
literature check. The constrained energy reduces exactly to a weighted
Dirichlet form. A positive constant exists at each connected compact regulator
under the assumptions below. A constant uniform in cutoff and volume does
**not** follow from the constraints and vacuum equation alone. The counterexample
below proves that logical obstruction; it is not a counterexample to Yang–Mills.
No target cell is selected or evaluated here.

## Constraints and vacuum equation

Let the configuration space be a connected finite product of compact link
groups, with normalized Haar measure dU. Work in the gauge-invariant physical
Hilbert space, so the Gauss generators satisfy G_a Ψ = 0. Constraint terms
proportional to G_a vanish on this domain. They do not give an energy lower
bound on the remaining physical directions.

For divergence-free invariant derivatives X_j with a fixed normalization, set

\[
H=-\kappa\sum_jX_j^2+V,\qquad \kappa>0,
\qquad H\psi_0=E_0\psi_0.
\]

Assume V is real, smooth and gauge invariant, and ψ₀ is a normalized, smooth,
strictly positive, gauge-invariant ground state. Write Ψ = ψ₀ f and
dν = ψ₀² dU. Positivity makes this a unitary correspondence between the physical
weighted L² space and the physical original space. Begin with smooth invariant
f in a form core. The vacuum equation gives

\[
(V-E_0)\psi_0=\kappa\sum_jX_j^2\psi_0.
\]

Expanding the energy for complex f gives

\[
\begin{aligned}
q[\psi_0f]
&:=\langle\psi_0f,(H-E_0)\psi_0f\rangle\\
&=\kappa\sum_j\int\Big[
\psi_0^2|X_jf|^2+|f|^2(X_j\psi_0)^2
+\psi_0(X_j\psi_0)X_j|f|^2
+|f|^2\psi_0X_j^2\psi_0\Big]dU.
\end{aligned}
\]

The last three terms are precisely
X_j(|f|² ψ₀ X_jψ₀), whose integral is zero by Haar integration by parts.
Consequently, with extension by closure to the form domain,

\[
\boxed{q[\psi_0f]=\kappa\int\sum_j|X_jf|^2d\nu\geq0.}
\]

The potential has entered the vacuum measure; its effect has not disappeared.
Equivalently the transformed operator on the core is
L = −κ Σ_j [X_j² + 2(X_j log ψ₀)X_j].

## What it means to control every physical deviation

Let P₀ be the orthogonal projection onto ψ₀. Then

\[
\|(1-P_0)\Psi\|^2
=\int|f-\nu(f)|^2d\nu=\operatorname{Var}_{\nu}(f).
\]

Thus the requested statement is exactly

\[
\boxed{\kappa\int\sum_j|X_jf|^2d\nu
\geq\Delta\operatorname{Var}_{\nu}(f)
\quad\text{for all physical form-domain }f.}
\]

The optimal Δ is the bottom of the spectrum above the vacuum. Nonnegativity
does not establish Δ > 0. On this fixed connected compact space, ellipticity,
compactness and strict positivity of ψ₀ do give a positive gap. They provide
no uniform control as the regulator changes. A degenerate vacuum would require
projection onto its entire ground space instead of subtraction of one mean.

## A sufficient bound with explicit constants

At regulator r, suppose a reference probability measure μ_r satisfies

\[
\operatorname{Var}_{\mu_r}(f)
\leq C_r\int\sum_j|X_{r,j}f|^2d\mu_r,
\qquad 0<a_r\leq\frac{d\nu_r}{d\mu_r}\leq b_r<\infty.
\]

These inequalities must hold for the physical domain and the same gradient
normalization. Using variance as the infimum over constant shifts,

\[
\operatorname{Var}_{\nu_r}(f)
\leq b_r\operatorname{Var}_{\mu_r}(f)
\leq \frac{b_rC_r}{a_r}\int\sum_j|X_{r,j}f|^2d\nu_r.
\]

Therefore Δ_r ≥ κ_r a_r/(b_r C_r). If physical energies are obtained by
multiplying regulator energies by c_r > 0, an explicit sufficient condition is

\[
\boxed{\inf_r\frac{c_r\kappa_r a_r}{b_rC_r}>0.}
\]

The infimum must cover every cutoff and volume along the specified limit.
The vacuum equation alone supplies no such bound on a_r/b_r or C_r.
For example Haar comparison at a fixed regulator uses the minimum and maximum
of ψ₀², which can separate without bound as the regulator changes.

## Counterexample with fixed kinetic coefficient

Consider a periodic physical U(1) holonomy θ, normalized Haar measure
dθ/(2π), and a fixed κ > 0. Holonomy class functions are gauge invariant for
U(1), so this example already lives in a physical quotient. For β > 0 define

\[
\psi_\beta=Z_\beta^{-1/2}e^{(\beta/2)\cos2\theta},\qquad
H_\beta=-\kappa\partial_\theta^2+
\kappa(\beta^2\sin^22\theta-2\beta\cos2\theta).
\]

Here Z_β normalizes ψ_β². Direct differentiation gives
ψ_β'/ψ_β = −β sin 2θ and
ψ_β''/ψ_β = β² sin² 2θ − 2β cos 2θ. Thus H_β ψ_β = 0 and

\[
H_\beta=\kappa A_\beta^*A_\beta,
\qquad A_\beta=\partial_\theta+\beta\sin2\theta.
\]

The kernel is one dimensional: A_β ψ = 0 has only scalar multiples of ψ_β
as periodic solutions. Every β has a unique positive vacuum and a positive
gap. Nevertheless f(θ) = cos θ has zero ν_β mean by θ ↦ θ+π, and

\[
0<\Delta_\beta\leq
\kappa\frac{\int\sin^2\theta\,d\nu_\beta}
{\int\cos^2\theta\,d\nu_\beta}\longrightarrow0.
\]

Here is an explicit proof of the limit without a spectral approximation.
Put S = sin² θ. Apart from normalization the density is e^(−2βS).
For 0 < δ < 1 let a_δ be the Haar measure of {S ≤ δ/2}. Then

\[
\nu_\beta(S\geq\delta)\leq a_\delta^{-1}e^{-\beta\delta},
\qquad \mathbb E_{\nu_\beta}S
\leq\delta+a_\delta^{-1}e^{-\beta\delta}.
\]

The arc |θ| ≤ √(δ/2) alone gives a_δ ≥ √(δ/2)/π.
Take integers m ≥ 2, δ = m⁻² and β = m⁴. Since √2 π < 6,

\[
\mathbb E_{\nu_{m^4}}S\leq B_m:=m^{-2}+6m e^{-m^2},
\qquad
\frac{\Delta_{m^4}}{\kappa}\leq\frac{B_m}{1-B_m}\longrightarrow0.
\]

B₂ < 1 and B_m decreases for m ≥ 2, so the denominators are positive.
The configuration space, physical constraint and kinetic coefficient stay
fixed. The vacuum measure develops two separated concentrations. This disproves
the inference from those general assumptions to a uniform positive constant;
the potential is not the pure Yang–Mills potential.

## Passing a proved bound to a limit

Even a uniform regulated bound needs a construction of the limiting theory.
A sufficient transfer hypothesis is: a nonnegative limiting closed form Q
and vacuum Ω exist, and every vector u in a form core orthogonal to Ω has
physical approximants u_r orthogonal to Ω_r such that
‖u_r‖ → ‖u‖ and c_r q_r[u_r] → Q[u]. Then
c_r q_r[u_r] ≥ Δ_* ‖u_r‖² passes to Q[u] ≥ Δ_* ‖u‖²,
and extends by form closure. These convergence and vacuum hypotheses must be
proved; they are not consequences of the cancellation identity.

The existing single-angle development certificates do not establish a
uniform reference inequality, vacuum-density comparison, or this limiting
construction for field theory. The requested unconditional Yang–Mills
coercivity theorem remains unproved here. The broader existence and mass-gap
problem remains listed as unsolved by
[Clay Mathematics Institute](https://www.claymath.org/millennium/yang-mills-the-maths-gap/).

## Reproducible check

Run `python3 scripts/verify_vacuum_coercivity.py` from the repository root.
It checks the documented sample bounds using the existing outward exponential
routine and verifies the checked-in report, including hashes of this page and
the arithmetic sources. These checks certify the displayed numerical upper
bounds and detect artifact drift; the analytic arguments above prove the
identity and the limit. They are not a machine-checked Yang–Mills proof.
