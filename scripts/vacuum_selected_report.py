"""Post-run presentation of frozen evidence; no solver or parameter changes."""
from fractions import Fraction as F
import gzip
from html import escape
import json
from pathlib import Path

import vacuum_registered_run as registered

D=registered.D
OUTPUT=D/'selected-summary.json'
VACUUM_COMPONENTS=('mean_P','mean_P2','variance_P','variance_P2','covariance_P_P2')


def subtract(left,right):
    if left is None or right is None:return None
    return [str(F(left[0])-F(right[1])),str(F(left[1])-F(right[0]))]


def summarize():
    registration=json.loads(registered.REGISTRATION.read_text())
    index=json.loads((registered.OUTPUT/'index.json').read_text())
    verification=registered.verify_run(registration,index['registration_commit'])
    rows=[]
    for spec,entry in zip(registration['cells'],index['cells']):
        cell=json.loads(gzip.decompress((registered.OUTPUT/entry['result']['path']).read_bytes()))
        stages=cell['stages']; certificate=stages['certificates']['rungs'][-1].get('record')
        certified=certificate is not None and registered.core.certificates.verify(certificate)
        result=certificate['result'] if certified else {}
        full=(result.get('first_three_gap_intervals',[None])[0] if spec['theory']=='SU2'
              else result.get('parity',{}).get('full_gap_interval'))
        channels=registered.core.certificates.verified_channels(certificate) if certified else []
        thresholds={c['certificate']['observable']:c['threshold'] for c in channels}
        vacuum=result.get('vacuum')
        components=dict(zip(VACUUM_COMPONENTS,
            [*vacuum['raw_moments'][:2],vacuum['covariance'][0][0],
             vacuum['covariance'][1][1],vacuum['covariance'][0][1]] if vacuum else [None]*5))
        constraints={'stages_completed':all(s['status']=='completed' for s in stages.values()),
                     'scalar_representation_agreement':cell.get('scalar_replay',{}).get('cross_representation_agreement') is True,
                     'scalar_exact_accuracy':cell.get('scalar_accuracy',{}).get('qualifies') is True,
                     'certificate_scalar_budget':result.get('scalar_budget_met') is True,
                     'common_sample_window':bool(cell.get('qualifying_common_sample_pairs'))}
        rows.append({'id':spec['id'],'theory':spec['theory'],'g':spec['g'],'eta':spec['eta'],
            'status':entry['status'],'verification':entry['verification'],'raw':entry['result'],
            'full_gap_interval':full,'thresholds':thresholds,'constraints':constraints,
            'vacuum_component_intervals':components,
            'stage_status':{k:{f:s[f] for f in ('status','reason') if f in s} for k,s in stages.items()},
            'times':stages['certificates'].get('times'),
            'common_sample_pairs':cell.get('qualifying_common_sample_pairs',[]),
            'scalar_accuracy':cell.get('scalar_accuracy'),
            'evidence':{'finest_certificate':certificate,'scalar_final':stages['scalar']['result'].get('final'),
                        'temporal_finest':stages['temporal']['result']['rungs'][-1]}})
    comparisons=[]
    for row in rows:
        if F(row['eta'])==0:continue
        base=next(r for r in rows if r['theory']==row['theory'] and r['g']==row['g'] and F(r['eta'])==0)
        differences={'full_gap':subtract(row['full_gap_interval'],base['full_gap_interval'])}
        differences.update({name:subtract(row['vacuum_component_intervals'][name],
                                          base['vacuum_component_intervals'][name])
                            for name in VACUUM_COMPONENTS})
        for observable in ('P','P2'):
            differences[observable+'_threshold']=subtract(row['thresholds'].get(observable,{}).get('gap_interval'),
                                                         base['thresholds'].get(observable,{}).get('gap_interval'))
        comparisons.append({'cell':row['id'],'reference':base['id'],'difference_intervals':differences,
                            'interpretation':'matched finite-model deformation; accessible leading levels may change'})
    full_intervals=[r['full_gap_interval'] for r in rows]
    common_lower=min(F(v[0]) for v in full_intervals) if all(v is not None for v in full_intervals) else None
    return {'schema_version':1,'finite_family_full_gap_lower':str(common_lower) if common_lower is not None else None,
            'registration_commit':index['registration_commit'],
            'registration_sha256':index['registration_sha256'],'index_sha256':registered.digest((registered.OUTPUT/'index.json').read_bytes()),
            'verification':verification,'elapsed_seconds':index['elapsed_seconds'],'cells':rows,
            'deformation_comparisons':comparisons,'scope':registration['scope'],
            'original_pilot':'permanently unverifiable; original script and results lost'}


def display(interval):
    if interval is None:return 'unresolved'
    return f'{float((F(interval[0])+F(interval[1]))/2):.9g}'


def table(summary):
    rows=[]
    for row in summary['cells']:
        values=[row['theory'],row['g'],row['eta'],row['status'],display(row['full_gap_interval'])]
        for observable in ('P','P2'):
            threshold=row['thresholds'].get(observable,{})
            values.append(display(threshold.get('gap_interval'))+(' (level '+str(threshold['leading_level'])+')' if threshold.get('leading_level') else ''))
        values.append(str(row['common_sample_pairs']))
        values.append(', '.join(k for k,v in row['constraints'].items() if not v) or 'all met')
        rows.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in values)+'</tr>')
    return '<table><tr>'+''.join('<th>'+s+'</th>' for s in ('Theory','g','η','Outcome','Full gap','P threshold','P² threshold','Common sample pairs','Unmet checks'))+'</tr>'+''.join(rows)+'</table>'


if __name__=='__main__':
    result=summarize(); registered.core.baseline.write_report(OUTPUT,result)
    print(json.dumps(result['verification']))


CHECKS=r'''
def verify_selected(report):
    from fractions import Fraction as F
    import hashlib,json
    data=report['data']; summary=data['selected-summary.json']
    registration=data['selected-registration.json']
    index=data['selected-run/index.json']
    assert summary['registration_commit']==index['registration_commit']
    assert summary['registration_sha256']==index['registration_sha256']
    assert summary['verification']==data['selected-run/verification.json']
    assert [c['id'] for c in summary['cells']]==registration['selected_target_ids']
    assert [c['id'] for c in registration['cells']]==registration['selected_target_ids']
    assert [c['id'] for c in index['cells']]==registration['selected_target_ids']
    assert len(summary['cells'])==42 and summary['verification']['status']=='verified'
    assert registration['registered'] and registration['target_execution_authorized']
    assert summary['verification']['cells']==42
    for row,spec,entry in zip(summary['cells'],registration['cells'],index['cells']):
        assert all(row[k]==spec[k] for k in ('id','theory','g','eta'))
        assert row['status']==entry['status'] and row['raw']==entry['result']
        assert row['verification']==entry['verification']
        assert row['status'] in ('instrument_agreement','unresolved','failure')
        intervals=[row['full_gap_interval']]+[c.get('gap_interval') for c in row['thresholds'].values()]
        intervals+=list(row['vacuum_component_intervals'].values())
        for interval in intervals:
            if interval is not None:
                lo,hi=map(F,interval); assert lo <= hi
        for threshold in row['thresholds'].values():
            if threshold['status']=='resolved':
                assert F(threshold['gap_interval'][0])>0
        if row['status']=='instrument_agreement':
            assert all(row['constraints'].values())
            assert row['full_gap_interval'] is not None and F(row['full_gap_interval'][0])>0
            assert all(row['thresholds'].get(o,{}).get('status')=='resolved' for o in ('P','P2'))
            assert all(v is not None for v in row['vacuum_component_intervals'].values())
        if F(row['eta'])==0:
            g=F(row['g']); full=(3 if row['theory']=='SU2' else 4)*g*g
            if row['full_gap_interval'] is not None:
                assert F(row['full_gap_interval'][0])<=full<=F(row['full_gap_interval'][1])
            for observable,level in [('P',1),('P2',2)]:
                c=row['thresholds'].get(observable,{})
                if c.get('status')!='resolved':continue
                assert c['leading_level']==level
                exact=g*g*level*(level+2) if row['theory']=='SU2' else 4*g*g*level*level
                assert F(c['gap_interval'][0])<=exact<=F(c['gap_interval'][1])
    if 'finite_family_full_gap_lower' in summary:
        intervals=[r['full_gap_interval'] for r in summary['cells']]
        expected=str(min(F(v[0]) for v in intervals)) if all(v is not None for v in intervals) else None
        assert summary['finite_family_full_gap_lower']==expected
    lookup={r['id']:r for r in summary['cells']}
    for comparison in summary['deformation_comparisons']:
        a,b=lookup[comparison['cell']],lookup[comparison['reference']]
        assert a['theory']==b['theory'] and a['g']==b['g'] and F(b['eta'])==0
        for field,difference in comparison['difference_intervals'].items():
            def component(row):
                if field=='full_gap':return row['full_gap_interval']
                if field.endswith('_threshold'):return row['thresholds'].get(field.split('_')[0],{}).get('gap_interval')
                return row['vacuum_component_intervals'][field]
            left,right=component(a),component(b)
            expected=None if left is None or right is None else [str(F(left[0])-F(right[1])),str(F(left[1])-F(right[0]))]
            assert difference==expected
    print('42 selected cells: exact free spectra, interval ordering and matched deformation arithmetic checked.')
    return 42
'''
