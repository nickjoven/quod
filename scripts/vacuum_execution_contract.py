"""Build/check an unselected protocol draft. No numerical or execution entry point."""
import argparse
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform

from jsonschema import Draft202012Validator

import vacuum_run_envelope as development

DIRECTORY=development.baseline.ROOT/'research/vacuum-spectrum'
SCHEMA=DIRECTORY/'execution-contract.schema.json'
OUTPUT=DIRECTORY/'execution-contract.json'
PACKAGES=('numpy','scipy','jsonschema','jsonpointer','referencing','rpds-py','attrs','jsonschema-specifications','typing-extensions')


def schema():
    result=json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(result)
    return result


def protocol():
    """Use the schema's exact frozen values; do not duplicate constants."""
    return {k:deepcopy(v['const']) for k,v in schema()['$defs']['protocol']['properties'].items()}


def environment():
    return {'python':platform.python_version(),'implementation':platform.python_implementation(),
            'packages':{name:version(name) for name in PACKAGES}}


def source_hashes():
    result=development.source_hashes()
    for path in (Path(__file__).resolve(),SCHEMA,DIRECTORY/'requirements.txt',
                 DIRECTORY/'requirements-readiness.txt'):
        result[str(path.relative_to(development.baseline.ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def draft():
    return {'schema_version':1,'registered':False,'target_execution_authorized':False,
            'selected_target_ids':[],'targets_run':0,
            'targets':[{'id':i,'status':'unrun','result':None} for i in development.baseline.target_ids()],
            'protocol':protocol(),'environment':environment(),'source_sha256':source_hashes()}


def validate(value):
    Draft202012Validator(schema()).validate(value)
    json.dumps(value,allow_nan=False)
    if [r['id'] for r in value['targets']]!=development.baseline.target_ids():
        raise ValueError('missing, reordered, duplicate or unknown target identity')
    if value['source_sha256']!=source_hashes():
        raise ValueError('execution contract source/schema drift')
    if value['environment']!=environment():
        raise ValueError('execution dependency environment drift')
    # This validates specification compatibility without invoking any solver.
    fixed=value['protocol']
    for theory in ('SU2','U1'):
        development.validate({'schema_version':1,'purpose':'development','registered':False,
            'target_execution_authorized':False,'source_sha256':development.source_hashes(),
            'tau':fixed['tau'],'tolerances':fixed['tolerances'],
            'cells':[{'id':'specification-consistency','theory':theory,'g':'1','eta':'1',
                      'cutoffs':fixed[theory+'_cutoffs'],'grids':fixed['grids']}]})
    return True


def validate_terminal_structure(value):
    """Structure is necessary, never sufficient for scientific qualification."""
    definition=schema()
    Draft202012Validator({'$schema':definition['$schema'],'$defs':definition['$defs'],
                         '$ref':'#/$defs/terminal_cell'}).validate(value)
    json.dumps(value,allow_nan=False)
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='write the dedicated unselected draft')
    args=parser.parse_args()
    value=draft() if args.write else json.loads(OUTPUT.read_text())
    validate(value)
    if args.write:
        development.baseline.write_report(OUTPUT,value)
    print('Unselected draft verified: 42 unrun targets; no execution authority.')


if __name__=='__main__':
    main()
