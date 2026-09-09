"""Exact rational SU(2) character spectral enclosures; no target runner.

The infinite Jacobi operator has diagonal g^2 n(n+2), hopping -eta/g^2.
Candidate floats are never trusted as bounds. Integer Sturm counts certify
finite upper endpoints and a tail Schur-complement lower endpoint.
"""
from fractions import Fraction as F
from math import isqrt, lcm

import vacuum_intervals as interval


def rational(value):
    """Declared coordinates use decimal spelling; vectors use exact binary floats."""
    return F(str(value))


def sqrt_interval(value, bits=100):
    """Dyadic outward enclosure using integer square roots only."""
    value = F(value)
    if value < 0 or bits < 1:
        raise ValueError("nonnegative radicand and positive precision required")
    scale = 1 << bits
    root = isqrt((value.numerator * scale**2) // value.denominator)
    low = F(root, scale)
    return low, low if low**2 == value else F(root + 1, scale)


def sturm_count(diagonal, hopping, x, edge_correction=F(0)):
    """Number of eigenvalues strictly below x, using exact determinant signs.

    Positive common denominators reduce the recurrence to integer arithmetic.
    Zero minors are skipped in the sign-variation count, including a zero final
    determinant. Zero hopping is handled as a diagonal matrix explicitly.
    """
    x, hopping, edge_correction = F(x), F(hopping), F(edge_correction)
    diagonal = [F(d) for d in diagonal]
    if not diagonal:
        raise ValueError("empty matrix")
    diagonal[-1] -= edge_correction
    if hopping == 0:
        return sum(d < x for d in diagonal)
    scale = lcm(x.denominator, hopping.denominator, *(d.denominator for d in diagonal))
    d = [int((value - x) * scale) for value in diagonal]
    b2 = int(hopping * scale)**2
    previous, current, last_sign, count = 0, 1, 1, 0
    for value in d:
        previous, current = current, value * current - b2 * previous
        if current:
            sign = 1 if current > 0 else -1
            count += sign != last_sign
            last_sign = sign
    return count


def parameters(g, eta, size):
    g, eta = rational(g), rational(eta)
    if g <= 0 or isinstance(size, bool) or not isinstance(size, int) or size < 2:
        raise ValueError("positive coupling and integer size >=2 required")
    hopping = -eta / g**2
    diagonal = [g**2 * n * (n + 2) for n in range(size)]
    tail_floor = g**2 * size * (size + 2) - 2 * abs(hopping)
    return diagonal, hopping, tail_floor


def finite_bracket(diagonal, hopping, index, width):
    lower = min(diagonal) - 2 * abs(hopping) - 1
    upper = max(diagonal) + 2 * abs(hopping) + 1
    while upper - lower > width:
        middle = (lower + upper) / 2
        if sturm_count(diagonal, hopping, middle) <= index:
            lower = middle
        else:
            upper = middle
    return lower, upper


def eigenvalue_enclosures(g, eta, size, count=5, bits=44):
    """Enclose the first count eigenvalues of the infinite half-line operator.

    For x < tail_floor, S(x) >= A-x - b^2/(tail_floor-x) e e^T.
    The negative count of this lower Schur matrix bounds that of H-x from
    above. A finite Ritz upper endpoint bounds the infinite eigenvalue above.
    """
    if not isinstance(count, int) or not 1 <= count <= size or bits < 1:
        raise ValueError("invalid count or precision")
    diagonal, hopping, tail_floor = parameters(g, eta, size)
    width = F(1, 1 << bits)
    global_floor = -2 * abs(hopping)
    output = []
    for index in range(count):
        finite_low, upper = finite_bracket(diagonal, hopping, index, width)
        lower = global_floor
        if upper < tail_floor:
            left, right = global_floor - 1, upper

            def lower_count(x):
                return sturm_count(diagonal, hopping, x, hopping**2 / (tail_floor - x))

            step = F(1)
            while lower_count(left) > index:
                left -= step
                step *= 2
            while right - left > width:
                middle = (left + right) / 2
                if lower_count(middle) <= index:
                    left = middle
                else:
                    right = middle
            lower = max(global_floor, left)
        output.append({"index": index, "lower": lower, "upper": upper,
                       "finite_lower": finite_low, "tail_floor": tail_floor,
                       "lower_method": "global_operator_floor" if lower == global_floor else "tail_schur_sturm"})
    return output


def verify_enclosures(g, eta, size, enclosures):
    """Check endpoints from scratch; no bisection history or floats required."""
    diagonal, hopping, tail_floor = parameters(g, eta, size)
    if not enclosures or len(enclosures) > size:
        return False
    for index, enclosure in enumerate(enclosures):
        lower, upper = F(enclosure["lower"]), F(enclosure["upper"])
        if enclosure["index"] != index or lower > upper or enclosure["tail_floor"] != tail_floor:
            return False
        if sturm_count(diagonal, hopping, upper) <= index:
            return False
        finite_lower = F(enclosure["finite_lower"])
        if finite_lower > upper or sturm_count(diagonal, hopping, finite_lower) > index:
            return False
        if lower <= -2 * abs(hopping):
            continue
        if lower >= tail_floor or sturm_count(
                diagonal, hopping, lower, hopping**2 / (tail_floor - lower)) > index:
            return False
    return True


def multiply_p(vector):
    result = [F(0)] * (len(vector) + 1)
    for n, value in enumerate(vector):
        result[n + 1] += value / 2
        if n:
            result[n - 1] += value / 2
    return result


def dot(a, b):
    return sum((x * y for x, y in zip(a, b)), F(0))


def eigenvector_bound(g, eta, vector, index, enclosures):
    """Infinite residual and aligned normalized eigenvector-distance bound."""
    q = [F(float(value)) for value in vector]
    diagonal, hopping, _ = parameters(g, eta, len(q))
    norm2 = dot(q, q)
    if norm2 == 0 or not 0 <= index < len(enclosures) - 1:
        raise ValueError("nonzero vector and neighboring eigenvalue enclosure required")
    mu = (enclosures[index]["lower"] + enclosures[index]["upper"]) / 2
    separation = enclosures[index + 1]["lower"] - mu
    if index:
        separation = min(separation, mu - enclosures[index - 1]["upper"])
    residual = [(diagonal[n] - mu) * q[n]
                + (hopping * q[n - 1] if n else 0)
                + (hopping * q[n + 1] if n + 1 < len(q) else 0) for n in range(len(q))]
    residual.append(hopping * q[-1])  # exact omitted hopping component
    residual_squared = dot(residual, residual) / norm2
    rho_upper = sqrt_interval(residual_squared)[1]
    if separation <= 0:
        return {"status": "unresolved", "reason": "neighboring spectral enclosures do not isolate eigenvector",
                "residual_norm_upper": rho_upper, "separation_lower": separation,
                "distance_upper": None, "norm_squared": norm2, "rayleigh_reference": mu}
    # sin(theta) <= rho/separation; aligned distance <= sqrt(2)sin(theta)
    # <= 2rho/separation. Cap at 2, a bound for any two normalized vectors.
    distance = min(F(2), 2 * rho_upper / separation)
    return {"status": "bounded", "residual_norm_upper": rho_upper,
            "separation_lower": separation, "distance_upper": distance,
            "norm_squared": norm2, "rayleigh_reference": mu}


def overlap_intervals(vectors, bounds):
    """Bound P and P^2 transition amplitudes; operator norms are at most one."""
    if any(b["distance_upper"] is None for b in bounds):
        return None
    q = [[F(float(value)) for value in vector] for vector in vectors]
    applied = [multiply_p(q[0])]
    applied.append(multiply_p(applied[0]))
    intervals = []
    for k in range(1, len(q)):
        norm_low, norm_high = sqrt_interval(bounds[0]["norm_squared"] * bounds[k]["norm_squared"])
        if norm_low <= 0:
            raise ValueError("normalization enclosure includes zero")
        uncertainty = bounds[0]["distance_upper"] + bounds[k]["distance_upper"]
        row = []
        for observable in applied:
            numerator = dot(q[k], observable)
            endpoints = (numerator / norm_low, numerator / norm_high)
            lower, upper = max(F(-1), min(endpoints) - uncertainty), min(F(1), max(endpoints) + uncertainty)
            weight_lower = F(0) if lower <= 0 <= upper else min(lower**2, upper**2)
            row.append({"amplitude_lower": lower, "amplitude_upper": upper,
                        "weight_lower": weight_lower, "weight_upper": max(lower**2, upper**2),
                        "nonzero_certified": weight_lower > 0})
        intervals.append(row)
    return intervals


def vacuum_intervals(vector, bound):
    """Full multiplication before projection; ||P^m||<=1 for m=1,...,4."""
    if bound["distance_upper"] is None:
        return None
    q = [F(float(value)) for value in vector]
    applied = q
    moments = []
    for power in range(1, 5):
        applied = multiply_p(applied)
        estimate = dot(q, applied) / bound["norm_squared"]
        uncertainty = 2 * bound["distance_upper"]
        moments.append((max(F(0) if power % 2 == 0 else F(-1), estimate - uncertainty),
                        min(F(1), estimate + uncertainty)))
    p, p2, p3, p4 = moments
    variance_p = interval.subtract(p2, interval.square(p))
    variance_p2 = interval.subtract(p4, interval.square(p2))
    variance_p = max(F(0), variance_p[0]), variance_p[1]
    variance_p2 = max(F(0), variance_p2[0]), variance_p2[1]
    cross = interval.subtract(p3, interval.multiply(p, p2))
    return {"raw_moments": moments, "covariance": [[variance_p, cross], [cross, variance_p2]]}


def correlation_intervals(enclosures, overlaps, vacuum, times):
    """Low-state interval sum plus a PSD omitted covariance tail enclosure."""
    if overlaps is None or vacuum is None:
        return None
    gaps = [(e["lower"] - enclosures[0]["upper"], e["upper"] - enclosures[0]["lower"])
            for e in enclosures[1:]]
    if any(gap[0] <= 0 for gap in gaps):
        return None
    retained = len(overlaps)
    if retained >= len(gaps):
        raise ValueError("next omitted eigenvalue enclosure required")
    tail = [max(F(0), vacuum["covariance"][a][a][1]
                - sum(row[a]["weight_lower"] for row in overlaps)) for a in range(2)]
    tail_cross = sqrt_interval(tail[0] * tail[1])[1]
    records = []
    for time in times:
        time = F(time)
        total = [[(F(0), F(0)) for _ in range(2)] for _ in range(2)]
        for row, gap in zip(overlaps, gaps):
            decay = interval.decay(gap, time)
            for a in range(2):
                weight = row[a]["weight_lower"], row[a]["weight_upper"]
                total[a][a] = interval.add(total[a][a], interval.multiply(weight, decay))
            cross_weight = interval.multiply(
                (row[0]["amplitude_lower"], row[0]["amplitude_upper"]),
                (row[1]["amplitude_lower"], row[1]["amplitude_upper"]))
            total[0][1] = interval.add(total[0][1], interval.multiply(cross_weight, decay))
        decay_upper = interval.exp_negative(gaps[retained][0] * time)[1]
        for a in range(2):
            total[a][a] = interval.add(total[a][a], (F(0), tail[a] * decay_upper))
        total[0][1] = interval.add(total[0][1], (-tail_cross * decay_upper, tail_cross * decay_upper))
        total[1][0] = total[0][1]
        # At t=0 the full vacuum covariance interval is sharper than splitting
        # the retained states and omitted covariance independently.
        if time == 0:
            total = vacuum["covariance"]
        records.append({"time": time, "correlation": total,
                        "tail_diagonal_upper": [t * decay_upper for t in tail],
                        "tail_cross_absolute_upper": tail_cross * decay_upper})
    return records
