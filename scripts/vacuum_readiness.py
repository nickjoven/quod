"""Consolidate and replay development evidence; never authorize target execution."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import vacuum_development as baseline
import vacuum_refinement as refinement
import vacuum_certificate_run as su2cert
import vacuum_late_time_run as su2time
import vacuum_u1_run as u1scalar
import vacuum_u1_certificate_run as u1cert
import vacuum_u1_semigroup_run as u1time
import vacuum_time_windows as windows
import vacuum_null_controls as nulls

DIRECTORY = baseline.ROOT / 'research/vacuum-spectrum'
SCHEMA = DIRECTORY / 'readiness.schema.json'
INPUTS = ('refinement.json', 'certificates.json', 'late-times.json',
          'u1-development.json', 'u1-certificates.json', 'u1-semigroup.json', 'null-controls.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs():
    reports, hashes = {}, {}
    for name in INPUTS:
        path = DIRECTORY / name
        reports[name] = json.loads(path.read_text())
        hashes[name] = digest(path)
    return reports, hashes


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_schema(report):
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report)


def audit(reports, hashes):
    require(set(reports) == set(INPUTS) and set(hashes) == set(INPUTS), 'input manifest mismatch')
    require(all(hashes[name] == digest(DIRECTORY / name) for name in INPUTS), 'input hash mismatch')
    for name, report in reports.items():
        require(report['registered'] is False and report['targets_run'] == 0,
                'registration or target boundary changed: ' + name)
        require(baseline.coverage(report['targets']) and all(t['status'] == 'unrun' for t in report['targets']),
                'target manifest changed: ' + name)
        for path, expected in report['source_sha256'].items():
            require(digest(baseline.ROOT / path) == expected, 'source drift: ' + path)
        dependencies = report.get('input_sha256', {})
        if isinstance(dependencies, str):
            dependencies = {report.get('input', 'u1-development.json'): dependencies}
        for path, expected in dependencies.items():
            actual = baseline.ROOT / path if '/' in path else DIRECTORY / path
            require(digest(actual) == expected, 'input drift: ' + path)
    require(reports['null-controls.json'] == su2cert.encode(nulls.evaluate()), 'null control replay failed')
    rows = []
    for theory, names, scalar_runner, cert_runner, time_runner in (
        ('SU2', INPUTS[:3], refinement, su2cert, su2time),
        ('U1', INPUTS[3:6], u1scalar, u1cert, u1time)):
        scalar, cert, temporal = [reports[n] for n in names]
        for report, runner in ((scalar, scalar_runner), (cert, cert_runner), (temporal, time_runner)):
            require(report['state'] == 'completed' and runner.accounting(report), 'incomplete ' + theory)
            require(all(r['status'] == 'completed' for c in report['cells'] for r in c['rungs']), 'failed rung')
        for s, c, t in zip(scalar['cells'], cert['cells'], temporal['cells']):
            if theory == 'SU2':
                agreement = refinement.finite_goal(baseline.differences(s['final']['character'], s['final']['angle_fourth']))
            else:
                agreement = u1scalar.u1.within_goal(u1scalar.u1.differences(s['final']['fourier'], s['final']['angle']))
            for rung in c['rungs']:
                require(cert_runner.verify_result(c['g'], rung['result'], [F(v) for v in c['times']]), 'certificate replay failed')
            final = c['rungs'][-1]['result']
            gaps = final['first_three_gap_intervals' if theory == 'SU2' else 'first_three_even_gap_intervals']
            eigen = final['enclosures' if theory == 'SU2' else 'even_enclosures']
            derived = [(F(e['lower'])-F(eigen[0]['upper']), F(e['upper'])-F(eigen[0]['lower'])) for e in eigen[1:4]]
            require(gaps == su2cert.encode(derived), 'gap intervals differ from eigenvalue bounds')
            if theory == 'U1':
                require(t['times'] == [float(F(v)) for v in c['times']], 'U1 time mismatch')
            full_gap = gaps[0] if theory == 'SU2' else final['parity']['full_gap_interval']
            checked_gaps = gaps if theory == 'SU2' else [*gaps, full_gap]
            vacuum = windows.numeric(final['vacuum'])
            moments = [*vacuum['raw_moments'][:2], vacuum['covariance'][0][0], vacuum['covariance'][1][1], vacuum['covariance'][0][1]]
            scalar_bound = all(F(lo)>0 and (F(hi)-F(lo))/(2*F(lo))<=F('1e-6') for lo,hi in checked_gaps) and all((hi-lo)/2<=F('1e-6') for lo,hi in moments)
            require(scalar_bound == final['scalar_budget_met'], 'false scalar budget flag')
            overlap = [F(o['weight_lower'])>0 for o in final['overlaps'][0]]
            reference = su2time.extended_certificate(c,t['times']) if theory == 'SU2' else u1time.window_reference(c)
            assessed = windows.assess_cell(reference,t)
            require(su2cert.encode(assessed) == t['window_assessment'], 'window replay failed')
            correlation = windows.numeric(reference['rungs'][-1]['result']['correlations'])
            require(su2cert.encode(su2cert.angle_error_bounds(correlation,vacuum,t['rungs'])) == t['angle_error_bounds'], 'combined error replay failed')
            common = [p['sample_indices'] for p in assessed['rungs'][-1]['pairs'] if all(o['qualifies'] for o in p['observables'])]
            rows.append({'theory': theory, 'g': c['g'], 'eta': 1, 'partition': 'development',
                'full_gap_interval': full_gap, 'observable_gap_interval': gaps[0],
                'observable_gap_reference': 'first_ordered_excitation' if theory=='SU2' else 'first_even_excitation',
                'nonzero_overlap': overlap, 'cross_representation_agreement': agreement,
                'scalar_bounds_met': scalar_bound, 'qualifying_common_sample_pairs': common,
                'registered_window': None, 'status': 'development_qualified' if agreement and scalar_bound and all(overlap) and common else 'unresolved'})
    result = {'schema_version': 1, 'state': 'audited', 'registered': False, 'targets_run': 0,
        'target_execution_authorized': False, 'targets': reports['refinement.json']['targets'],
        'input_sha256': hashes, 'audit_source_sha256': digest(Path(__file__)), 'schema_sha256': digest(SCHEMA),
        'cells': rows, 'external_prerequisites': {
            'source_pilot_and_conventions': 'unresolved', 'litcheck_and_lessons_workflow': 'unresolved',
            'owning_registration_and_identifiers': 'unresolved', 'independent_review': 'unresolved'},
        'scope': 'Single-angle development models under documented analytic/arithmetic assumptions; no field-theory conclusion'}
    validate_schema(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.resolve() == (DIRECTORY / 'readiness.json').resolve(), 'use the dedicated readiness.json output')
    reports, hashes = load_inputs()
    result = audit(reports, hashes)
    baseline.write_report(args.output, result)
    print(json.dumps({'state': result['state'], 'qualified_development_cells': sum(c['status']=='development_qualified' for c in result['cells']), 'external_prerequisites': result['external_prerequisites']}))


if __name__ == '__main__':
    main()
