"""Replay scalar records and representation comparisons without eigensolvers.

This validates stored arithmetic and request identity. Exact model accuracy is
still assessed against a separately verified coordinate-bound certificate.
"""
from fractions import Fraction as F
import json

import vacuum_parameterized_scalar as scalar


def encoded(value):
    return json.dumps(scalar.encode(value),sort_keys=True,separators=(',',':'),allow_nan=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonblank(value):
    return isinstance(value,str) and bool(value.strip())


def replay(theory,g,eta,cutoffs,grids,output):
    encoded(output)
    g,eta=F(str(g)),F(str(eta))
    require(theory in ('SU2','U1') and g>0 and eta>=0,'invalid model coordinate')
    cutoffs=scalar.ladder(cutoffs,4,'cutoffs'); grids=scalar.ladder(grids,16,'grids')
    require(output['target_execution_authorized'] is False and
            output['precision_status']=='not_assessed','unexpected authority or precision claim')
    result=output['result']
    require(result['theory']==theory and F(result['g'])==g and F(result['eta'])==eta,
            'scalar coordinate mismatch')
    basis='character' if theory=='SU2' else 'fourier'
    expected=[(method,n) for method,ns in ((basis,cutoffs),('angle_fourth',grids)) for n in ns]
    rungs=result['rungs']
    require([(r['method'],r['rung']) for r in rungs]==expected,'scalar request accounting mismatch')
    validator=scalar.refinement.validate_record if theory=='SU2' else scalar.validate_u1
    for slot in rungs:
        require(slot['status'] in ('completed','failed'),'nonterminal scalar rung')
        if slot['status']=='failed':
            require(nonblank(slot.get('reason')),'failed scalar rung needs a reason')
            continue  # malformed solver evidence is retained, never certified here
        record=slot['result']
        validator(record)
        require(encoded(slot['spectral_consistency'])==encoded(scalar.spectral_consistency(record)),
                'spectral consistency verdict mismatch')
        n=slot['rung']
        if theory=='SU2':
            method,key,length=('character','J',2*n+1) if slot['method']==basis else (
                'angle_dirichlet_fourth_order','interiors',n)
        else:
            method,key,length=('u1_fourier_even_odd','cutoff',2*n+1) if slot['method']==basis else (
                'u1_periodic_fourth_order','nodes',n)
            require(record['convention']==scalar.u1.CONVENTION,'U1 kinetic convention mismatch')
        require(record['method']==method and record[key]==n and len(record['ground'])==length,
                'stored method or representation size mismatch')
    finest=[rungs[len(cutoffs)-1],rungs[-1]]
    available=all(r['status']=='completed' for r in finest)
    comparison=result['comparison_status']
    agreement=None
    if not available:
        require(result['final'] is None and comparison=='not_attempted',
                'finest failure replaced by another record or comparison')
    else:
        require(encoded(result['final'])==encoded({r['method']:r['result'] for r in finest}),
                'final representations differ from requested finest rungs')
        require(comparison in ('completed','failed'),'missing final comparison outcome')
        if comparison=='failed':
            require(nonblank(result.get('comparison_reason')),'failed comparison needs a reason')
        else:
            a,b=[r['result'] for r in finest]
            difference=scalar.su2.differences(a,b) if theory=='SU2' else scalar.u1.differences(a,b)
            agreement=scalar.refinement.finite_goal(difference) if theory=='SU2' else scalar.u1.within_goal(difference)
            require(encoded(result['cross_representation_difference'])==encoded(difference),
                    'stored representation difference mismatch')
            require(result['cross_representation_agreement'] is agreement,'stored agreement flag mismatch')
    if comparison!='completed':
        require(result['cross_representation_difference'] is None and
                result['cross_representation_agreement'] is None,'failed/unattempted comparison has a success result')
    expected_status='failed' if comparison=='failed' or any(r['status']=='failed' for r in rungs) else 'completed'
    require(output['status']==expected_status,'scalar stage status contradicts requests')
    if expected_status=='failed':
        require(nonblank(output.get('reason')),'failed scalar stage needs a reason')
        agreement=None
    return {'status':'verified','stage_status':expected_status,'cross_representation_agreement':agreement,
            'scope':'stored scalar arithmetic and request identity; solver execution not authenticated; accuracy requires exact certificate'}


def verify(theory,g,eta,cutoffs,grids,output):
    try:
        return replay(theory,g,eta,cutoffs,grids,output)
    except (KeyError,TypeError,ValueError,ArithmeticError,IndexError) as exc:
        return {'status':'invalid','reason':f'{type(exc).__name__}: {exc}',
                'cross_representation_agreement':None}
