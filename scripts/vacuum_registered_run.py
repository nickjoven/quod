"""Committed all-42 registration, append-only checkpoints and registered execution."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

import vacuum_execution_contract as contract
import vacuum_run_envelope as core
import vacuum_run_replay as replay

ROOT=core.baseline.ROOT
D=contract.DIRECTORY
REGISTRATION=D/'selected-registration.json'
SCHEMA=D/'selected-registration.schema.json'
OUTPUT=D/'selected-run'
BASELINES=('refinement.json','certificates.json','late-times.json',
           'u1-design-development.json','u1-design-certificates.json','u1-design-semigroup.json',
           'pilot-disposition.json')
AUTHORIZATION='User selected all 42 SU2/corrected-U1 cells and authorized committed registration, validation, then execution without further confirmation.'
FAILURE_RULES={'solver_failure':'retain partial evidence and continue later selected cells',
 'checkpoint_failure':'stop immediately; no silent restart or overwrite',
 'source_or_dependency_drift':'stop new target work and invalidate qualification',
 'unresolved':'retain at fixed caps; never replace with zero or a gap-collapse claim',
 'post_result_changes':'no budget widening, schedule extension or additional refinement',
 'controls':'failed required preflight prevents every target attempt',
 'verification':'replay every cell before qualification; retain invalid evidence as failure'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sources():
    result=contract.source_hashes()
    for p in (Path(__file__).resolve(),SCHEMA,ROOT/'scripts/test_vacuum_registered_run.py'):
        result[str(p.relative_to(ROOT))]=digest(p.read_bytes())
    return result


def cells():
    protocol=contract.protocol()
    result=[]
    for name in core.baseline.target_ids():
        theory,g,eta=name.split(':')
        result.append({'id':name,'theory':theory,'g':g.split('=')[1],'eta':eta.split('=')[1],
                       'cutoffs':protocol[theory+'_cutoffs'],'grids':protocol['grids']})
    return result


def registration():
    protocol=contract.protocol()
    return {'schema_version':1,'registered':True,'target_execution_authorized':True,
            'authorization':AUTHORIZATION,'selected_target_ids':core.baseline.target_ids(),'cells':cells(),
            'protocol':protocol,'tau':protocol['tau'],'tolerances':protocol['tolerances'],
            'environment':contract.environment(),'source_sha256':sources(),
            'baseline_sha256':{n:digest((D/n).read_bytes()) for n in BASELINES},
            'handoff':{'commit':'24d42a9abdbeb67c2ca4cbb6759d200af5ddeb19',
                       'path':'research/vacuum-spectrum/VACUUM-REPORT.html',
                       'original_pilot':'permanently unverifiable; script and results lost'},
            'failure_rules':FAILURE_RULES,
            'scope':'Registered finite-rotor characterization; full gaps distinct from accessible thresholds; no uniform Yang-Mills gap proof.'}


def validate(value):
    schema=json.loads(SCHEMA.read_text())
    registry=Registry().with_resource('urn:quod:execution-contract',Resource.from_contents(contract.schema()))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema,registry=registry).validate(value)
    replay.encoded(value)
    if value!=registration():
        raise ValueError('registration differs from exact authorized selection, frozen rules, sources, baseline or dependencies')
    return True


def committed(value,commit):
    validate(value)
    if not commit or any(c not in '0123456789abcdef' for c in commit) or len(commit)!=40:
        raise ValueError('full registration commit required')
    def blob(path):
        return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
    path=str(REGISTRATION.relative_to(ROOT))
    if blob(path)!=REGISTRATION.read_bytes() or json.loads(blob(path))!=value:
        raise ValueError('registration not identical to committed document')
    pins=dict(value['source_sha256'])
    pins.update({str((D/name).relative_to(ROOT)):sha for name,sha in value['baseline_sha256'].items()})
    for path,sha in pins.items():
        if digest(blob(path))!=sha:
            raise ValueError('registered source not present in registration commit: '+path)
    return True


def write_gzip(path,value):
    if path.exists():
        raise FileExistsError('refusing to overwrite evidence: '+str(path))
    raw=replay.encoded(value).encode()
    compressed=gzip.compress(raw,mtime=0)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(compressed); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)
    return {'path':str(path.relative_to(OUTPUT)),'sha256':digest(compressed),'json_sha256':digest(raw)}


def inventory(spec,cell,tolerances):
    if cell['id']!=spec['id']:
        raise ValueError('cell identity mismatch')
    stages=cell['stages']
    expected=core.planned_stages(spec,tolerances)
    if [(r['method'],r['rung']) for r in stages['scalar']['result']['rungs']]!=[(r['method'],r['rung']) for r in expected['scalar']['result']['rungs']]:
        raise ValueError('scalar request coverage')
    if [r['cutoff'] for r in stages['certificates']['rungs']]!=spec['cutoffs']:
        raise ValueError('certificate request coverage')
    temporal=stages['temporal']['result']['rungs']
    if [r['nodes'] for r in temporal]!=spec['grids']:
        raise ValueError('temporal grid coverage')
    for rung in temporal:
        if [[s['rtol'],s['atol']] for s in rung['evolutions']]!=tolerances:
            raise ValueError('temporal tolerance coverage')
    for stage in stages.values():
        if stage['status'] not in ('completed','failed','unresolved'):
            raise ValueError('nonterminal stage')
    for rung in stages['scalar']['result']['rungs']+stages['certificates']['rungs']+temporal:
        if rung['status'] not in ('completed','failed','unresolved'):
            raise ValueError('nonterminal rung')
        for slot in rung.get('evolutions',[]):
            if slot['status'] not in ('completed','failed','unresolved'):
                raise ValueError('nonterminal evolution')


def assess(spec,cell,registration):
    try:
        inventory(spec,cell,registration['tolerances'])
        status=replay.replay_cell(spec,cell,registration)
        return {'status':'verified','outcome':'instrument_agreement' if status=='development_qualified' else status}
    except Exception as exc:
        return {'status':'invalid','outcome':'failure','reason':f'{type(exc).__name__}: {exc}'}


def execute_cell(spec,registration,checkpoint):
    cell={'id':spec['id'],'status':'pending','stages':core.planned_stages(spec,registration['tolerances'])}
    def emit():
        try: checkpoint(deepcopy(cell))
        except Exception as exc: raise core.CheckpointFailure('checkpoint failed; target work stopped') from exc
    emit()
    try:
        core.process_cell(spec,cell,registration,emit)
    except core.CheckpointFailure:
        raise
    except Exception as exc:
        cell.update(status='failure',reason=f'{type(exc).__name__}: {exc}')
        for stage in cell['stages'].values():
            if stage['status']=='pending':core.terminalize(stage,'failed','unexpected cell exception')
    emit()
    return cell,assess(spec,cell,registration)


def run(value,commit):
    committed(value,commit)
    if os.environ.get('OPENBLAS_NUM_THREADS')!='1':
        raise ValueError('run with OPENBLAS_NUM_THREADS=1')
    if OUTPUT.exists():
        raise FileExistsError('run directory already exists; no silent restart or evidence overwrite')
    OUTPUT.mkdir()
    start=time.monotonic()
    index={'schema_version':1,'state':'running','registration_commit':commit,
           'registration_sha256':digest(REGISTRATION.read_bytes()),'selected':42,'attempted':0,
           'cells':[{'id':s['id'],'status':'unrun','attempted':False,'result':None} for s in value['cells']],
           'checkpoints':[],'scope':value['scope']}
    def save():
        index['elapsed_seconds']=time.monotonic()-start
        core.baseline.write_report(OUTPUT/'index.json',index)
    save()
    index['control_preflight']=core.control_preflight()
    try:
        controls=replay.control_verdict(index['control_preflight'])
    except Exception as exc:
        controls=False
        index['control_error']=f'{type(exc).__name__}: {exc}'
    save()
    if not controls:
        index.update(state='instrument_failure',reason='required controls failed; no targets attempted')
        for row in index['cells']:row['reason']='blocked by control preflight'
        save(); return index
    def drift_check():
        try:
            validate(value)
            return True
        except Exception as exc:
            index.update(state='instrument_failure',reason=f'source/dependency drift: {exc}',source_verification='failed')
            for item in index['cells']:
                if item['status']=='instrument_agreement':
                    item['prior_status']=item['status']; item['status']='failure'
                if not item['attempted']:item['reason']='blocked by source/dependency drift'
            save()
            return False
    for number,(spec,row) in enumerate(zip(value['cells'],index['cells'])):
        if not drift_check():return index
        row.update(status='running',attempted=True); index['attempted']+=1; save()
        sequence=0
        def checkpoint(cell):
            nonlocal sequence
            path=OUTPUT/'checkpoints'/f'{number:02d}-{sequence:03d}.json.gz'
            ref=write_gzip(path,cell); sequence+=1
            index['checkpoints'].append(ref); save()
        cell,verification=execute_cell(spec,value,checkpoint)
        ref=write_gzip(OUTPUT/'cells'/f'{number:02d}.json.gz',cell)
        row.update(status=verification['outcome'],verification=verification,result=ref)
        save()
        if not drift_check():return index
        print(json.dumps({'cell':number+1,'id':spec['id'],'status':row['status'],'elapsed_seconds':index['elapsed_seconds']}),flush=True)
    index['state']='completed_with_failures' if any(r['status']=='failure' for r in index['cells']) else 'completed'
    index['source_verification']='passed'; save()
    return index


def checkpoint_snapshots(index):
    """Check complete ordered checkpoint inventory and return final snapshots."""
    refs=index['checkpoints']
    paths=[r['path'] for r in refs]
    present=sorted(str(p.relative_to(OUTPUT)) for p in (OUTPUT/'checkpoints').glob('*.json.gz'))
    if len(set(paths))!=len(paths) or sorted(paths)!=present:
        raise ValueError('checkpoint inventory differs from retained files')
    offset=0
    snapshots=[]
    for number,row in enumerate(index['cells']):
        sequence=0
        last=None
        prefix=f'checkpoints/{number:02d}-'
        while offset<len(refs) and refs[offset]['path'].startswith(prefix):
            ref=refs[offset]
            if ref['path']!=prefix+f'{sequence:03d}.json.gz':
                raise ValueError('checkpoint sequence is missing, reordered or noncanonical')
            raw=(OUTPUT/ref['path']).read_bytes()
            unpacked=gzip.decompress(raw)
            if digest(raw)!=ref['sha256'] or digest(unpacked)!=ref['json_sha256']:
                raise ValueError('checkpoint digest mismatch')
            last=json.loads(unpacked)
            if last['id']!=row['id']:
                raise ValueError('checkpoint cell identity mismatch')
            sequence+=1; offset+=1
        if sequence<2:
            raise ValueError('completed cell lacks initial and final checkpoints')
        snapshots.append(last)
    if offset!=len(refs):
        raise ValueError('checkpoint references outside selected cell sequence')
    return snapshots


def verify_run(value,commit):
    """Verify a complete terminal run; interrupted runs retain forensic evidence."""
    committed(value,commit)
    index=json.loads((OUTPUT/'index.json').read_text())
    if index.get('source_verification')!='passed':
        raise ValueError('complete run requires a successful final source/dependency audit')
    if index['registration_commit']!=commit or index['registration_sha256']!=digest(REGISTRATION.read_bytes()):
        raise ValueError('run registration binding mismatch')
    if [r['id'] for r in index['cells']]!=value['selected_target_ids']:
        raise ValueError('selected row inventory mismatch')
    if not replay.control_verdict(index['control_preflight']):
        raise ValueError('control preflight failed')
    def read_ref(ref):
        path=(OUTPUT/ref['path']).resolve()
        if not path.is_relative_to(OUTPUT.resolve()):raise ValueError('evidence path outside run')
        return path.read_bytes()
    snapshots=checkpoint_snapshots(index)
    outcomes=[]
    for spec,row,snapshot in zip(value['cells'],index['cells'],snapshots):
        raw=read_ref(row['result'])
        if digest(raw)!=row['result']['sha256'] or digest(gzip.decompress(raw))!=row['result']['json_sha256']:
            raise ValueError('raw cell digest mismatch')
        cell=json.loads(gzip.decompress(raw))
        if replay.encoded(cell)!=replay.encoded(snapshot):
            raise ValueError('final cell differs from its last preserved checkpoint')
        result=assess(spec,cell,value)
        if result!=row['verification'] or result['outcome']!=row['status']:
            raise ValueError('stored outcome/replay mismatch')
        outcomes.append(row['status'])
    expected='completed_with_failures' if 'failure' in outcomes else 'completed'
    if index['selected']!=42 or index['state']!=expected or index['attempted']!=42 or not all(r['attempted'] for r in index['cells']):
        raise ValueError('terminal run accounting mismatch')
    validate(value)
    return {'status':'verified','cells':42,'outcomes':{s:outcomes.count(s) for s in set(outcomes)},
            'checkpoints':len(index['checkpoints']),'registration_commit':commit}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','check','run','verify'))
    parser.add_argument('--registration-commit')
    args=parser.parse_args()
    if args.action=='prepare':
        value=registration(); validate(value); core.baseline.write_report(REGISTRATION,value)
        print('Selected all42 registration prepared; commit and validate before execution.'); return
    value=json.loads(REGISTRATION.read_text())
    committed(value,args.registration_commit)
    if args.action=='run':run(value,args.registration_commit)
    elif args.action=='verify':
        result=verify_run(value,args.registration_commit)
        core.baseline.write_report(OUTPUT/'verification.json',result); print(json.dumps(result))
    else:print('Committed registration, sources, schemas, baseline and dependencies verified.')


if __name__=='__main__':main()
