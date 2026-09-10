"""Freeze target inventory and requests without selecting or executing cells."""
import argparse
import hashlib
import json

from jsonschema import Draft202012Validator

import vacuum_execution_contract as contract

SCHEMA=contract.DIRECTORY/'target-result-envelope.schema.json'
OUTPUT=contract.DIRECTORY/'target-result-envelope.json'


def requests(theory,protocol):
    cutoffs=protocol[theory+'_cutoffs']
    basis='character' if theory=='SU2' else 'fourier'
    return {'scalar':[{'method':m,'rung':n} for m,ns in
                       ((basis,cutoffs),('angle_fourth',protocol['grids'])) for n in ns],
            'certificates':list(cutoffs),
            'temporal':[{'nodes':n,'rtol':r,'atol':a} for n in protocol['grids'] for r,a in protocol['tolerances']]}


def bound_contract():
    raw=contract.OUTPUT.read_bytes()
    value=json.loads(raw)
    contract.validate(value)
    return value,hashlib.sha256(raw).hexdigest()


def draft():
    specification,digest=bound_contract()
    return {'schema_version':1,'state':'awaiting_target_selection','contract_sha256':digest,
            'selected_target_ids':[],'target_execution_authorized':False,'targets_run':0,
            'rows':[{'id':row['id'],'selected':False,'status':'unrun',
                     'reason':"awaiting the user's target selection",'result':None,
                     'requests':requests(row['id'].split(':')[0],specification['protocol'])}
                    for row in specification['targets']]}


def validate(value):
    definition=json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(definition)
    Draft202012Validator(definition).validate(value)
    json.dumps(value,allow_nan=False)
    specification,digest=bound_contract()
    if value['contract_sha256']!=digest:
        raise ValueError('target envelope contract digest mismatch')
    if [r['id'] for r in value['rows']]!=[r['id'] for r in specification['targets']]:
        raise ValueError('target identity inventory mismatch')
    for row in value['rows']:
        if row['requests']!=requests(row['id'].split(':')[0],specification['protocol']):
            raise ValueError('requested methods, cutoffs, grids or tolerances differ from frozen protocol')
    return True


def require_execution_authority(value):
    """Current stopping boundary: a draft can never authorize target execution.

    After the user chooses targets, a separate committed registration and exact
    subset execution path must be reviewed. No flag in this draft enables it.
    """
    validate(value)
    raise PermissionError('Target execution is disabled: user selection and committed registration are absent.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    value=draft() if args.write else json.loads(OUTPUT.read_text())
    validate(value)
    if args.write:
        contract.development.baseline.write_report(OUTPUT,value)
    print('42 unselected rows; 378 scalar, 210 certificate and 336 temporal requests planned; zero executed.')


if __name__=='__main__':
    main()
