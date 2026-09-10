# Version 3 intake and controlled-model proof focus

## Source and scope

The user supplied the revised bundle on 2026-09-09. Its manifest identifies
artifact version 3. All 15 payload hashes verify; the archive SHA-256 is
`2144f205f462cdb094d09a76e9c9bd577013143634ed8e56bd4968eedfded178`.
The exact files are preserved in [design-bundle-v3](design-bundle-v3/README.md),
with archive provenance. Original v1 sources and computational archives remain
unchanged. Bundled patches and GitHub request payloads are archival data.

The numerical specification from “Scope and proposed question” through the
connected-lattice requirements, and the final preregistration requirements,
are byte-identical to the original draft. Version 3 adds a proof milestone;
it inherits a v2 suggestion for a later SU(3) plaquette-chain benchmark.
No benchmark, trajectory or target cell is selected by this intake.

The included [proposal review](design-bundle-v3/review/yang_mills_proposal_review_v1.md)
addresses the conceptual proposal and recommends a controlled-model lemma.
It is not an independent review of quod's implemented certificates, combined
error bounds, result contract or propagation runs. Their review remains open.
The user's later confirmation that the pilot is lost still applies; see
[PILOT-DISPOSITION.md](PILOT-DISPOSITION.md).

## Focus adopted from the revision

The [v3 proof milestone](design-bundle-v3/notes/ym_vacuum_gap_registration_draft.md)
requires a specified physical form/domain, an exact transform or controlled
approximation, an independent sufficient input, a positive remainder bound,
physical normalization and a justified limit transfer. The local
[vacuum derivation](VACUUM-COERCIVITY.md) supplies the transform, a conditional
density comparison and a counterexample to uniformity from cancellation alone.
The following elementary theorem supplies an actual sufficient input in the
already specified controlled models, without using measured eigenvalues.

## Full-domain bounded-potential comparison

Let T be a nonnegative self-adjoint operator on the physical Hilbert space,
with compact resolvent, a simple zero eigenvalue and first excited eigenvalue
γ > 0. Suppose V is a bounded self-adjoint multiplication operator with
v₋ I ≤ V ≤ v₊ I. The form sum H = T + V has the same form domain.
The min–max principle on that full domain gives

\[
\lambda_1(H)\geq\gamma+v_-,\qquad
\lambda_0(H)\leq v_+.
\]

For the second inequality the free normalized vacuum is an admissible trial
state. Therefore

\[
\boxed{\Delta(H)\geq\gamma-(v_+-v_-).}
\]

When the right side is positive the ground eigenvalue is simple, and the
spectral theorem gives the corresponding form inequality for every physical
form-domain vector after projection off the actual H vacuum. This is a lower
bound from a known free spectrum and a pointwise potential bound. It requires
neither an approximate interacting vacuum nor a measured interacting gap.
When the right side is nonpositive it gives no positive certificate.

## Application to the existing SU(2) and U(1) rotors

Use precisely the recovered theta-zero physical domains: SU(2) class functions
with Haar measure, and periodic U(1) functions with normalized Haar measure.
The form domain is the corresponding invariant H¹ space; smooth physical
functions are a core. No singular orbit-space coordinate approximation is
needed. For g > 0 and η ≥ 0, the kinetic spectra and bounded potential give

| Model | Free physical gap γ | Potential oscillation | Certified lower bound |
| --- | --- | --- | --- |
| SU(2), T = 4g² C₂ | 3g², from j = 1/2 | 4η/g², since −1 ≤ P ≤ 1 | 3g² − 4η/g² |
| U(1), T = −4g² ∂²θ | 4g², from n = ±1 | 4η/g², since −1 ≤ cos θ ≤ 1 | 4g² − 4η/g² |

The U(1) bound covers both parities, not just the even probes. The multiplicity
of its first free excited level does not affect min–max. Both free vacua are
simple. Positivity requires respectively 3g⁴ > 4η and g⁴ > η. At η = 0 the
bounds are exact. Adding a scalar energy offset changes v₋ and v₊ equally
and leaves the excitation bound unchanged.

These are analytic parameter inequalities, not evaluations or selections of
the held-out cells. The certificate holds on the infinite representation
space at fixed rotor parameters, so it is not an inference from a finite
Rayleigh minimum. It also applies to conforming representation truncations
containing the free vacuum and first excited level: compression preserves the
potential bounds, and the free gap is unchanged. Grid discretizations need
their own operator comparison and are not included in that assertion.

## Constants that still lack the required uniformity

For a reference energy s_r fixed independently of the candidate gap, this
method requires inf_r (γ_r − osc V_r)/s_r > 0. It fails to certify weak g
at fixed positive η. For a connected many-link Hamiltonian the total
potential oscillation can grow with volume; the one-rotor inequality supplies
no volume-uniform estimate. Neither rotor defines the requested
four-dimensional continuum trajectory or its limiting theory.

Thus the controlled-model sufficient-input lemma is proved here, while a
useful interacting volume-uniform input remains open. The v3 challenge cases
remain essential: an accumulating spectrum or increasing circle length loses
γ > 0 uniformly, and restricting trial functions cannot repair that loss.
The fixed-kinetic double-well example in VACUUM-COERCIVITY.md likewise lies
outside any asserted uniformly positive comparison margin.

## Next development obligations

1. Review this full-domain comparison and the existing numerical instrument
   separately. The proposal review does not certify either implementation.
2. If formalizing the lemma, specify the self-adjoint operator, form domain,
   ordered eigenvalues and min–max hypotheses first. No Lean build is claimed.
3. Before a connected-model extension, specify the Hamiltonian and domains,
   establish an independent volume-uniform estimate or explicitly retain its
   failure, and define the physical reference scale and convergence claims.
   The suggested plaquette-chain benchmark needs a separate design and
   source assessment; rotor error bounds cannot be transferred by analogy.
4. Preserve owner assignment, independent review, future registration and
   the user's target-selection boundary for the existing numerical study.

## Verification

`python3 -m unittest discover -s scripts -p 'test_vacuum_v3_bundle.py' -v`
verifies the manifest, exact member set and preserved numerical specification.
It checks artifact integrity and version scope, not the truth of imported
literature claims or the analytic proof above. Those claims retain the source
and review qualifications in the supplied documents.
