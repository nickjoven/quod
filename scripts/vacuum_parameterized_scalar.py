"""Parameterized representation comparison; no target-run entry point.

Agreement is a diagnostic. Certified scalar accuracy is assessed separately
against the coordinate-bound infinite-model certificate.
"""
from fractions import Fraction as F
import json

import numpy as np

import vacuum_development as su2
import vacuum_refinement as refinement
import vacuum_u1_design as u1
from vacuum_u1_design_run import validate as validate_u1
from vacuum_angle_refined import angle_refined
from vacuum_certificate_run import encode


def ladder(values, minimum, name):
    values = list(values)
    if (not values or any(isinstance(v,bool) or not isinstance(v,int) or v < minimum for v in values)
            or any(b <= a for a,b in zip(values,values[1:]))):
        raise ValueError(f'{name} must be strictly increasing integers >= {minimum}')
    return values


def spectral_consistency(record):
    """Check recorded sum rules; tolerance is a consistency check, not a certificate."""
    weights=np.asarray(record['weights'],dtype=float)
    cross=np.asarray(record['cross_weights'],dtype=float)
    covariance=np.asarray(record['covariance'],dtype=float)
    omitted=np.asarray(record['unrepresented_covariance'],dtype=float)
    moments=np.asarray(record['moments'],dtype=float)
    if (weights.ndim!=2 or weights.shape[1]!=2 or cross.shape!=(len(weights),)
            or covariance.shape!=(2,2) or omitted.shape!=(2,2) or moments.shape!=(5,)):
        raise ValueError('spectral sum-rule shape mismatch')
    if not all(np.isfinite(v).all() for v in (weights,cross,covariance,omitted,moments)):
        raise ValueError('nonfinite spectral sum-rule evidence')
    if (weights<0).any():
        raise ValueError('negative spectral weight')
    represented=np.array([[weights[:,0].sum(),cross.sum()],
                          [cross.sum(),weights[:,1].sum()]])
    errors={
        'sum_rule':float(np.max(abs(represented+omitted-covariance))),
        'cross_rank_one':float(np.max(abs(cross*cross-weights[:,0]*weights[:,1]),initial=0)),
        'covariance_symmetry':float(np.max(abs(covariance-covariance.T))),
        'omitted_symmetry':float(np.max(abs(omitted-omitted.T))),
        'moment_covariance':float(np.max(abs(np.array([covariance[0,0],covariance[1,1],covariance[0,1]])-moments[2:]))),
        'moment_redundancy':float(abs(moments[2]-(moments[1]-moments[0]**2))),
        'omitted_psd':float(max(0,-np.linalg.eigvalsh((omitted+omitted.T)/2)[0]))}
    if 'observable_projection_tail_gram' in record:
        tail=np.asarray(record['observable_projection_tail_gram'],dtype=float)
        if tail.shape!=(2,2) or not np.isfinite(tail).all():
            raise ValueError('invalid padded projection tail')
        errors['full_basis_padding']=float(np.max(abs(omitted-tail)))
    if any(not np.isfinite(e) or e>1e-9 for e in errors.values()):
        raise ValueError('spectral consistency failed: '+str(errors))
    return {'status':'passed','absolute_consistency_tolerance':1e-9,
            'defects':errors,'precision_certificate':False}


def run(theory, g, eta, cutoffs, grids):
    g, eta = F(str(g)), F(str(eta))
    if theory not in ('SU2','U1') or g <= 0 or eta < 0:
        raise ValueError('valid theory, positive g and nonnegative eta required')
    cutoffs, grids = ladder(cutoffs,4,'cutoffs'), ladder(grids,16,'grids')
    gf, ef = float(g), float(eta)
    if not np.isfinite([gf,ef]).all():
        raise ValueError('coordinates must be finite in numerical representation')
    methods = [('character' if theory=='SU2' else 'fourier', cutoffs,
                su2.character if theory=='SU2' else u1.fourier),
               ('angle_fourth', grids, angle_refined if theory=='SU2' else u1.angle)]
    rungs = [{'method':name, 'rung':n, 'status':'pending'} for name,sizes,_ in methods for n in sizes]
    out = {'status':'unresolved', 'reason':'not yet run', 'target_execution_authorized':False,
           'precision_status':'not_assessed', 'result': {'theory':theory,'g':str(g),'eta':str(eta),
            'rungs':rungs,'final':None,'cross_representation_difference':None,
            'cross_representation_agreement':None,'comparison_status':'not_attempted'}}
    validate = refinement.validate_record if theory=='SU2' else validate_u1
    for slot in rungs:
        solver = next(solver for name,_,solver in methods if name==slot['method'])
        try:
            record = solver(gf,ef,slot['rung'])
            # Reject non-JSON numerical data before inserting it into a report.
            json.dumps(record,allow_nan=False)
            slot['result'] = record
            validate(record)
            slot['spectral_consistency'] = spectral_consistency(record)
            slot['status'] = 'completed'
        except Exception as exc:
            slot.update(status='failed', reason=f'{type(exc).__name__}: {exc}')
    final = [next(s for s in rungs if s['method']==name and s['rung']==sizes[-1])
             for name,sizes,_ in methods]
    if all(s['status']=='completed' for s in final):
        a,b = [s['result'] for s in final]
        out['result']['final'] = {s['method']:s['result'] for s in final}
        try:
            diff = su2.differences(a,b) if theory=='SU2' else u1.differences(a,b)
            json.dumps(diff,allow_nan=False)
            agrees = refinement.finite_goal(diff) if theory=='SU2' else u1.within_goal(diff)
            out['result'].update(cross_representation_difference=diff,
                cross_representation_agreement=agrees,comparison_status='completed')
        except Exception as exc:
            out['result'].update(comparison_status='failed',comparison_reason=f'{type(exc).__name__}: {exc}')
    if out['result']['comparison_status']=='failed':
        out.update(status='failed',reason='scalar comparison failed; completed solver evidence retained')
    elif any(s['status']=='failed' for s in rungs):
        out.update(status='failed',reason='one or more requested representation rungs failed; partial evidence retained')
    else:
        out.update(status='completed',reason='all requested scalar representations completed; agreement is diagnostic')
    return encode(out)
