"""Draft result contract, checked on development archives; targets stay unrun."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import jsonpointer

import vacuum_development as baseline
import vacuum_certificate_run as shared
import vacuum_channel_contract as channels

DIRECTORY=baseline.ROOT/'research/vacuum-spectrum'
SCHEMA=DIRECTORY/'result-contract.schema.json'
INPUTS={'SU2':('refinement.json','certificates.json','late-times.json'),
        'U1':('u1-design-development.json','u1-design-certificates.json','u1-design-semigroup.json')}


def ref(name,pointer):
    return {'path':name,'sha256':hashlib.sha256((DIRECTORY/name).read_bytes()).hexdigest(),'pointer':pointer}


def resolve(reference):
    path=(DIRECTORY/reference['path']).resolve()
    if path.parent!=DIRECTORY or hashlib.sha256(path.read_bytes()).hexdigest()!=reference['sha256']:
        raise ValueError('artifact reference drift or invalid path')
    return jsonpointer.resolve_pointer(json.loads(path.read_text()),reference['pointer'])


def channel_from_certificate(theory,g,eta,result,observable):
    a=0 if observable=='P' else 1
    eigen=result['enclosures' if theory=='SU2' else 'even_enclosures']
    gaps=result['first_three_gap_intervals' if theory=='SU2' else 'first_three_even_gap_intervals']
    weights=[(F(row[a]['weight_lower']),F(row[a]['weight_upper'])) for row in result['overlaps']]
    variance=tuple(map(F,result['vacuum']['covariance'][a][a]))
    omitted=(max(F(0),variance[0]-sum(w[1] for w in weights)),max(F(0),variance[1]-sum(w[0] for w in weights)))
    return {'theory':theory,'g':str(g),'eta':str(eta),'observable':observable,
        'spectral_scope':'full' if theory=='SU2' else 'reflection_even','ordering_certified':True,
        'states':[{'level':i,'gap_interval':gap,'weight_interval':weight,'exact_zero_rule':None}
                  for i,(gap,weight) in enumerate(zip(gaps,weights),1)],
        'omitted_gap_lower':F(eigen[4]['lower'])-F(eigen[0]['upper']),
        'omitted_weight_interval':omitted}


def build():
    rows=[]
    for theory,(scalar_name,cert_name,time_name) in INPUTS.items():
        cert=json.loads((DIRECTORY/cert_name).read_text())
        for i,cell in enumerate(cert['cells']):
            final=cell['rungs'][-1]['result']
            adapted=[channel_from_certificate(theory,cell['g'],1,final,o) for o in ('P','P2')]
            rows.append({'theory':theory,'g':str(cell['g']),'eta':'1','partition':'development',
                'status':'available','reason':'archived development output; no target execution',
                'channels':[{'certificate':c,'threshold':channels.threshold(c)} for c in adapted],
                'payload':{'scalar':ref(scalar_name,f'/cells/{i}/final'),
                           'certificates':ref(cert_name,f'/cells/{i}'),
                           'temporal':ref(time_name,f'/cells/{i}')}})
    result=shared.encode({'schema_version':1,'state':'unregistered_contract','registered':False,
        'target_execution_authorized':False,'targets_run':0,
        'targets':[{'id':t,'status':'unrun','reason':'registration and user target decision outstanding','result':None} for t in baseline.target_ids()],
        'development_examples':rows,'source_sha256':{p:hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest()
            for p in ('scripts/vacuum_result_contract.py','scripts/vacuum_channel_contract.py')},
        'schema_sha256':hashlib.sha256(SCHEMA.read_bytes()).hexdigest()})
    validate(result)
    return result


def validate(result):
    schema=json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(result)
    if not baseline.coverage(result['targets']):
        raise ValueError('target manifest mismatch')
    expected=[(theory,str(g),'1') for theory in INPUTS for g in baseline.G_VALUES]
    if [(r['theory'],r['g'],r['eta']) for r in result['development_examples']]!=expected:
        raise ValueError('development manifest mismatch')
    if result['schema_sha256']!=hashlib.sha256(SCHEMA.read_bytes()).hexdigest():
        raise ValueError('schema source drift')
    required_sources=('scripts/vacuum_result_contract.py','scripts/vacuum_channel_contract.py')
    if result['source_sha256']!={p:hashlib.sha256((baseline.ROOT/p).read_bytes()).hexdigest() for p in required_sources}:
        raise ValueError('contract source drift')
    for row_index,row in enumerate(result['development_examples']):
        if row['payload'] is None:
            if row['channels']:
                raise ValueError('channel evidence requires a payload')
            continue
        if len(row['channels']) not in (0,2):
            raise ValueError('retain both observable channel slots')
        for key,name in zip(('scalar','certificates','temporal'),INPUTS[row['theory']]):
            pointer=f'/cells/{row_index%len(baseline.G_VALUES)}'+('/final' if key=='scalar' else '')
            if row['payload'][key]!=ref(name,pointer):
                raise ValueError('payload reference does not match cell identity')
            resolve(row['payload'][key])
        source=resolve(row['payload']['certificates'])['rungs'][-1]['result']
        for item,observable in zip(row['channels'],('P','P2')):
            expected_channel=shared.encode(channel_from_certificate(row['theory'],row['g'],row['eta'],source,observable))
            if item['certificate']!=expected_channel or item['threshold']!=shared.encode(channels.threshold(item['certificate'])):
                raise ValueError('channel certificate or threshold differs from source')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve()!=(DIRECTORY/'result-contract.json').resolve():
        parser.error('use the dedicated result-contract.json output')
    result=build()
    baseline.write_report(args.output,result)
    print(json.dumps({'development_examples':len(result['development_examples']),'targets_run':result['targets_run']}))
