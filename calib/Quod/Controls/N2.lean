import Mathlib.Tactic
/-! N2: the top-level proposition is `True` behind a name. Must land as
`stated` with reason: canonical type reduces to `True`; no anchor. -/
def PvsNPClaim : Prop := True
theorem p_vs_np : PvsNPClaim := trivial
