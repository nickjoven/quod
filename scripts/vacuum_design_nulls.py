"""Exact analytic null families specified by the recovered experiment draft."""
import argparse
from fractions import Fraction as F
import hashlib
from pathlib import Path

import numpy as np
import vacuum_certificate_run as shared
import vacuum_development as baseline
import vacuum_intervals as interval
import vacuum_null_controls as previous
import vacuum_time_windows as windows

EPSILONS=(F(1),F(1,2),F(1,8),F(1,32))
SOURCES=(*windows.SOURCES,'scripts/vacuum_null_controls.py','scripts/vacuum_design_nulls.py',
 'research/vacuum-spectrum/design-bundle/notes/ym_vacuum_gap_registration_draft.md')


def tensor(epsilon):
    epsilon=F(epsilon)
    if not 0<epsilon<=1:
        raise ValueError('epsilon in (0,1] required')
    unit=np.eye(2,dtype=object)
    x=np.array([[0,1],[1,0]],dtype=object)
    matrix=np.kron(unit-x,unit)+epsilon*np.kron(unit,unit-x)
    vectors=[np.array([1,b,a,a*b],dtype=object)/F(2) for a,b in ((1,1),(1,-1),(-1,1),(-1,-1))]
    energies=[F(0),2*epsilon,F(2),2+2*epsilon]
    checks=[all(matrix@q==energy*q) and sum(v*v for v in q)==1 for q,energy in zip(vectors,energies)]
    return {'epsilon':epsilon,'matrix':matrix.tolist(),'energies':energies,
            'ground':vectors[0].tolist(),'eigenpair_checks':checks,'full_gap':2*epsilon}


def exponential_correlation(time):
    time=F(time)
    if time<0:
        raise ValueError('nonnegative time required')
    return F(1)/(1+time)


def mass_below(epsilon):
    epsilon=F(epsilon)
    if epsilon<=0:
        raise ValueError('positive epsilon required')
    lo,hi=interval.exp_negative(epsilon)
    return 1-hi,1-lo


def raw_correlation(time,mean=F(3),gap=F(2)):
    lo,hi=interval.exp_negative(F(time)*gap)
    return mean*mean+lo,mean*mean+hi


def evaluate():
    tensors=[tensor(e) for e in EPSILONS]
    hidden=[{'epsilon':e,**previous.measure([0,e,1],[0,0,1])} for e in EPSILONS]
    times=[F(0),F(1),F(4),F(16),F(64)]
    gapless=[windows.slope_interval((exponential_correlation(t),)*2,
        (exponential_correlation(t+1),)*2,F(1)) for t in times]
    raw=[windows.slope_interval(raw_correlation(t),raw_correlation(t+1),F(1)) for t in times]
    centered=[windows.slope_interval(interval.exp_negative(2*t),interval.exp_negative(2*(t+1)),F(1)) for t in times]
    masses=[mass_below(e) for e in EPSILONS]
    checks={
        'specified_tensor_eigenpairs':all(all(r['eigenpair_checks']) for r in tensors),
        'tensor_fixed_ground':all(r['ground']==[F(1,2)]*4 for r in tensors),
        'tensor_full_gap':all(r['full_gap']==2*e for r,e in zip(tensors,EPSILONS)),
        'specified_hidden_family':all(r['first_ordered_gap']==r['epsilon'] and r['observed_threshold']==1
            and r['support']==[{'gap':F(1),'weight':F(1)}] for r in hidden),
        'exponential_measure_normalized':exponential_correlation(0)==1,
        'exponential_measure_low_mass':all(0<lo<=hi<1 for lo,hi in masses),
        'gapless_positive_decreasing_slopes':all(0<lo<=hi for lo,hi in gapless)
            and all(b[1]<a[0] for a,b in zip(gapless,gapless[1:])),
        'raw_positive_decreasing_slopes':all(0<lo<=hi<2 for lo,hi in raw)
            and all(b[1]<a[0] for a,b in zip(raw,raw[1:])),
        'centered_single_mode_gap':all(lo<=2<=hi for lo,hi in centered)}
    mutants={
        'hidden_full_gap_as_probe_threshold':hidden[-1]['first_ordered_gap']!=hidden[-1]['observed_threshold'],
        'raw_as_connected':raw[-1][1]<centered[-1][0],
        'positive_floor_for_exponential_measure':mass_below(F(1,64))[0]>0,
        'tensor_omit_epsilon_scaling':tensors[-1]['energies'][1]!=2}
    return {'schema_version':1,'state':'completed','registered':False,'targets_run':0,
        'targets':[{'id':t,'status':'unrun'} for t in baseline.target_ids()],
        'checks':checks,'mutants_rejected':mutants,'pass':all(checks.values()) and all(mutants.values()),
        'tensor':tensors,'hidden':hidden,'times':times,'gapless_effective_gap_intervals':gapless,
        'raw_effective_gap_intervals':raw,'centered_effective_gap_intervals':centered,
        'low_energy_mass_intervals':masses,
        'analytic_limits':{'gapless':'C(t)=1/(1+t); support reaches zero; slopes tend to zero',
            'raw':'G(t)=9+exp(-2t); raw slopes tend to zero while connected slopes equal 2',
            'tensor':'ground fixed for epsilon>0; gap 2 epsilon tends to zero'},
        'scope':'specified analytic controls, not target solver runs or a field-theory statement',
        'source_sha256':{p:hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest() for p in SOURCES}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve()!=(baseline.ROOT/'research/vacuum-spectrum/design-nulls.json').resolve():
        parser.error('use the dedicated design-nulls.json output')
    result=evaluate()
    baseline.write_report(args.output,shared.encode(result))
    print('pass' if result['pass'] else 'failure')
    raise SystemExit(0 if result['pass'] else 1)
