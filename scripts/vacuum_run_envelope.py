"""Checkpointed development integration; reject targets before numerical work."""
import ast
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import vacuum_development as baseline
import vacuum_parameterized_scalar as scalar
import vacuum_parameterized_certificate as certificates
import vacuum_parameterized_temporal as temporal
import vacuum_future_adapter as adapter

SCHEMA = baseline.ROOT / 'research/vacuum-spectrum/run-envelope.schema.json'


class CheckpointFailure(RuntimeError):
    """Stop numerical work if the caller cannot preserve a checkpoint."""


def source_hashes():
    """Pin transitive local Python imports plus both runtime stage schemas."""
    pending, seen = [Path(__file__).resolve()], set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else (
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in names:
                local = path.parent / (name.split('.')[0]+'.py')
                if local.is_file() and local not in seen:
                    pending.append(local)
    seen.update((SCHEMA, baseline.ROOT/'research/vacuum-spectrum/future-stage-input.schema.json'))
    return {str(p.relative_to(baseline.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(seen)}


def validate(manifest):
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)
    json.dumps(manifest,allow_nan=False)
    if manifest['source_sha256'] != source_hashes():
        raise ValueError('execution source or schema drift')
    ids, coordinates = set(), set()
    allowed = {F(str(g)) for g in baseline.G_VALUES}
    for cell in manifest['cells']:
        g,eta = F(cell['g']),F(cell['eta'])
        if g not in allowed or eta not in (0,F(1,2),1):
            raise PermissionError('only existing development couplings and declared deformations are executable; targets disabled')
        key = cell['theory'],g,eta
        if cell['id'] in ids or key in coordinates:
            raise ValueError('duplicate cell ID or model coordinate')
        ids.add(cell['id']); coordinates.add(key)
        scalar.ladder(cell['cutoffs'],4,'cutoffs')
        scalar.ladder(cell['grids'],16,'grids')
        if cell['theory']=='U1' and any(n%2 for n in cell['grids']):
            raise ValueError('U1 periodic grids must be even')
        if manifest['purpose']=='development':
            expected = list(baseline.CHARACTER_J) if cell['theory']=='SU2' else [40,80,160,320,640]
            if cell['cutoffs']!=expected or cell['grids']!=list(baseline.ANGLE_INTERIORS):
                raise ValueError('development runs require the full recovered ladders')
    tau = list(map(F,manifest['tau']))
    if tau[0]!=0 or any(b<=a for a,b in zip(tau,tau[1:])):
        raise ValueError('tau must start at zero and strictly increase')
    if manifest['purpose']=='development':
        expected_tau=list(map(F,('0','1/8','1/4','1/2','1','2','4','8','12','16','20','24')))
        if tau!=expected_tau or manifest['tolerances']!=[list(t) for t in temporal.TOLERANCES]:
            raise ValueError('development runs require the frozen sample schedule and tolerance pairs')


def retime(record, times):
    if not certificates.verify(record):
        raise ValueError('cannot retime an invalid certificate')
    theory,cutoff=record['theory'],record['cutoff']
    g,eta,times=certificates.coordinates(theory,record['g'],record['eta'],cutoff,times)
    r=record['result']
    eigen=certificates.decode_eigen(r['enclosures' if theory=='SU2' else 'even_enclosures'])
    odd=None if theory=='SU2' else certificates.decode_eigen(r['odd_enclosures'])
    vectors=[[float.fromhex(v) for v in q] for q in r['candidate_vectors_hex']]
    out=deepcopy(record)
    out['times']=certificates.encode(times)
    out['result']=certificates.encode(certificates.assemble(theory,g,eta,cutoff,times,eigen,odd,vectors))
    return out


def planned_stages(spec, tolerances):
    basis = 'character' if spec['theory']=='SU2' else 'fourier'
    return {
        'scalar': {'status':'pending', 'result': {'rungs':[
            {'method':method,'rung':n,'status':'pending'}
            for method,sizes in ((basis,spec['cutoffs']),('angle_fourth',spec['grids'])) for n in sizes]}},
        'certificates': {'status':'pending','rungs':[
            {'cutoff':k,'status':'pending','retime_status':'not_attempted'} for k in spec['cutoffs']]},
        'temporal': {'status':'pending','result':{'rungs':[
            {'nodes':n,'status':'pending','evolutions':[
                {'rtol':r,'atol':a,'status':'pending'} for r,a in tolerances]} for n in spec['grids']]}}
    }


def terminalize(stage, status, reason):
    stage.update(status=status,reason=reason)
    for rung in stage.get('rungs',stage.get('result',{}).get('rungs',[])):
        if rung['status']=='pending':
            rung.update(status=status,reason=reason)
        for slot in rung.get('evolutions',[]):
            if slot['status']=='pending':
                slot.update(status=status,reason=reason)


def scalar_accuracy(stages, theory):
    exact=stages['certificates'].get('result')
    final=stages['scalar'].get('result',{}).get('final')
    if exact is None or exact.get('vacuum') is None or final is None:
        return {'status':'unresolved','qualifies':False,'reason':'finest scalar/certificate evidence unavailable'}
    vacuum=exact['vacuum']
    moments=[*vacuum['raw_moments'][:2],vacuum['covariance'][0][0],
             vacuum['covariance'][1][1],vacuum['covariance'][0][1]]
    gaps=exact['first_three_gap_intervals' if theory=='SU2' else 'first_three_even_gap_intervals']
    output={}
    for method,record in final.items():
        moment_errors=[max(abs(F(float(v))-F(e)) for e in interval)
                       for v,interval in zip(record['moments'],moments)]
        actual_gaps=list(record['first_three_gaps'])
        bounds=list(gaps)
        if theory=='U1':
            if exact['parity']['full_gap_interval'] is None:
                return {'status':'unresolved','qualifies':False,'reason':'full U1 gap unavailable'}
            actual_gaps.append(record['full_gap'])
            bounds.append(exact['parity']['full_gap_interval'])
        if len(moment_errors)!=5 or len(actual_gaps)!=len(bounds) or any(F(i[0])<=0 for i in bounds):
            return {'status':'unresolved','qualifies':False,'reason':'scalar shape or positive gap bound unavailable'}
        relative=[max(abs(F(float(v))-F(e)) for e in interval)/F(interval[0])
                  for v,interval in zip(actual_gaps,bounds)]
        output[method]={'moment_absolute_error_upper':moment_errors,
                        'gap_relative_error_upper':relative,
                        'qualifies':all(x<=F(1,10**6) for x in moment_errors+relative)}
    return certificates.encode({'status':'assessed','qualifies':bool(output) and all(r['qualifies'] for r in output.values()),
                                'methods':output})


def process_cell(spec, cell, manifest, emit):
    theory,g,eta=spec['theory'],spec['g'],spec['eta']
    stages=cell['stages']
    try:
        stages['scalar']=scalar.run(theory,g,eta,spec['cutoffs'],spec['grids'])
    except Exception as exc:
        terminalize(stages['scalar'],'failed',f'unexpected scalar stage error: {type(exc).__name__}: {exc}')
    emit()
    stage=stages['certificates']
    for rung in stage['rungs']:
        try:
            rung['record']=certificates.calculate(theory,g,eta,rung['cutoff'],[0])
            if not certificates.verify(rung['record']):
                raise ValueError('generated certificate failed replay')
            rung['status']='completed'
        except Exception as exc:
            rung.update(status='failed',reason=f'{type(exc).__name__}: {exc}')
        emit()
    final=stage['rungs'][-1]
    try:
        if final['status']!='completed':
            raise ValueError('finest certificate unavailable; no fallback')
        record=final['record']
        selected=certificates.verified_channels(record)
        if len(selected)!=2 or any(c['threshold']['status']!='resolved' for c in selected):
            stage.update(status='unresolved',reason='finest observable thresholds unresolved',result=record['result'])
            terminalize(stages['temporal'],'unresolved','no certified clock reference')
        else:
            reference=min((F(c['threshold']['gap_interval'][0])+F(c['threshold']['gap_interval'][1]))/2 for c in selected)
            times=[F(float(F(t)/reference)) for t in manifest['tau']]
            for rung in stage['rungs']:
                if rung['status']=='completed':
                    rung['initial_record']=deepcopy(rung['record'])
                    try:
                        rung['record']=retime(rung['initial_record'],times)
                        rung['retime_status']='completed'
                    except Exception as exc:
                        rung.update(status='failed',retime_status='failed',reason=f'{type(exc).__name__}: {exc}')
                    emit()
            if final['status']!='completed' or final['retime_status']!='completed':
                raise ValueError('finest retimed certificate unavailable; no fallback')
            record=final['record']
            stage.update(status='completed',result=record['result'],times=record['times'],
                         clock_rule='binary64-rounded tau / minimum accessible-gap midpoint at finest certificate')
            try:
                stages['temporal']=temporal.run(record,spec['grids'],manifest['tolerances'])
            except Exception as exc:
                terminalize(stages['temporal'],'failed',f'unexpected temporal stage error: {type(exc).__name__}: {exc}')
    except CheckpointFailure:
        raise
    except Exception as exc:
        stage.update(status='failed',reason=f'{type(exc).__name__}: {exc}')
        terminalize(stages['temporal'],'unresolved','certificate prerequisite failed')
    if any(r['status']=='failed' for r in stage['rungs']):
        stage.update(status='failed',reason='one or more requested certificate rungs failed; partial evidence retained')
    emit()
    adapted=adapter.adapt_cell(theory,g,eta,stages)
    cell['adaptation']=adapted
    cell['scalar_accuracy']=scalar_accuracy(stages,theory)
    common=[]
    if stages['temporal']['status']=='completed':
        last=stages['temporal']['result']['rungs'][-1]['evolutions'][-1]
        common=[p['sample_indices'] for p in last['pairs'] if all(o['window']['qualifies'] for o in p['observables'])]
    qualified=(adapted['status']=='available' and stages['scalar']['result']['cross_representation_agreement'] is True
               and stage.get('result',{}).get('scalar_budget_met') is True
               and cell['scalar_accuracy']['qualifies'] and bool(common))
    cell.update(status='failure' if adapted['status']=='failure' else ('development_qualified' if qualified else 'unresolved'),
                qualifying_common_sample_pairs=common,registered_window=None)


def accounting(manifest, result):
    try:
        if [c['id'] for c in result['cells']] != [c['id'] for c in manifest['cells']]:
            return False
        if result['targets_run']!=0 or result['target_execution_authorized']:
            return False
        if result['targets'] != [{'id':t,'status':'unrun'} for t in baseline.target_ids()]:
            return False
        terminal = {'completed','failed','unresolved'}
        for spec,cell in zip(manifest['cells'],result['cells']):
            s=cell['stages']
            if set(s)!={'scalar','certificates','temporal'} or any(v['status'] not in terminal for v in s.values()):
                return False
            basis='character' if spec['theory']=='SU2' else 'fourier'
            scalar_rungs=s['scalar']['result']['rungs']
            if [(r['method'],r['rung']) for r in scalar_rungs] != [(m,n) for m,ns in ((basis,spec['cutoffs']),('angle_fourth',spec['grids'])) for n in ns]:
                return False
            cert_rungs=s['certificates']['rungs']
            if [r['cutoff'] for r in cert_rungs] != spec['cutoffs']:
                return False
            time_rungs=s['temporal']['result']['rungs']
            if [r['nodes'] for r in time_rungs] != spec['grids']:
                return False
            if any(r['status'] not in terminal for r in scalar_rungs+cert_rungs+time_rungs):
                return False
            for r in time_rungs:
                if [[e['rtol'],e['atol']] for e in r['evolutions']] != manifest['tolerances']:
                    return False
                if any(e['status'] not in terminal for e in r['evolutions']):
                    return False
            if 'times' in s['certificates'] and any(r['record']['times']!=s['certificates']['times']
                    for r in cert_rungs if r['status']=='completed'):
                return False
        return True
    except (KeyError,TypeError,ValueError):
        return False


def run(manifest, checkpoint=None):
    validate(manifest)  # entire manifest checked before the first solver
    manifest=deepcopy(manifest)
    result={'schema_version':1,'state':'running','manifest':deepcopy(manifest),
            'targets_run':0,'target_execution_authorized':False,
            'targets':[{'id':t,'status':'unrun'} for t in baseline.target_ids()],
            'cells':[{'id':c['id'],'status':'pending','stages':planned_stages(c,manifest['tolerances'])}
                     for c in manifest['cells']]}
    def emit():
        if checkpoint:
            try:
                checkpoint(deepcopy(result))
            except Exception as exc:
                raise CheckpointFailure('checkpoint failed; numerical work stopped') from exc
    emit()
    for spec,cell in zip(manifest['cells'],result['cells']):
        try:
            process_cell(spec,cell,manifest,emit)
        except CheckpointFailure:
            raise
        except Exception as exc:
            cell.update(status='failure',reason=f'unexpected cell error: {type(exc).__name__}: {exc}')
            for stage in cell['stages'].values():
                if stage['status']=='pending':
                    terminalize(stage,'failed','cell processing aborted')
        emit()
    result['state']='completed_with_failures' if any(c['status']=='failure' for c in result['cells']) else 'completed'
    try:
        result['source_verification']='passed' if source_hashes()==manifest['source_sha256'] else 'failed'
    except Exception as exc:
        result.update(source_verification='failed',source_verification_reason=f'{type(exc).__name__}: {exc}')
    result['accounting_verified']=accounting(manifest,result)
    if result['source_verification']=='failed' or not result['accounting_verified']:
        result.update(state='instrument_failure',reason='source/schema drift or incomplete request accounting')
        for cell in result['cells']:
            cell.update(pre_audit_status=cell['status'],status='failure',reason='final evidence audit invalidates qualification')
    emit()
    return certificates.encode(result)
