"""Independent U(1) angle evolution and certified even-gap window assessment."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy

import vacuum_certificate_run as shared
import vacuum_development as baseline
import vacuum_semigroup as evolution
import vacuum_time_windows as windows
import vacuum_u1_design as u1
import vacuum_u1_design_run as development
import vacuum_u1_design_certificate_run as certificates

TOLERANCES=((1e-8,1e-18),(1e-10,1e-20))
SOURCES=(*certificates.SOURCES,*windows.SOURCES,'scripts/vacuum_u1_design_semigroup_run.py')


def source_hashes():
    return {p:hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest() for p in SOURCES}


def load_inputs():
    reports,hashes={},{}
    for name in ('u1-design-development.json','u1-design-certificates.json'):
        raw=(baseline.ROOT/'research/vacuum-spectrum'/name).read_bytes()
        report=json.loads(raw)
        if report['state']!='completed' or [c['g'] for c in report['cells']]!=list(baseline.G_VALUES):
            raise ValueError('incomplete input manifest '+name)
        for path,expected in report['source_sha256'].items():
            if hashlib.sha256((baseline.ROOT/path).read_bytes()).hexdigest()!=expected:
                raise ValueError('input source drift '+path)
        reports[name],hashes[name]=report,hashlib.sha256(raw).hexdigest()
    if reports['u1-design-certificates.json']['input_sha256']!=hashes['u1-design-development.json']:
        raise ValueError('certificate input mismatch')
    return reports,hashes


def window_reference(cell):
    """Explicit adapter: effective-gap analysis references EVEN, never full, gaps."""
    final=cell['rungs'][-1]['result']
    if not final['parity']['even_ground_below_odd_certified'] or final['correlations'] is None:
        raise ValueError('even ground/correlation certificate unavailable')
    return {'g':cell['g'],'times':cell['times'],'rungs':[{'result':{
        'correlations':final['correlations'],
        'first_three_gap_intervals':final['first_three_even_gap_intervals'],
        'first_gap_overlap_certified':final['first_even_overlap_certified']}}]}


def calibration():
    n,g=64,.5
    matrix,obs=u1.periodic_matrix(g,0,n)
    ground=np.full(n,1/np.sqrt(n))
    vectors=evolution.centered_vectors(ground,obs)
    times=np.asarray(certificates.TAU)/(4*g*g)
    actual=evolution.propagate(matrix,0.,vectors,times,1e-10,1e-13)
    h=2*np.pi/n
    lam=4*np.sin(np.array([1,2])*h/2)**2/h**2
    gaps=4*g*g*(lam+h*h*lam*lam/12)
    expected=np.zeros((len(times),2,2))
    expected[:,0,0]=.5*np.exp(-gaps[0]*times)
    expected[:,1,1]=.125*np.exp(-gaps[1]*times)
    error=float(np.max(abs(np.asarray(actual['correlations'])-expected)))
    return {'pass':error<1e-9,'free_correlation_max_absolute_error':error,
            'scope':'analytic finite periodic U1 correlation, including both Haar variances'}


def accounting(report):
    return (report['targets_run']==0 and baseline.coverage(report['targets'])
        and all(t['status']=='unrun' for t in report['targets'])
        and [c['g'] for c in report['cells']]==list(baseline.G_VALUES)
        and all(c['eta']==1 and c['partition']=='development'
            and [r['rung'] for r in c['rungs']]==list(baseline.ANGLE_INTERIORS)
            and all(r['status'] in ('completed','failure')
                and [(e['rtol'],e['atol']) for e in r['evolutions']]==list(TOLERANCES)
                and all(e['status'] in ('completed','failure') for e in r['evolutions'])
                for r in c['rungs']) for c in report['cells']))


def run(output):
    inputs,hashes=load_inputs()
    start=time.monotonic()
    report={'schema_version':1,'state':'running','theory':'U1','registered':False,'targets_run':0,
        'targets':inputs['u1-design-development.json']['targets'],'input_sha256':hashes,'source_sha256':source_hashes(),
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'dimensionless_times':list(certificates.TAU),'observable_gap_reference':'first_even_gap',
        'cells':[{'g':g,'eta':1,'partition':'development','status':'pending',
            'rungs':[{'method':'angle_fourth','rung':n,'status':'pending',
                'evolutions':[{'rtol':r,'atol':a,'status':'pending'} for r,a in TOLERANCES]}
                for n in baseline.ANGLE_INTERIORS]} for g in baseline.G_VALUES],
        'limitations':['Recovered design coefficient 4g^2; original pilot code remains unavailable',
            'Same model-certificate trusted base; no field-theory or registered target inference',
            'Only sampled pairs are assessed; no interpolation to unsampled windows',
            'Finest periodic ground is reused explicitly from the development archive']}

    def checkpoint(event,**fields):
        baseline.write_report(output,shared.encode(report))
        print(json.dumps({'event':event,'elapsed_seconds':time.monotonic()-start,**fields}),flush=True)

    checkpoint('started')
    try:
        report['calibration']=calibration()
    except Exception as exc:
        report['calibration']={'pass':False,'reason':f'{type(exc).__name__}: {exc}'}
    if not report['calibration']['pass']:
        report['state']='instrument_failure'
        checkpoint('calibration_failed')
        return 1
    for i,cell in enumerate(report['cells']):
        cell['status']='running'
        source=inputs['u1-design-certificates.json']['cells'][i]
        final=source['rungs'][-1]['result']
        cell['times']=[float(F(t)) for t in source['times']]
        cell['full_gap_interval']=final['parity']['full_gap_interval']
        cell['first_even_gap_interval']=final['parity']['first_even_gap_interval']
        try:
            reference=window_reference(source)
        except Exception as exc:
            for rung in cell['rungs']:
                rung.update(status='failure',reason=str(exc))
                for slot in rung['evolutions']:
                    slot.update(status='failure',reason='certificate prerequisite unavailable')
            cell['status']='failure'
            checkpoint('cell_failed',g=cell['g'])
            continue
        prior=inputs['u1-design-development.json']['cells'][i]['final']
        spectral=evolution.spectral_correlations(prior['fourier'],cell['times'])
        for rung in cell['rungs']:
            rung['status']='running'
            checkpoint('ground_started',g=cell['g'],nodes=rung['rung'])
            began=time.monotonic()
            try:
                cached=rung['rung']==baseline.ANGLE_INTERIORS[-1]
                record=prior['angle'] if cached else u1.angle(cell['g'],1,rung['rung'])
                development.validate(record)
                if record['nodes']!=rung['rung']:
                    raise ValueError('ground grid mismatch')
                matrix,obs=u1.periodic_matrix(cell['g'],1,rung['rung'])
                vectors=evolution.centered_vectors(record['ground'],obs)
                rung['ground_origin']='archived_u1_development' if cached else 'fresh_parity_solve'
                rung['ground_elapsed_seconds']=time.monotonic()-began
                rung['centered_parity_defect']=float(np.max(abs(vectors-vectors[(-np.arange(rung['rung']))%rung['rung']])))
            except Exception as exc:
                rung.update(status='failure',reason=f'{type(exc).__name__}: {exc}')
                for slot in rung['evolutions']:
                    slot.update(status='failure',reason='ground preparation failed')
                checkpoint('ground_failed',g=cell['g'],nodes=rung['rung'])
                continue
            for slot in rung['evolutions']:
                slot['status']='running'
                checkpoint('evolution_started',g=cell['g'],nodes=rung['rung'],rtol=slot['rtol'])
                began=time.monotonic()
                try:
                    result=evolution.propagate(matrix,record['E0'],vectors,cell['times'],slot['rtol'],slot['atol'])
                    json.dumps(result,allow_nan=False)
                    slot.update(status='completed',result=result)
                except Exception as exc:
                    slot.update(status='failure',reason=f'{type(exc).__name__}: {exc}')
                slot['elapsed_seconds']=time.monotonic()-began
                checkpoint('evolution_completed',g=cell['g'],nodes=rung['rung'],status=slot['status'])
            rung['status']='completed' if all(e['status']=='completed' for e in rung['evolutions']) else 'failure'
            if rung['status']=='completed':
                coarse,fine=[e['result']['correlations'] for e in rung['evolutions']]
                rung['tolerance_difference']=evolution.comparison(coarse,fine,prior['fourier']['covariance'])
                rung['fourier_difference']=evolution.comparison(fine,spectral,prior['fourier']['covariance'])
        complete={**cell,'rungs':[r for r in cell['rungs'] if r['status']=='completed']}
        cell['window_assessment']=windows.assess_cell(reference,complete)
        cell['angle_error_bounds']=shared.angle_error_bounds(windows.numeric(final['correlations']),
            windows.numeric(final['vacuum']),complete['rungs'])
        cell['status']='unresolved' if all(r['status']=='completed' for r in cell['rungs']) else 'failure'
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
    if args.output.resolve() != (baseline.ROOT/'research/vacuum-spectrum/u1-design-semigroup.json').resolve():
        parser.error('use the dedicated u1-design-semigroup.json output')
    raise SystemExit(run(args.output))
