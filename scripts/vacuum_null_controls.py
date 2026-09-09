"""Exact hidden-state, tensor, gapless and disconnected analysis controls."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
from pathlib import Path

import vacuum_certificate_run as certificates
import vacuum_development as baseline
import vacuum_intervals as interval
import vacuum_time_windows as windows


def measure(energies, column, center=True):
    """Spectral measure of O|vacuum>, with vacuum index zero in a known eigenbasis."""
    energies, column = [F(x) for x in energies], [F(x) for x in column]
    if len(energies) != len(column) or len(energies) < 2 or energies != sorted(energies):
        raise ValueError('ordered energies and matching observable column required')
    weights = [x*x for x in column]
    if center:
        weights[0] = F(0)
    support = [{'gap': energy-energies[0], 'weight': weight} for energy, weight in zip(energies, weights) if weight]
    positive = [energy-energies[0] for energy in energies if energy > energies[0]]
    return {'first_ordered_gap': energies[1]-energies[0],
            'ground_multiplicity': sum(e == energies[0] for e in energies),
            'gap_above_ground_space': min(positive) if positive else None,
            'observed_threshold': min(row['gap'] for row in support) if support else None,
            'zero_gap_weight': sum((r['weight'] for r in support if r['gap'] == 0), F(0)),
            'variance': sum(weights), 'support': support}


def uniform_gapless_correlation(time):
    """Uniform spectral measure on [0,1]: C(t)=integral_0^1 exp(-Et)dE."""
    time = F(time)
    if time < 0:
        raise ValueError('nonnegative time required')
    if time == 0:
        return F(1), F(1)
    low, high = interval.exp_negative(time)
    return (1-high)/time, (1-low)/time


def uniform_mass_below(epsilon):
    epsilon = F(epsilon)
    if not 0 <= epsilon <= 1:
        raise ValueError('epsilon must be in [0,1]')
    return epsilon  # exact integral of density one over [0,epsilon]


def evaluate():
    hidden = measure([0, 1, 2], [0, 0, 1])
    base = measure([0, 2, 5], [3, 1, 2])
    shifted = measure([7, 9, 12], [3, 1, 2])
    clocked = measure([0, 6, 15], [3, 1, 2])
    # The observable acts on the second factor; a dark low-energy first factor
    # changes the full gap without changing its correlation.
    tensor_records = []
    for epsilon in (F(1), F(1, 2), F(1, 4), F(1, 8)):
        states = sorted((a+b, i, j) for (i,a),(j,b) in product(enumerate([0,epsilon]), enumerate([0,F(3)])))
        tensor_records.append(measure([s[0] for s in states], [F(1) if s[1:] == (0,1) else F(0) for s in states]))
    disconnected = measure([0, 0, 1], [0, 1, 1])
    early = windows.slope_interval(uniform_gapless_correlation(1), uniform_gapless_correlation(2), F(1))
    late = windows.slope_interval(uniform_gapless_correlation(20), uniform_gapless_correlation(40), F(20))
    checks = {
        'hidden_state_threshold_differs_from_full_gap': hidden['first_ordered_gap'] == 1 and hidden['observed_threshold'] == 2,
        'energy_offset_invariance': shifted == base,
        'clock_scales_gaps_not_weights': [r['weight'] for r in clocked['support']] == [r['weight'] for r in base['support']]
            and [r['gap'] for r in clocked['support']] == [3*r['gap'] for r in base['support']],
        'tensor_dark_factor_changes_only_full_gap': [r['first_ordered_gap'] for r in tensor_records] == [F(1),F(1,2),F(1,4),F(1,8)]
            and all(r['observed_threshold'] == 3 and r['variance'] == 1 for r in tensor_records),
        'gapless_uniform_mass_fixtures': all(uniform_mass_below(F(1, 2**k)) == F(1, 2**k) for k in range(1, 17)),
        'gapless_effective_gap_decreases': 0 < late[0] < late[1] < early[0],
        'disconnected_ground_space_retained': disconnected['ground_multiplicity'] == 2
            and disconnected['first_ordered_gap'] == 0 and disconnected['gap_above_ground_space'] == 1
            and disconnected['zero_gap_weight'] == 1,
        'centering_removes_only_selected_vacuum_mean': base['zero_gap_weight'] == 0 and disconnected['zero_gap_weight'] == 1,
    }
    uncentered = measure([0,2,5], [3,1,2], center=False)
    dropped_zero = measure([0,1], [0,1])
    mutants = {
        'assign_full_gap_to_dark_observable': hidden['first_ordered_gap'] != hidden['observed_threshold'],
        'omit_centering': uncentered['zero_gap_weight'] != base['zero_gap_weight'],
        'drop_degenerate_zero_mode': dropped_zero['variance'] != disconnected['variance'],
        'declare_positive_floor_for_uniform_measure': F(1,16) < F(1,8) and uniform_mass_below(F(1,16)) > 0,
    }
    return {'schema_version': 1, 'state': 'completed', 'registered': False, 'targets_run': 0,
            'targets': [{'id': row, 'status': 'unrun'} for row in baseline.target_ids()],
            'scope': 'analytic analysis fixtures; not additional development rungs or solver-level mutants',
            'checks': checks, 'mutants_rejected': mutants, 'pass': all(checks.values()) and all(mutants.values()),
            'hidden': hidden, 'tensor_family': tensor_records, 'disconnected': disconnected,
            'uniform_gapless': {'spectral_support': '[0,1]', 'density': '1', 'spectral_gap': F(0),
                'mass_below_epsilon': 'epsilon for every 0<epsilon<=1',
                'early_effective_gap': early, 'late_effective_gap': late},
            'source_sha256': {p: hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest() for p in
                ('scripts/vacuum_null_controls.py', *windows.SOURCES)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate()
    baseline.write_report(args.output, certificates.encode(report))
    print('pass' if report['pass'] else 'failure')
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
