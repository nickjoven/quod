"""Coordinate-bound rotor certificates using the reviewed exact engines.

No run manifest, CLI, target selection or target authorization is implemented
here. Production callers must enforce the future committed execution envelope.
"""
from fractions import Fraction as F

import numpy as np
from scipy.linalg import eigh_tridiagonal

import vacuum_certified as su2
import vacuum_u1_design_certified as u1
from vacuum_certificate_run import encode


def coordinates(theory, g, eta, cutoff, times):
    g, eta = su2.rational(g), su2.rational(eta)
    if theory not in ('SU2', 'U1') or g <= 0 or eta < 0:
        raise ValueError('valid theory, positive g and nonnegative eta required')
    if isinstance(cutoff, bool) or not isinstance(cutoff, int) or cutoff < 4:
        raise ValueError('integer cutoff >=4 required; SU2 uses J, U1 uses K')
    times = tuple(F(t) for t in times)
    if not times or times[0] < 0 or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('nonempty strictly increasing nonnegative exact sample times required')
    return g, eta, times


def assemble(theory, g, eta, cutoff, times, eigen, odd, vectors):
    """Exact replay stage; eigensolver output is only a candidate vector."""
    if len(vectors) != 4 or any(len(v) != 2*cutoff+1 for v in vectors):
        raise ValueError('four full-length candidate vectors required')
    if len(eigen) != 5:
        raise ValueError('five ordered spectral enclosures required')
    if theory == 'SU2':
        if odd is not None or not su2.verify_enclosures(g, eta, 2*cutoff+1, eigen):
            raise ValueError('invalid SU2 spectral endpoints')
        bounds = [su2.eigenvector_bound(g, eta, v, k, eigen) for k, v in enumerate(vectors)]
        overlaps = su2.overlap_intervals(vectors, bounds)
        vacuum = su2.vacuum_intervals(vectors[0], bounds[0])
        result = {'size': 2*cutoff+1, 'enclosures': eigen, 'endpoint_verification': True}
        gap_key, overlap_key = 'first_three_gap_intervals', 'first_gap_overlap_certified'
        ground_proved = True
    else:
        if (odd is None or len(odd) != 1 or not u1.verify(g, eta, cutoff, 'even', eigen)
                or not u1.verify(g, eta, cutoff, 'odd', odd)):
            raise ValueError('invalid U1 spectral endpoints')
        bounds = [u1.vector_bound(g, eta, v, k, eigen) for k, v in enumerate(vectors)]
        overlaps, vacuum = u1.observables(vectors, bounds)
        parity = u1.gap_fields(eigen, odd)
        result = {'cutoff': cutoff, 'even_enclosures': eigen, 'odd_enclosures': odd, 'parity': parity}
        gap_key, overlap_key = 'first_three_even_gap_intervals', 'first_even_overlap_certified'
        ground_proved = parity['even_ground_below_odd_certified']
    gaps = [(e['lower']-eigen[0]['upper'], e['upper']-eigen[0]['lower']) for e in eigen[1:4]]
    checked_gaps = list(gaps)
    if theory == 'U1' and ground_proved:
        checked_gaps.append(parity['full_gap_interval'])
    gap_ok = ground_proved and all(lo > 0 and (hi-lo)/(2*lo) <= F(1,10**6) for lo,hi in checked_gaps)
    moments = None if vacuum is None else [*vacuum['raw_moments'][:2],
        vacuum['covariance'][0][0], vacuum['covariance'][1][1], vacuum['covariance'][0][1]]
    moment_ok = moments is not None and all((hi-lo)/2 <= F(1,10**6) for lo,hi in moments)
    correlations = su2.correlation_intervals(eigen, overlaps, vacuum, times) if ground_proved else None
    result.update(candidate_vectors_hex=[[float(v).hex() for v in q] for q in vectors],
        vector_bounds=bounds, overlaps=overlaps, vacuum=vacuum, correlations=correlations,
        scalar_budget_met=bool(gap_ok and moment_ok),
        bound_status='bounded' if correlations is not None else 'unresolved')
    result[gap_key] = gaps
    result[overlap_key] = None if overlaps is None else [o['nonzero_certified'] for o in overlaps[0]]
    return result


def calculate(theory, g, eta, cutoff, times):
    g, eta, times = coordinates(theory, g, eta, cutoff, times)
    if theory == 'SU2':
        d, b, _ = su2.parameters(g, eta, 2*cutoff+1)
        _, v = eigh_tridiagonal(np.asarray(d, dtype=float), np.full(2*cutoff, float(b)),
                               select='i', select_range=(0,3))
        vectors = v.T
        eigen, odd = su2.eigenvalue_enclosures(g, eta, 2*cutoff+1), None
    else:
        d, squared, _, _ = u1.parameters(g, eta, cutoff, 'even')
        _, v = eigh_tridiagonal(np.asarray(d, dtype=float), -np.sqrt(np.asarray(squared, dtype=float)),
                               select='i', select_range=(0,3))
        vectors = np.empty((4,2*cutoff+1))
        vectors[:,cutoff] = v[0]
        vectors[:,cutoff+1:] = v[1:].T/np.sqrt(2)
        vectors[:,:cutoff] = vectors[:,cutoff+1:][:,::-1]
        eigen = u1.enclosures(g, eta, cutoff, 'even')
        odd = u1.enclosures(g, eta, cutoff, 'odd', count=1)
    return encode({'theory': theory, 'g': g, 'eta': eta, 'cutoff': cutoff, 'times': times,
                   'result': assemble(theory, g, eta, cutoff, times, eigen, odd, vectors)})


def decode_eigen(rows):
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('endpoint array of objects required')
    return [{k: (F(v) if k in ('lower', 'upper', 'finite_lower', 'tail_floor') else v)
             for k,v in row.items()} for row in rows]


def verify(record):
    """Replay all derived fields without invoking an eigensolver."""
    try:
        if set(record) != {'theory', 'g', 'eta', 'cutoff', 'times', 'result'}:
            return False
        theory, cutoff = record['theory'], record['cutoff']
        g, eta, times = coordinates(theory, record['g'], record['eta'], cutoff, record['times'])
        result = record['result']
        eigen = decode_eigen(result['enclosures' if theory == 'SU2' else 'even_enclosures'])
        odd = None if theory == 'SU2' else decode_eigen(result['odd_enclosures'])
        vectors = [[float.fromhex(v) for v in q] for q in result['candidate_vectors_hex']]
        expected = assemble(theory, g, eta, cutoff, times, eigen, odd, vectors)
        return result == encode(expected)
    except (KeyError, TypeError, ValueError, ArithmeticError):
        return False


def verified_channels(record):
    """Bind the future channel adapter to independently replayed coordinates."""
    import vacuum_future_adapter as adapter
    if not verify(record):
        raise ValueError('coordinate-bound certificate replay failed')
    return adapter.adapt_channels(record['theory'], record['g'], record['eta'], record['result'])
