"""Resolve observable thresholds without discarding uncertain low-state weights."""
from fractions import Fraction as F

import vacuum_time_windows as windows


def bounds(value, nonnegative=False):
    if len(value)!=2:
        raise ValueError('two interval endpoints required')
    lo,hi=map(F,value)
    if hi<lo or (nonnegative and lo<0):
        raise ValueError('invalid interval')
    return lo,hi


def threshold(channel):
    """States must cover consecutive ordered levels in the declared sector.

    This checks a certificate interface, not a new spectral theorem. Producers
    must certify ordering, omitted-spectrum floor and sector invariance.
    """
    theory,observable=channel['theory'],channel['observable']
    if theory not in ('SU2','U1') or observable not in ('P','P2'):
        raise ValueError('unknown theory or observable')
    expected_scope='full' if theory=='SU2' else 'reflection_even'
    if channel['spectral_scope']!=expected_scope or not channel['ordering_certified']:
        raise ValueError('ordered invariant-sector certificate required')
    g=F(channel['g'])
    if g<=0:
        raise ValueError('positive model coupling required')
    states=channel['states']
    if [s['level'] for s in states]!=list(range(1,len(states)+1)):
        raise ValueError('missing or unordered retained levels')
    tail_floor=F(channel['omitted_gap_lower'])
    tail_weight=bounds(channel['omitted_weight_interval'],True)
    previous=F(0)
    parsed=[]
    for state in states:
        gap=bounds(state['gap_interval'],True)
        weight=bounds(state['weight_interval'],True)
        if gap[0]<previous or weight[1]>1:
            raise ValueError('invalid ordered gap or bounded-observable weight')
        if F(channel['eta'])==0:
            level=state['level']
            exact=g*g*level*(level+2) if theory=='SU2' else 4*g*g*level*level
            if not gap[0]<=exact<=gap[1]:
                raise ValueError('free gap interval excludes analytic spectrum')
            active_level=1 if observable=='P' else 2
            active_weight=(F(1,4) if observable=='P' else F(1,16)) if theory=='SU2' else (F(1,2) if observable=='P' else F(1,8))
            exact_weight=active_weight if level==active_level else F(0)
            if not weight[0]<=exact_weight<=weight[1]:
                raise ValueError('free weight interval excludes analytic overlap')
        previous=gap[0]
        rule=state['exact_zero_rule']
        if rule is not None:
            active_level=1 if observable=='P' else 2
            if (rule!='free_polynomial_selection' or F(channel['eta'])!=0
                or state['level']==active_level or weight!=(F(0),F(0))):
                raise ValueError('unsupported exact-zero assertion')
        parsed.append((state,gap,weight))
    for state,gap,weight in parsed:
        if state['exact_zero_rule'] is not None:
            continue
        if weight[0]<=0:
            return {'status':'unresolved','reason':'earlier or leading overlap includes zero',
                    'leading_level':None,'gap_interval':None,'full_gap_claim_supported':False}
        if gap[0]<=0 or (tail_weight[1]>0 and tail_floor<gap[1]):
            return {'status':'unresolved','reason':'positive threshold or omitted-spectrum separation unavailable',
                    'leading_level':None,'gap_interval':None,'full_gap_claim_supported':False}
        return {'status':'resolved','reason':'nonzero overlap with all preceding levels exactly excluded',
                'leading_level':state['level'],'gap_interval':gap,
                'full_gap_claim_supported':theory=='SU2' and state['level']==1}
    return {'status':'unresolved','reason':'no certified nonzero retained overlap',
            'leading_level':None,'gap_interval':None,'full_gap_claim_supported':False}


def assess(channel,left,right,observed_left,observed_right,duration):
    selected=threshold(channel)
    if selected['status']!='resolved':
        return {'threshold':selected,'window':{'status':'unresolved','qualifies':False,'reason':selected['reason']}}
    return {'threshold':selected,'window':windows.assess_pair(bounds(left,True),bounds(right,True),
        observed_left,observed_right,F(duration),selected['gap_interval'],True)}
