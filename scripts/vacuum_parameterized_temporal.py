"""Direct propagation and channel-specific assessment of a verified certificate.

This kernel has no CLI or target authorization; future orchestration must supply
a committed run envelope. It preserves all requested grids/tolerances on failure.
"""
from fractions import Fraction as F
import hashlib
import json

import numpy as np

import vacuum_parameterized_certificate as certificates
import vacuum_semigroup as evolution
import vacuum_u1_design as u1
import vacuum_channel_contract as channels
import vacuum_time_windows as windows
from vacuum_angle_refined import angle_refined
from vacuum_certificate_run import angle_error_bounds, encode

TOLERANCES = ((1e-8, 1e-18), (1e-10, 1e-20))


def stop_before_evolution(output, status, reason):
    for rung in output['result']['rungs']:
        rung.update(status=status, reason=reason)
        for slot in rung['evolutions']:
            slot.update(status=status, reason=reason)
    output.update(status=status, reason=reason)
    return output


def run(certificate, grids, tolerances=TOLERANCES):
    grids, tolerances = list(grids), list(tolerances)
    if (not grids or any(isinstance(n, bool) or not isinstance(n, int) or n < 16 for n in grids)
            or len(set(grids)) != len(grids) or any(b <= a for a,b in zip(grids,grids[1:]))):
        raise ValueError('distinct increasing integer grids >=16 required')
    if (not tolerances or any(len(pair) != 2 or not np.isfinite(pair).all()
                             or min(pair) <= 0 for pair in tolerances)):
        raise ValueError('positive finite tolerance pairs required')
    output = {'status': 'unresolved', 'reason': 'not yet run',
              'target_execution_authorized': False, 'precision_status': 'not_assessed',
              'result': {'rungs': [{'nodes': n, 'status': 'pending', 'evolutions': [
                  {'rtol': r, 'atol': a, 'status': 'pending'} for r,a in tolerances]} for n in grids]}}
    rungs = output['result']['rungs']
    try:
        selected = certificates.verified_channels(certificate)
        if len(selected) != 2:
            return stop_before_evolution(output, 'unresolved', 'valid certificate has insufficient observable bounds')
        exact_times = list(map(F, certificate['times']))
        times = [float(t) for t in exact_times]
        if (len(times) < 2 or exact_times[0] != 0 or not np.isfinite(times).all()
                or any(F(t) != exact for t,exact in zip(times,exact_times))):
            raise ValueError('certificate must use exact binary64 sample times starting at zero')
        reference = certificate['result']
        if reference['correlations'] is None:
            return stop_before_evolution(output, 'unresolved', 'valid correlation certificate remains unresolved')
        correlations = windows.numeric(reference['correlations'])
        vacuum = windows.numeric(reference['vacuum'])
        theory = certificate['theory']
        g, eta = float(F(certificate['g'])), float(F(certificate['eta']))
        if not np.isfinite([g,eta]).all():
            raise ValueError('model coordinates not finite in numerical representation')
        output['result'].update(theory=theory, g=certificate['g'], eta=certificate['eta'],
            times=certificate['times'], channels=selected,
            certificate_sha256=hashlib.sha256(json.dumps(certificate,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        reason = 'certificate prerequisite failed: '+str(exc)
        return stop_before_evolution(output, 'failed', reason)
    for rung in rungs:
        try:
            n = rung['nodes']
            if theory == 'SU2':
                ground = angle_refined(g,eta,n)
                matrix, observables = evolution.angle_matrix(g,eta,n)
            else:
                ground = u1.angle(g,eta,n)
                matrix, observables = u1.periodic_matrix(g,eta,n)
            vectors = evolution.centered_vectors(ground['ground'],observables)
            rung['ground'] = ground
        except Exception as exc:
            reason = f'ground preparation failed: {type(exc).__name__}: {exc}'
            rung.update(status='failed', reason=reason)
            for slot in rung['evolutions']:
                slot.update(status='failed', reason=reason)
            continue
        for slot in rung['evolutions']:
            slot.update(propagation_status='pending', assessment_status='not_attempted')
            try:
                observed = evolution.propagate(matrix,ground['E0'],vectors,times,slot['rtol'],slot['atol'])
                slot['result'] = observed
                slot.update(propagation_status='completed', assessment_status='pending')
                # Every tolerance has its own bound; no successful result is silently substituted.
                error = angle_error_bounds(correlations,vacuum,[{'rung':n,'evolutions':[{'result':observed}]}])[0]
                slot['angle_error_bounds'] = error
                pairs = []
                slot['pairs'] = pairs
                for i in range(len(times)-1):
                    assessments = [channels.assess(selected[a]['certificate'],
                        correlations[i]['correlation'][a][a], correlations[i+1]['correlation'][a][a],
                        observed['correlations'][i][a][a], observed['correlations'][i+1][a][a],
                        exact_times[i+1]-exact_times[i]) for a in range(2)]
                    pairs.append({'sample_indices':[i,i+1], 'times':exact_times[i:i+2],
                                  'observables':assessments})
                slot.update(status='completed',assessment_status='completed',result=observed,angle_error_bounds=error,pairs=pairs)
            except Exception as exc:
                if slot['propagation_status'] == 'completed':
                    slot['assessment_status'] = 'failed'
                else:
                    slot['propagation_status'] = 'failed'
                slot.update(status='failed',reason=f'{type(exc).__name__}: {exc}')
        rung['status'] = 'completed' if all(s['status']=='completed' for s in rung['evolutions']) else 'failed'
        if rung['status'] == 'failed':
            rung['reason'] = 'one or more requested evolutions failed; all slots retained'
    output['status'] = 'completed' if all(r['status']=='completed' for r in rungs) else 'failed'
    output['reason'] = ('requested propagation and sampled assessment completed' if output['status']=='completed'
                        else 'one or more requested grids/tolerances failed; partial evidence retained')
    return encode(output)
