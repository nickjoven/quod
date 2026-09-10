"""Replay stored temporal error/window arithmetic without solving an evolution.

This checks consistency of recorded evidence, not execution authenticity or a
standalone BDF error theorem. Failed and unresolved requests remain explicit.
"""
from fractions import Fraction as F
import hashlib
import json

import numpy as np

import vacuum_parameterized_temporal as temporal
import vacuum_parameterized_scalar as scalar


def encoded(value):
    return json.dumps(temporal.encode(value),sort_keys=True,separators=(',',':'),allow_nan=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reason(record):
    require(isinstance(record.get('reason'),str) and bool(record['reason'].strip()),
            'failed/unresolved request needs a reason')


def replay(certificate, output, grids, tolerances):
    """Return recomputed common pairs; reject discrepancies with stored evidence."""
    encoded(output)  # nonfinite data cannot enter a successful replay
    grids=scalar.ladder(grids,16,'grids')
    tolerances=[list(t) for t in tolerances]
    require(bool(tolerances) and all(len(t)==2 and np.isfinite(t).all() and min(t)>0
                                   for t in tolerances),'invalid tolerance request')
    selected=temporal.certificates.verified_channels(certificate)
    require(output['target_execution_authorized'] is False and
            output['precision_status']=='not_assessed','unexpected authority or precision claim')
    result=output['result']
    rungs=result['rungs']
    require([r['nodes'] for r in rungs]==grids,'grid request accounting mismatch')
    for rung in rungs:
        require([[s['rtol'],s['atol']] for s in rung['evolutions']]==tolerances,
                'tolerance request accounting mismatch')
    exact_times=list(map(F,certificate['times']))
    clock_ok=(len(exact_times)>=2 and exact_times[0]==0 and
              all(np.isfinite(float(t)) and F(float(t))==t for t in exact_times))
    unavailable=('unresolved' if len(selected)!=2 else 'failed' if not clock_ok else
                 'unresolved' if certificate['result']['correlations'] is None else None)
    if unavailable:
        require(output['status']==unavailable,'incorrect prerequisite outcome')
        reason(output)
        for rung in rungs:
            require(rung['status']==unavailable,'incorrect skipped grid status'); reason(rung)
            for slot in rung['evolutions']:
                require(slot['status']==unavailable and 'result' not in slot,
                        'skipped propagation has a result or incorrect status'); reason(slot)
        return {'status':'verified','stage_status':unavailable,'common_sample_pairs':[],
                'scope':'prerequisite and request accounting only'}
    require(all(encoded(result[k])==encoded(certificate[k]) for k in ('theory','g','eta','times')),
            'certificate coordinates or clock mismatch')
    require(result['certificate_sha256']==hashlib.sha256(encoded(certificate).encode()).hexdigest(),
            'certificate digest mismatch')
    require(encoded(result['channels'])==encoded(selected),'stored channel mismatch')
    correlations=temporal.windows.numeric(certificate['result']['correlations'])
    vacuum=temporal.windows.numeric(certificate['result']['vacuum'])
    common=[]
    for rung in rungs:
        n=rung['nodes']
        if 'ground' not in rung:
            require(rung['status']=='failed','missing ground without failure'); reason(rung)
            for slot in rung['evolutions']:
                require(slot['status']=='failed' and 'result' not in slot,
                        'missing ground with successful propagation'); reason(slot)
            continue
        for slot in rung['evolutions']:
            require(slot['status'] in ('completed','failed'),'nonterminal evolution')
            if slot['status']=='failed':
                reason(slot)
            propagated=slot['propagation_status']=='completed'
            if not propagated:
                require(slot['status']=='failed' and slot['propagation_status']=='failed'
                        and slot['assessment_status']=='not_attempted' and 'result' not in slot,
                        'inconsistent failed propagation')
                continue
            observed=slot['result']
            values=np.asarray(observed['correlations'],dtype=float)
            require(values.shape==(len(exact_times),2,2) and np.isfinite(values).all(),
                    'invalid observed correlation matrix')
            require(encoded([observed['rtol'],observed['atol']])==encoded([slot['rtol'],slot['atol']]),
                    'observed propagation tolerance mismatch')
            require(observed['integration_error_bound'] is None,'unsupported standalone integration bound')
            error=temporal.angle_error_bounds(correlations,vacuum,[{'rung':n,'evolutions':[{'result':observed}]}])[0]
            pairs=[]
            for i in range(len(exact_times)-1):
                assessments=[temporal.channels.assess(selected[a]['certificate'],
                    correlations[i]['correlation'][a][a],correlations[i+1]['correlation'][a][a],
                    observed['correlations'][i][a][a],observed['correlations'][i+1][a][a],
                    exact_times[i+1]-exact_times[i]) for a in range(2)]
                pairs.append({'sample_indices':[i,i+1],'times':exact_times[i:i+2],
                              'observables':assessments})
            if 'angle_error_bounds' in slot:
                require(encoded(slot['angle_error_bounds'])==encoded(error),'stored correlation error mismatch')
            if 'pairs' in slot:
                require(len(slot['pairs'])<=len(pairs) and
                        encoded(slot['pairs'])==encoded(pairs[:len(slot['pairs'])]),'stored window mismatch')
            if slot['status']=='completed':
                require(slot['assessment_status']=='completed' and 'angle_error_bounds' in slot
                        and len(slot.get('pairs',[]))==len(pairs),'completed assessment missing evidence')
                if rung is rungs[-1] and slot is rung['evolutions'][-1]:
                    common=[p['sample_indices'] for p in pairs if all(o['window']['qualifies'] for o in p['observables'])]
            else:
                require(slot['assessment_status']=='failed','inconsistent failed assessment')
        expected='completed' if all(s['status']=='completed' for s in rung['evolutions']) else 'failed'
        require(rung['status']==expected,'grid outcome contradicts requested evolutions')
        if expected=='failed':
            reason(rung)
    expected='completed' if all(r['status']=='completed' for r in rungs) else 'failed'
    require(output['status']==expected,'stage outcome contradicts requested grids')
    if expected=='failed':
        reason(output)
        common=[]
    return {'status':'verified','stage_status':expected,'common_sample_pairs':common,
            'scope':'stored correlation error and sampled-window arithmetic; propagation not rerun or authenticated'}


def verify(certificate, output, grids, tolerances):
    try:
        return replay(certificate,output,grids,tolerances)
    except (KeyError,TypeError,ValueError,ArithmeticError,IndexError) as exc:
        return {'status':'invalid','reason':f'{type(exc).__name__}: {exc}','common_sample_pairs':[]}
