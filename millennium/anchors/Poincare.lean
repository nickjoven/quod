import Problems.Poincare.Millennium

/-!
# Anchor descriptors for the Clay Poincaré wrapper (Millennium registry pin)

Pin: lean-dojo/LeanMillenniumPrizeProblems `fd52071`, Lean v4.31.0, Mathlib `fabf563a7c`
(`millennium/PIN.yml`). Tracked at `millennium/anchors/Poincare.lean`; installed into the
gitignored registry clone and compiled there as `Quod.Anchors.Poincare` by
`millennium/anchors/install.sh`, so that `lake env lean` in `millennium/registry` can import it.

Every custom constant in the definitional closure of `MillenniumPoincare.ClayPoincareConjecture`
(six, per `millennium/closure_MillenniumPoincare.ClayPoincareConjecture.json`) is a thin
definition over a Mathlib notion. Each lemma below is the definitional bridge for one constant,
in the shape `scripts/anchor_check.py` admits: `c x₁ … xₖ = rhs` or `c x₁ … xₖ ↔ rhs`, the
`xᵢ` distinct bound variables, `rhs` free of `c`. The chain is

    ClayPoincareConjecture ↔ Formulations.SimplyConnectedClosed3Manifold
      ↔ ∀ M …, [ChartedSpace EuclideanThreeSpace M] … → Nonempty (M ≃ₜ ThreeSphere)
    EuclideanThreeSpace = EuclideanCoordinateSpace ℝ 3 = EuclideanSpace ℝ (Fin 3)
    ThreeSphere = ↥(Metric.sphere (0 : EuclideanFourSpace) 1),
    EuclideanFourSpace = EuclideanCoordinateSpace ℝ 4 = EuclideanSpace ℝ (Fin 4)

and ends in Mathlib names. The last two lemmas anchor the registry's `ClosedCurvesContract` and
`TrivialFundamentalGroup`, which occur in its `Formulations.ClosedCurves` / `TrivialPi1` and not in
the wrapper's closure.

These lemmas are nominated under `anchors:` in `millennium/PIN.yml`. A row there proves nothing:
`registry_import.py` runs the shape gate and the axiom gate on every nomination it reaches and
recomputes the claim; `claims/millennium/poincare_conjecture.yml` is never edited by hand.
-/

universe u

namespace QuodAnchors.Poincare

open MillenniumPoincare

/-- The Clay wrapper is, by definition, the simply-connected closed 3-manifold formulation. -/
theorem anchor_ClayPoincareConjecture :
    ClayPoincareConjecture.{u} ↔
      ClayPoincareConjecture.Formulations.SimplyConnectedClosed3Manifold.{u} :=
  Iff.rfl

/-- The formulation with its binders written out. `EuclideanThreeSpace` and `ThreeSphere` are
anchored below; everything else is Mathlib. -/
theorem anchor_SimplyConnectedClosed3Manifold :
    ClayPoincareConjecture.Formulations.SimplyConnectedClosed3Manifold.{u} ↔
      ∀ (M : Type u) [TopologicalSpace M] [T2Space M] [SecondCountableTopology M]
        [ChartedSpace EuclideanThreeSpace M] [SimplyConnectedSpace M] [CompactSpace M],
        Nonempty (Homeomorph M ThreeSphere) :=
  Iff.rfl

/-- The model space of the 3-manifolds is the registry's `ℝ^3`. -/
theorem anchor_EuclideanThreeSpace : EuclideanThreeSpace = EuclideanCoordinateSpace ℝ 3 :=
  rfl

/-- The ambient space of the 3-sphere is the registry's `ℝ^4`. -/
theorem anchor_EuclideanFourSpace : EuclideanFourSpace = EuclideanCoordinateSpace ℝ 4 :=
  rfl

/-- The 3-sphere is the unit metric sphere about the origin of `ℝ^4`, as a type. -/
theorem anchor_ThreeSphere : ThreeSphere = ↥(Metric.sphere (0 : EuclideanFourSpace) 1) :=
  rfl

/-- The registry's coordinate space is Mathlib's `EuclideanSpace` over `Fin n`
(`Problems.Common.Euclidean`). -/
theorem anchor_EuclideanCoordinateSpace (𝕜 : Type u) (n : ℕ) :
    EuclideanCoordinateSpace 𝕜 n = EuclideanSpace 𝕜 (Fin n) :=
  rfl

/-- Clay's closed-curve wording is Mathlib's `SimplyConnectedSpace`. -/
theorem anchor_ClosedCurvesContract (M : Type u) [TopologicalSpace M] :
    ClosedCurvesContract M ↔ SimplyConnectedSpace M :=
  Iff.rfl

/-- Clay's trivial-`π₁` wording is Mathlib's `SimplyConnectedSpace`. -/
theorem anchor_TrivialFundamentalGroup (M : Type u) [TopologicalSpace M] :
    TrivialFundamentalGroup M ↔ SimplyConnectedSpace M :=
  Iff.rfl

end QuodAnchors.Poincare

#print axioms QuodAnchors.Poincare.anchor_SimplyConnectedClosed3Manifold
#print axioms QuodAnchors.Poincare.anchor_ThreeSphere
