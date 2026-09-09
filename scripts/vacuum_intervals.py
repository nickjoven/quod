"""Rational interval operations and outward standard-library exponential."""
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F


def add(a, b):
    return a[0] + b[0], a[1] + b[1]


def subtract(a, b):
    return a[0] - b[1], a[1] - b[0]


def multiply(a, b):
    values = [x * y for x in a for y in b]
    return min(values), max(values)


def square(a):
    return (F(0) if a[0] <= 0 <= a[1] else min(a[0]**2, a[1]**2),
            max(a[0]**2, a[1]**2))


def exp_negative(x, precision=70):
    """Enclose exp(-x) for exact nonnegative rational x.

    Decimal.exp is correctly rounded (ROUND_HALF_EVEN). Outward conversion
    of its input, monotonicity, and adjacent representable outputs enclose
    both input rounding and the exponential's final rounding.
    """
    x = F(x)
    if not 0 <= x <= 10000 or precision < 10:
        raise ValueError("exponent must be in [0,10000] and precision >=10")
    if x == 0:
        return F(1), F(1)
    with localcontext() as ctx:
        ctx.prec = precision
        ctx.rounding = ROUND_FLOOR
        low = Decimal(x.numerator) / Decimal(x.denominator)
        ctx.rounding = ROUND_CEILING
        high = Decimal(x.numerator) / Decimal(x.denominator)
        lower = (-high).exp().next_minus()
        upper = (-low).exp().next_plus()
        if not lower.is_finite() or not upper.is_finite():
            raise ValueError("nonfinite exponential enclosure")
        return max(F(0), F(lower)), min(F(1), F(upper))


def decay(gap, time):
    if gap[0] <= 0 or gap[1] < gap[0] or time < 0:
        raise ValueError("positive ordered gap and nonnegative time required")
    return exp_negative(gap[1] * time)[0], exp_negative(gap[0] * time)[1]
