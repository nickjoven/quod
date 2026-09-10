"""Whole development-result replay; no eigensolver or propagation invocation.

Recomputes retained arithmetic and outcomes under current source pins. Recorded
operational failures and control verdicts are not execution-authenticity proofs.
"""
from copy import deepcopy
from fractions import Fraction as F
import json

from jsonschema import Draft202012Validator, ValidationError

import vacuum_run_envelope as runner
from vacuum_temporal_replay import encoded, require, reason


def control_verdict(preflight):
    schema=json.loads((runner.baseline.ROOT/'research/vacuum-spectrum/control-preflight.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(preflight)
    suites=preflight['suites']
    require(set(suites)=={'design_nulls','analytic_nulls','SU2_representation','U1_representation'},
            'control suite inventory mismatch')
    for suite in suites.values():
        require(suite['status'] in ('passed','failed'),'nonterminal control verdict')
        if 'result' not in suite:
            require(suite['status']=='failed','missing successful control evidence'); reason(suite)
            continue
        record=suite['result']
        require(isinstance(record,dict),'control result must be an object')
        checks=record.get('checks',{})
        mutants=record.get('mutants_rejected',record.get('mutants',{}))
        require(isinstance(checks,dict) and isinstance(mutants,dict),'control checks and mutants must be objects')
        accepted=(record.get('pass') is True and bool(checks) and bool(mutants)
                  and all(v is True for v in checks.values())
                  and all((v.get('rejected') if isinstance(v,dict) else v) is True for v in mutants.values()))
        require((suite['status']=='passed')==accepted,'control aggregate contradicts individual verdicts')
    passed=all(s['status']=='passed' for s in suites.values())
    require(preflight['status']==('passed' if passed else 'failed'),'control preflight aggregate mismatch')
    return passed


def certificate_stage(spec,stage,tau):
    """Replay every successful certificate and bind all retiming to the frozen rule."""
    def check(record,cutoff):
        require(record['theory']==spec['theory'] and F(record['g'])==F(spec['g'])
                and F(record['eta'])==F(spec['eta']) and record['cutoff']==cutoff,
                'certificate coordinate or cutoff mismatch')
        require(runner.certificates.verify(record),'certificate arithmetic replay failed')
    rungs=stage['rungs']; final=rungs[-1]
    for rung in rungs:
        if rung['status']=='failed':
            reason(rung)
        else:
            require(rung['status']=='completed','nonterminal certificate rung')
            check(rung['record'],rung['cutoff'])
        if rung['retime_status'] in ('completed','failed'):
            check(rung['initial_record'],rung['cutoff'])
            require(list(map(F,rung['initial_record']['times']))==[F(0)],'initial certificate clock mismatch')
        else:
            require(rung['retime_status']=='not_attempted','unknown retiming status')
            if rung['status']=='completed':
                require(list(map(F,rung['record']['times']))==[F(0)],'unretimed certificate clock mismatch')
    source=final.get('initial_record',final.get('record'))
    times=None
    if source is not None and (final['status']=='completed' or 'initial_record' in final):
        selected=runner.certificates.verified_channels(source)
        if len(selected)==2 and all(c['threshold']['status']=='resolved' for c in selected):
            reference=min((F(c['threshold']['gap_interval'][0])+F(c['threshold']['gap_interval'][1]))/2 for c in selected)
            times=[F(float(F(t)/reference)) for t in tau]
    for rung in rungs:
        if rung['retime_status']=='completed':
            require(rung['status']=='completed' and times is not None,'invalid completed retiming')
            require(encoded(rung['record'])==encoded(runner.retime(rung['initial_record'],times)),
                    'retimed certificate differs from frozen clock replay')
        elif rung['retime_status']=='failed':
            require(rung['status']=='failed','failed retiming marked completed')
    if 'result' in stage:
        require(final['status']=='completed' and encoded(stage['result'])==encoded(final['record']['result']),
                'stage certificate differs from finest record')
    if stage['status']=='completed':
        require(all(r['status']=='completed' for r in rungs) and final['retime_status']=='completed',
                'completed certificate stage has incomplete requests')
        require('result' in stage and encoded(stage['times'])==encoded(times),
                'completed certificate stage clock or result missing')
        require(stage['clock_rule']=='binary64-rounded tau / minimum accessible-gap midpoint at finest certificate',
                'clock rule mismatch')
    elif stage['status']=='unresolved':
        require(all(r['status']=='completed' and r['retime_status']=='not_attempted' for r in rungs)
                and times is None and 'result' in stage,'unresolved certificate contradicts available clock')
        reason(stage)
    else:
        require(stage['status']=='failed','unknown certificate stage outcome'); reason(stage)
    return final['record'] if final['retime_status']=='completed' else None


def original_stage(stage):
    value=deepcopy(stage)
    if 'pre_replay_status' in value:
        require(value['status']=='failed','replay-invalid stage is not failed')
        value['status']=value.pop('pre_replay_status')
    return value


def replay_cell(spec,cell,manifest):
    stages=cell['stages']
    runner.adapter.STAGE_VALIDATOR.validate(stages)
    scalar=runner.scalar_replay.verify(spec['theory'],spec['g'],spec['eta'],spec['cutoffs'],spec['grids'],
                                       original_stage(stages['scalar']))
    require(encoded(cell['scalar_replay'])==encoded(scalar),'stored scalar replay verdict mismatch')
    if scalar['status']=='invalid':
        require(stages['scalar']['status']=='failed','invalid scalar evidence not failed')
    final=certificate_stage(spec,stages['certificates'],manifest['tau'])
    if final is not None:
        temporal=runner.temporal_replay.verify(final,original_stage(stages['temporal']),spec['grids'],manifest['tolerances'])
        require(encoded(cell['temporal_replay'])==encoded(temporal),'stored temporal replay verdict mismatch')
        if temporal['status']=='invalid':
            require(stages['temporal']['status']=='failed','invalid temporal evidence not failed')
    else:
        temporal={'status':'not_attempted','reason':'verified temporal prerequisite unavailable','common_sample_pairs':[]}
        require(encoded(cell['temporal_replay'])==encoded(temporal),'unexpected temporal evidence without finest certificate')
        require(stages['temporal']['status'] in ('failed','unresolved'),'propagation completed without finest certificate')
        for rung in stages['temporal']['result']['rungs']:
            for slot in rung['evolutions']:
                require(slot['status'] in ('failed','unresolved') and 'result' not in slot,
                        'skipped propagation contains successful evidence'); reason(slot)
    adapted=runner.adapter.adapt_cell(spec['theory'],spec['g'],spec['eta'],stages)
    require(encoded(cell['adaptation'])==encoded(adapted),'stored adaptation mismatch')
    accuracy=runner.scalar_accuracy(stages,spec['theory'])
    require(encoded(cell['scalar_accuracy'])==encoded(accuracy),'stored exact scalar accuracy mismatch')
    common=temporal['common_sample_pairs'] if temporal['status']=='verified' and stages['temporal']['status']=='completed' else []
    qualified=(adapted['status']=='available' and scalar['status']=='verified'
               and scalar['cross_representation_agreement'] is True
               and stages['certificates'].get('result',{}).get('scalar_budget_met') is True
               and accuracy['qualifies'] and bool(common))
    expected='failure' if adapted['status']=='failure' else 'development_qualified' if qualified else 'unresolved'
    require(cell['status']==expected and cell['registered_window'] is None
            and cell['qualifying_common_sample_pairs']==common,'stored cell outcome mismatch')
    return expected


def replay(result):
    encoded(result)
    manifest=result['manifest']
    runner.validate(manifest)
    require(result['source_verification']=='passed','current-source replay requires successful source audit')
    require(runner.accounting(manifest,result) and result['accounting_verified'] is True,
            'incomplete or contradictory request accounting')
    controls_pass=control_verdict(result['control_preflight'])
    outcomes=[]
    for spec,cell in zip(manifest['cells'],result['cells']):
        if not controls_pass:
            require(cell['status']=='failure','failed controls did not invalidate cell')
            expected=runner.planned_stages(spec,manifest['tolerances'])
            for stage in expected.values():
                runner.terminalize(stage,'failed','required control preflight failed; cell not executed')
            require(encoded(cell['stages'])==encoded(expected),'failed controls retain unexpected cell work')
            outcomes.append('failure')
        else:
            outcomes.append(replay_cell(spec,cell,manifest))
    state='instrument_failure' if not controls_pass else 'completed_with_failures' if 'failure' in outcomes else 'completed'
    require(result['state']==state,'run outcome mismatch')
    verdict={'status':'verified','run_state':state,'cell_outcomes':outcomes,'targets_run':0,
             'scope':'current-source stored arithmetic and outcomes; control verdicts and operational failures not authenticated'}
    if 'whole_result_replay' in result:
        require(encoded(result['whole_result_replay'])==encoded(verdict),'stored whole-result replay verdict mismatch')
    return verdict


def verify(result):
    try:
        return replay(result)
    except (KeyError,TypeError,ValueError,ArithmeticError,IndexError,ValidationError) as exc:
        return {'status':'invalid','reason':f'{type(exc).__name__}: {exc}','targets_run':0}
