"""scripts/defs_digest.py: the parse of the Lean walker's output and the digest/compare logic, with no Lean."""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("defs_digest", os.path.join(ROOT, "scripts", "defs_digest.py"))
D = importlib.util.module_from_spec(spec); sys.modules["defs_digest"] = D; spec.loader.exec_module(D)

OUT = """DEF NavierStokes.Comparator.navier_stokes_breakdown_R3 theorem ComparatorChallenges.NavierStokes
TYPE-BEGIN
∀ (_ : Real),
  Foo _
TYPE-END
DEF NavierStokes.Comparator.divergence def ComparatorChallenges.NavierStokes
TYPE-BEGIN
(_ : A) → B
TYPE-END
VALUE-BEGIN
fun _ => trace _
VALUE-END
DEF NavierStokes.Comparator.InitialVelocityCondition inductive ComparatorChallenges.NavierStokes
TYPE-BEGIN
Prop
TYPE-END
DONE
"""


def test_parse_rows_and_whitespace_normalization():
    rows = D.parse(OUT)
    assert [r["name"].split(".")[-1] for r in rows] == ["navier_stokes_breakdown_R3", "divergence", "InitialVelocityCondition"]
    assert rows[0]["type"] == "∀ (_ : Real), Foo _" and rows[0]["value"] is None
    assert rows[1]["value"] == "fun _ => trace _" and rows[1]["kind"] == "def"
    assert rows[2]["kind"] == "inductive"


def test_digest_ignores_modules_and_order_but_not_definitions():
    a = D.parse(OUT)
    b = [dict(r, module="NavierStokes.ComparatorDefinitions") for r in reversed(a)]
    assert D.digest(a) == D.digest(b)
    c = [dict(r) for r in a]; c[1]["value"] = "fun _ => 0"
    assert D.digest(a) != D.digest(c)
    cmp = D.compare(a, c)
    assert cmp == {"equal": False, "only_a": [], "only_b": [], "differ": ["NavierStokes.Comparator.divergence"],
                   "digest_a": D.digest(a), "digest_b": D.digest(c)}


def test_compare_reports_missing_names():
    a = D.parse(OUT)
    cmp = D.compare(a, a[:-1])
    assert not cmp["equal"] and cmp["only_a"] == ["NavierStokes.Comparator.InitialVelocityCondition"] and cmp["differ"] == []
    assert D.compare(a, list(a))["equal"]
