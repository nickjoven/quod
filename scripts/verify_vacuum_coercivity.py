"""Replay outward upper bounds for the vacuum-coercivity counterexample."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

from vacuum_intervals import exp_negative


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "research/vacuum-spectrum/vacuum-coercivity-check.json"
SOURCES = (
    "research/vacuum-spectrum/VACUUM-COERCIVITY.md",
    "scripts/verify_vacuum_coercivity.py",
    "scripts/vacuum_intervals.py",
)


def build():
    rows = []
    previous = F(1)
    for m in (2, 3, 4, 8, 16, 32):
        lower, upper = exp_negative(F(m * m))
        if not 0 < lower <= upper < 1:
            raise ValueError("Invalid exponential enclosure")
        b = F(1, m * m) + 6 * m * upper
        if not 0 < b < previous:
            raise ValueError("Sample expectation bounds must decrease below one")
        ratio = b / (1 - b)
        # Independent elementary loose bounds: exp(m²) > m^6 for m >= 4.
        # At these samples the exact exponential enclosure should also imply
        # B_m <= 2/m² and hence the following simpler rational gap upper bound.
        if m >= 4 and not ratio <= F(2, m * m - 2):
            raise ValueError("Sample gap upper bound failed")
        rows.append({"m": m, "beta": m**4,
                     "expectation_upper": str(b),
                     "gap_over_kappa_upper": str(ratio)})
        previous = b
    return {"scope": "Analytic counterexample; no Yang-Mills target evaluation",
            "sources": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                        for p in SOURCES}, "samples": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate report")
    args = parser.parse_args()
    result = build()
    if args.write:
        REPORT.write_text(json.dumps(result, indent=2) + "\n")
    elif json.loads(REPORT.read_text()) != result:
        raise SystemExit("Counterexample report or source hashes differ")
    for row in result["samples"]:
        print(f"m={row['m']}: gap/kappa <= "
              f"{float(F(row['gap_over_kappa_upper'])):.9g} (display rounded)")
    print("Verified six rational upper bounds and source hashes.")


if __name__ == "__main__":
    main()
