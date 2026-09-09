"""Planning scenarios from development timings; no target solvers are called."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path

import vacuum_development as baseline
import vacuum_certificate_run as shared

DIRECTORY=baseline.ROOT/'research/vacuum-spectrum'
INPUTS={'SU2':('refinement.json','certificates.json','late-times.json'),
        'U1':('u1-design-development.json','u1-design-certificates.json','u1-design-semigroup.json')}


def load_inputs():
    return {name:json.loads((DIRECTORY/name).read_text()) for names in INPUTS.values() for name in names}


def duration(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('finite nonnegative measured duration required')
    return F(value)


def estimate(reports):
    if set(reports)!={name for names in INPUTS.values() for name in names}:
        raise ValueError('timing input manifest differs')
    result=[]
    for theory,names in INPUTS.items():
        scalar,cert,temporal=[reports[n] for n in names]
        for report in (scalar,cert,temporal):
            if (report['state']!='completed' or report['registered'] is not False or report['targets_run']!=0
                or not baseline.coverage(report['targets']) or any(t['status']!='unrun' for t in report['targets'])
                or [c['g'] for c in report['cells']]!=list(baseline.G_VALUES)):
                raise ValueError('incomplete or nondevelopment timing input')
            for p,h in report['source_sha256'].items():
                if hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest()!=h:
                    raise ValueError('timing input source drift')
        target_count=sum(t['id'].startswith(theory+':') for t in scalar['targets'])
        stages={'representations':[],'certificates':[],'direct_evolution_and_ground':[]}
        for s,c,t in zip(scalar['cells'],cert['cells'],temporal['cells']):
            rungs=[r for r in s['rungs'] if r['method'] in ('character','angle_fourth','fourier','angle')]
            if len(rungs)!=9 or len(c['rungs'])!=5 or len(t['rungs'])!=4:
                raise ValueError('missing timing requests')
            if any(r['status']!='completed' for r in [*rungs,*c['rungs'],*t['rungs']]):
                raise ValueError('failed timing requests')
            stages['representations'].append(sum((duration(r['elapsed_seconds']) for r in rungs),F(0)))
            stages['certificates'].append(sum((duration(r['elapsed_seconds']) for r in c['rungs']),F(0)))
            elapsed=F(0)
            for rung in t['rungs']:
                if len(rung['evolutions'])!=2 or any(e['status']!='completed' for e in rung['evolutions']):
                    raise ValueError('missing or failed evolution timing')
                elapsed+=duration(rung['ground_elapsed_seconds'])
                elapsed+=sum((duration(e['elapsed_seconds']) for e in rung['evolutions']),F(0))
            stages['direct_evolution_and_ground'].append(elapsed)
        summaries={}
        for stage,values in stages.items():
            mean=sum(values,F(0))/len(values)
            summaries[stage]={'mean_development_cell_seconds':mean,'slowest_development_cell_seconds':max(values),
                'target_count_times_mean_seconds':target_count*mean,
                'target_count_times_slowest_seconds':target_count*max(values)}
        mean_total=sum((s['target_count_times_mean_seconds'] for s in summaries.values()),F(0))
        slow_total=sum((s['target_count_times_slowest_seconds'] for s in summaries.values()),F(0))
        result.append({'theory':theory,'target_count_for_planning_only':target_count,'stages':summaries,
            'planned_counts':{'representation_requests':9*target_count,'certificate_rungs':5*target_count,
                              'evolutions':8*target_count},
            'scenario_seconds':{'mean_development':mean_total,'slowest_development':slow_total,
                                'four_times_slowest_stress_assumption':4*slow_total}})
    return {'schema_version':1,'state':'planning_only','registered':False,'targets_run':0,
        'target_execution_authorized':False,'theories':result,
        'basis':'sum measured work durations; no target solver or target numerical observation',
        'limitations':['Scenarios are not runtime bounds or precision guarantees',
            'The 4x stress factor is an explicit planning assumption, not a measured confidence level',
            'Checkpoint I/O, review, registration and failure repair are outside measured-work estimates',
            'Only eta=1 development timings are measured; eta=0 and .5 costs and overlap windows remain unverified',
            'Failure and unresolved outcomes must be retained; no window is selected by this estimate'],
        'input_sha256':{name:hashlib.sha256((DIRECTORY/name).read_bytes()).hexdigest() for name in reports},
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve()!=(DIRECTORY/'target-cost-plan.json').resolve():
        parser.error('use the dedicated target-cost-plan.json output')
    result=estimate(load_inputs())
    baseline.write_report(args.output,shared.encode(result))
    print(json.dumps({r['theory']:{k:round(float(v),2) for k,v in r['scenario_seconds'].items()} for r in result['theories']}))
