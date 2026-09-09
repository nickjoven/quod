"""Fixed development U(1) parity and scalar convergence run; targets unavailable."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy

import vacuum_development as baseline
import vacuum_refinement as refinement
import vacuum_u1 as u1

SOURCES=('scripts/vacuum_u1.py','scripts/vacuum_u1_run.py',*refinement.SOURCES)


def source_hashes():
    return {p:hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest() for p in SOURCES}


def methods():
    return (('fourier',baseline.CHARACTER_J,u1.fourier),('angle',baseline.ANGLE_INTERIORS,u1.angle))


def accounting(report):
    expected=[(name,rung) for name,ladder,_ in methods() for rung in ladder]
    return (report['targets_run']==0 and baseline.coverage(report['targets'])
        and all(t['status']=='unrun' for t in report['targets'])
        and [c['g'] for c in report['cells']]==list(baseline.G_VALUES)
        and all(c['eta']==1 and c['partition']=='development'
            and [(r['method'],r['rung']) for r in c['rungs']]==expected
            and all(r['status'] in ('completed','failure') for r in c['rungs']) for c in report['cells']))


def validate(record):
    refinement.validate_record(record)
    for parity in ('even','odd'):
        energies=np.asarray(record[parity+'_energies'])
        if len(energies)<4 or not (np.diff(energies)>=0).all():
            raise ValueError('unordered parity spectrum')
    if record['full_gap']<=0 or record['first_even_gap']<=0 or record['first_odd_gap']<=0:
        raise ValueError('nonpositive development gap')
    expected=min(record['even_energies'][1],record['odd_energies'][0])-record['E0']
    if record['full_gap'] != expected:
        raise ValueError('full gap does not combine both parities')


def run(output):
    start=time.monotonic()
    report={'schema_version':1,'state':'running','registered':False,'targets_run':0,
        'targets':[{'id':r,'status':'unrun'} for r in baseline.target_ids()],
        'source_sha256':source_hashes(),
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'convention':'H=-g^2 d_theta^2-2 eta cos(theta)/g^2; Haar dtheta/(2pi); pilot convention unverified',
        'cells':[{'g':g,'eta':1,'partition':'development','status':'pending',
            'rungs':[{'method':name,'rung':rung,'status':'pending'} for name,ladder,_ in methods() for rung in ladder]}
            for g in baseline.G_VALUES],
        'limitations':['Fourier cutoff values are a declared development choice matching existing numeric ladder',
            'Even observable threshold is not the full odd gap; overlaps remain uncertified',
            'No U1 residual/truncation enclosures, direct semigroup, or qualified windows yet',
            'Source pilot and registration workflow unavailable; no target interface']}

    def checkpoint(event,**fields):
        baseline.write_report(output,report)
        print(json.dumps({'event':event,'elapsed_seconds':time.monotonic()-start,**fields}),flush=True)

    checkpoint('started')
    try:
        report['calibration']=u1.calibration()
    except Exception as exc:
        report['calibration']={'pass':False,'reason':f'{type(exc).__name__}: {exc}'}
    if not report['calibration']['pass']:
        report['state']='instrument_failure'
        checkpoint('calibration_failed')
        return 1
    for cell in report['cells']:
        cell['status']='running'
        previous,final={},{}
        for slot in cell['rungs']:
            name=slot['method']
            solver=next(s for method,_,s in methods() if method==name)
            slot['status']='running'
            checkpoint('rung_started',g=cell['g'],method=name,rung=slot['rung'])
            began=time.monotonic()
            try:
                record=solver(cell['g'],1,slot['rung'])
                validate(record)
                if name in previous:
                    record['adjacent_rung_difference']=u1.differences(record,previous[name])
                json.dumps(record,allow_nan=False)
                previous[name]=record
                final[name]=record
                slot.update(status='completed',result=baseline.compact(record))
            except Exception as exc:
                slot.update(status='failure',reason=f'{type(exc).__name__}: {exc}')
                previous.pop(name,None)
            slot['elapsed_seconds']=time.monotonic()-began
            checkpoint('rung_completed',g=cell['g'],method=name,rung=slot['rung'],status=slot['status'])
        cell['final']=final
        cell['status']='failure' if any(r['status']=='failure' for r in cell['rungs']) else 'unresolved'
        if cell['status']=='unresolved':
            cell['cross_method_difference']=u1.differences(final['angle'],final['fourier'])
            cell['scalar_agreement']=u1.within_goal(cell['cross_method_difference']) and all(
                u1.within_goal(final[m]['adjacent_rung_difference']) for m in ('angle','fourier'))
        checkpoint('cell_completed',g=cell['g'],status=cell['status'])
    report['accounting_pass']=accounting(report)
    report['source_unchanged_during_run']=source_hashes()==report['source_sha256']
    passed=report['accounting_pass'] and report['source_unchanged_during_run'] and all(c['status']!='failure' for c in report['cells'])
    report['state']='completed' if passed else 'instrument_failure'
    report['elapsed_seconds']=time.monotonic()-start
    checkpoint('completed',state=report['state'])
    return 0 if passed else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.name in ('development.json','refinement.json','preflight.json','semigroup.json','certificates.json',
                            'late-times.json','time-windows.json','evidence-audit.json','null-controls.json'):
        parser.error('output must not overwrite earlier evidence')
    return run(args.output)


if __name__=='__main__':
    raise SystemExit(main())
