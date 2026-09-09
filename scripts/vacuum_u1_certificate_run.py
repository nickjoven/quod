"""Fixed U(1) parity certificate run; exact endpoints and even-observable bounds."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import eigh_tridiagonal

import vacuum_certificate_run as shared
import vacuum_certified as common
import vacuum_development as baseline
import vacuum_u1_certified as certified
import vacuum_u1_run as development

TAU=(0.,.125,.25,.5,1.,2.,4.,8.,12.,16.,20.,24.)
SOURCES=(*shared.SOURCES,*development.SOURCES,'scripts/vacuum_u1_certified.py','scripts/vacuum_u1_certificate_run.py')


def source_hashes():
    return {p:hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest() for p in SOURCES}


def calculate(g,cutoff,times):
    d,s,_,_=certified.parameters(g,1,cutoff,'even')
    _,ve=eigh_tridiagonal(np.asarray(d,dtype=float),-np.sqrt(np.asarray(s,dtype=float)),
                          select='i',select_range=(0,3))
    vectors=np.empty((4,2*cutoff+1))
    vectors[:,cutoff]=ve[0]
    vectors[:,cutoff+1:]=ve[1:].T/np.sqrt(2)
    vectors[:,:cutoff]=vectors[:,cutoff+1:][:,::-1]
    even=certified.enclosures(g,1,cutoff,'even')
    odd=certified.enclosures(g,1,cutoff,'odd',count=1)
    if not certified.verify(g,1,cutoff,'even',even) or not certified.verify(g,1,cutoff,'odd',odd):
        raise ValueError('exact parity endpoint verification failed')
    bounds=[certified.vector_bound(g,1,v,k,even) for k,v in enumerate(vectors)]
    overlaps,vacuum=certified.observables(vectors,bounds)
    parity=certified.gap_fields(even,odd)
    correlations=common.correlation_intervals(even,overlaps,vacuum,times) if parity['even_ground_below_odd_certified'] else None
    even_gaps=[(e['lower']-even[0]['upper'],e['upper']-even[0]['lower']) for e in even[1:4]]
    all_gaps=even_gaps+([parity['full_gap_interval']] if parity['full_gap_interval'] is not None else [])
    gap_ok=len(all_gaps)==4 and all(lo>0 and (hi-lo)/(2*lo)<=F(1,10**6) for lo,hi in all_gaps)
    moments=None if vacuum is None else [*vacuum['raw_moments'][:2],vacuum['covariance'][0][0],
                                         vacuum['covariance'][1][1],vacuum['covariance'][0][1]]
    moment_ok=moments is not None and all((hi-lo)/2<=F(1,10**6) for lo,hi in moments)
    return {'cutoff':cutoff,'even_enclosures':even,'odd_enclosures':odd,'parity':parity,
            'candidate_vectors_hex':[[float(v).hex() for v in row] for row in vectors],
            'vector_bounds':bounds,'overlaps':overlaps,'vacuum':vacuum,'correlations':correlations,
            'first_three_even_gap_intervals':even_gaps,'scalar_budget_met':bool(gap_ok and moment_ok),
            'first_even_overlap_certified':None if overlaps is None else [o['nonzero_certified'] for o in overlaps[0]],
            'bound_status':'bounded' if correlations is not None else 'unresolved'}


def decode_eigen(rows):
    return [{k:F(v) if k!='index' else v for k,v in r.items()} for r in rows]


def verify_result(g,result,times):
    even,odd=decode_eigen(result['even_enclosures']),decode_eigen(result['odd_enclosures'])
    cutoff=result['cutoff']
    if not certified.verify(g,1,cutoff,'even',even) or not certified.verify(g,1,cutoff,'odd',odd):
        return False
    vectors=[[float.fromhex(v) for v in row] for row in result['candidate_vectors_hex']]
    if len(vectors)!=4 or any(len(v)!=2*cutoff+1 for v in vectors):
        return False
    bounds=[certified.vector_bound(g,1,v,k,even) for k,v in enumerate(vectors)]
    overlaps,vacuum=certified.observables(vectors,bounds)
    parity=certified.gap_fields(even,odd)
    correlations=common.correlation_intervals(even,overlaps,vacuum,times) if parity['even_ground_below_odd_certified'] else None
    return all(result[key]==shared.encode(value) for key,value in (
        ('vector_bounds',bounds),('overlaps',overlaps),('vacuum',vacuum),('parity',parity),('correlations',correlations)))


def accounting(report):
    return (report['targets_run']==0 and baseline.coverage(report['targets'])
        and all(t['status']=='unrun' for t in report['targets'])
        and [c['g'] for c in report['cells']]==list(baseline.G_VALUES)
        and all(c['eta']==1 and c['partition']=='development'
            and [r['cutoff'] for r in c['rungs']]==list(baseline.CHARACTER_J)
            and all(r['status'] in ('completed','failure') for r in c['rungs']) for c in report['cells']))


def run(output):
    raw=(baseline.ROOT/'research/vacuum-spectrum/u1-development.json').read_bytes()
    source=json.loads(raw)
    if source['state']!='completed' or not development.accounting(source) or source['source_sha256']!=development.source_hashes():
        raise ValueError('incomplete or drifted U1 development evidence')
    start=time.monotonic()
    report={'schema_version':1,'state':'running','registered':False,'targets_run':0,'targets':source['targets'],
        'source_sha256':source_hashes(),'input_sha256':hashlib.sha256(raw).hexdigest(),
        'dimensionless_times':list(TAU),'time_convention':'tau divided by archived finest first EVEN gap; exact dyadic sampled times',
        'coordinate_convention':'exact declared decimal g; eta=1; U1 pilot normalization remains unverified',
        'cells':[{'g':g,'eta':1,'partition':'development','status':'pending',
            'rungs':[{'cutoff':k,'status':'pending'} for k in baseline.CHARACTER_J]} for g in baseline.G_VALUES],
        'limitations':['Parity-sector model certificates, not a registered field-theory result',
            'Exact integer/Fraction arithmetic and the documented Schur/residual arguments are trusted',
            'No U1 direct angle propagation or temporal qualification in this run',
            'No target selection or execution; source-pilot/registration and review remain outstanding']}

    def checkpoint(event,**fields):
        baseline.write_report(output,shared.encode(report))
        print(json.dumps({'event':event,'elapsed_seconds':time.monotonic()-start,**fields}),flush=True)

    checkpoint('started')
    for cell,prior in zip(report['cells'],source['cells']):
        times=[F(float(t)) for t in np.asarray(TAU)/prior['final']['fourier']['first_even_gap']]
        cell['times']=times
        cell['status']='running'
        for rung in cell['rungs']:
            rung['status']='running'
            checkpoint('rung_started',g=cell['g'],cutoff=rung['cutoff'])
            began=time.monotonic()
            try:
                result=calculate(cell['g'],rung['cutoff'],times)
                json.dumps(shared.encode(result),allow_nan=False)
                rung.update(status='completed',result=result)
            except Exception as exc:
                rung.update(status='failure',reason=f'{type(exc).__name__}: {exc}')
            rung['elapsed_seconds']=time.monotonic()-began
            checkpoint('rung_completed',g=cell['g'],cutoff=rung['cutoff'],status=rung['status'])
        cell['status']='failure' if any(r['status']=='failure' for r in cell['rungs']) else 'unresolved'
        checkpoint('cell_completed',g=cell['g'],status=cell['status'])
    report['accounting_pass']=accounting(report)
    report['source_unchanged_during_run']=source_hashes()==report['source_sha256']
    passed=report['accounting_pass'] and report['source_unchanged_during_run'] and all(c['status']!='failure' for c in report['cells'])
    report['state']='completed' if passed else 'instrument_failure'
    report['elapsed_seconds']=time.monotonic()-start
    checkpoint('completed',state=report['state'])
    return 0 if passed else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.name in ('u1-development.json','certificates.json','semigroup.json','late-times.json',
                           'development.json','refinement.json','preflight.json','time-windows.json','null-controls.json'):
        parser.error('output must not overwrite earlier evidence')
    raise SystemExit(run(args.output))
