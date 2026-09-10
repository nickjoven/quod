"""Adapt verified certificate/stage records; no solver or target-run entry point."""
from copy import deepcopy
from fractions import Fraction as F
import json

from jsonschema import Draft202012Validator

import vacuum_channel_contract as channels
import vacuum_result_contract as previous

STAGE_SCHEMA = json.loads((previous.DIRECTORY / 'future-stage-input.schema.json').read_text())
Draft202012Validator.check_schema(STAGE_SCHEMA)
STAGE_VALIDATOR = Draft202012Validator(STAGE_SCHEMA)


def adapt_channels(theory, g, eta, result):
    """Producer must verify the certificate against the declared coordinates.

    At eta=0, intersect analytically forbidden weights with the exact zero.
    Reject a supplied enclosure that contradicts that selection identity.
    No such refinement is available for an uncertain interacting overlap.
    """
    g, eta = F(str(g)), F(str(eta))
    if theory not in ('SU2', 'U1') or g <= 0 or eta < 0:
        raise ValueError('valid theory, positive g and nonnegative eta required')
    if result.get('bound_status') != 'bounded' or result.get('overlaps') is None or result.get('vacuum') is None:
        return []
    output = []
    for observable in ('P', 'P2'):
        channel = previous.channel_from_certificate(theory, str(g), str(eta), result, observable)
        if eta == 0:
            active = 1 if observable == 'P' else 2
            for state in channel['states']:
                if state['level'] != active:
                    lo, hi = map(F, state['weight_interval'])
                    if not lo <= 0 <= hi:
                        raise ValueError('certificate contradicts free selection identity')
                    state['weight_interval'] = (F(0), F(0))
                    state['exact_zero_rule'] = 'free_polynomial_selection'
        output.append({'certificate': channel, 'threshold': channels.threshold(channel)})
    return previous.shared.encode(output)


def adapt_cell(theory, g, eta, stages):
    """Retain all supplied stage evidence, including partial/failed stages.

    This is an adapter record, not a target execution envelope or a precision
    verdict. A completed certificate stage supplies its verified result in
    `result`; raw rung history can accompany it under any other stage key.
    """
    g, eta = F(str(g)), F(str(eta))
    if theory not in ('SU2', 'U1') or g <= 0 or eta < 0:
        raise ValueError('valid theory, positive g and nonnegative eta required')
    out = {'theory': theory, 'g': str(g), 'eta': str(eta), 'status': 'unresolved',
           'reason': 'stage evidence incomplete', 'channels': [],
           'stages': deepcopy(stages), 'precision_status': 'not_assessed',
           'target_execution_authorized': False}
    error = next(STAGE_VALIDATOR.iter_errors(stages), None)
    if error is not None:
        out.update(status='failure', reason='invalid stage evidence: '+error.message)
        return out
    certificate = stages['certificates']
    if certificate['status'] == 'completed':
        try:
            out['channels'] = adapt_channels(theory, g, eta, certificate['result'])
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            out.update(status='failure', reason=f'certificate adaptation failed: {exc}')
            return out
    failures = [name for name, stage in stages.items() if stage['status'] == 'failed']
    if failures:
        out.update(status='failure', reason='failed stages: '+', '.join(failures))
    elif any(stage['status'] == 'unresolved' for stage in stages.values()):
        out['reason'] = 'one or more stages unresolved; retained partial evidence'
    elif len(out['channels']) != 2 or any(c['threshold']['status'] != 'resolved' for c in out['channels']):
        out['reason'] = 'certificate or accessible threshold unresolved'
    else:
        out.update(status='available', reason='stage outputs and thresholds available; precision not assessed')
    return out
