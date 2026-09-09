"""Exact-zero selection differs from an unresolved small positive overlap."""
import copy
from fractions import Fraction as F
import unittest

import vacuum_channel_contract as contract
import vacuum_intervals as intervals


def free_channel(theory='SU2',observable='P2'):
    gaps=[F(3,4),F(2),F(15,4)] if theory=='SU2' else [F(1),F(4),F(9)]
    active=1 if observable=='P' else 2
    weight=F(1,4) if observable=='P' else F(1,16)
    if theory=='U1':
        weight=F(1,2) if observable=='P' else F(1,8)
    return {'theory':theory,'observable':observable,'g':'1/2','eta':'0',
        'spectral_scope':'full' if theory=='SU2' else 'reflection_even','ordering_certified':True,
        'states':[{'level':i,'gap_interval':[g,g],'weight_interval':[weight,weight] if i==active else [F(0),F(0)],
                   'exact_zero_rule':None if i==active else 'free_polynomial_selection'} for i,g in enumerate(gaps,1)],
        'omitted_gap_lower':F(6) if theory=='SU2' else F(16),'omitted_weight_interval':[F(0),F(0)]}


class ChannelContractTests(unittest.TestCase):
    def test_free_p2_uses_second_accessible_level(self):
        for theory in ('SU2','U1'):
            c=free_channel(theory)
            selected=contract.threshold(c)
            self.assertEqual(selected['leading_level'],2)
            self.assertFalse(selected['full_gap_claim_supported'])
            gap=selected['gap_interval'][0]
            weight=c['states'][1]['weight_interval'][0]
            left=(weight,weight)
            right=tuple(weight*x for x in intervals.exp_negative(gap))
            result=contract.assess(c,left,right,float(weight),float(sum(right)/2),F(1))
            self.assertTrue(result['window']['qualifies'])

    def test_uncertain_low_overlap_cannot_be_skipped(self):
        c=free_channel()
        c['eta']='1'
        for state in c['states']:
            state['exact_zero_rule']=None
        c['states'][0].update(exact_zero_rule=None,weight_interval=[F(0),F(1,10**30)])
        self.assertEqual(contract.threshold(c)['status'],'unresolved')
        c['states'][0]['weight_interval']=[F(1,10**31),F(1,10**30)]
        self.assertEqual(contract.threshold(c)['leading_level'],1)

    def test_exact_zero_requires_valid_rule(self):
        c=free_channel()
        c['eta']='1'
        with self.assertRaisesRegex(ValueError,'exact-zero'):
            contract.threshold(c)
        c=free_channel()
        c['states'][0]['exact_zero_rule']=None
        self.assertEqual(contract.threshold(c)['status'],'unresolved')
        c['states'][0]['weight_interval']=[F(1,100),F(1,50)]
        with self.assertRaisesRegex(ValueError,'analytic overlap'):
            contract.threshold(c)

    def test_missing_levels_and_omitted_low_spectrum(self):
        c=free_channel()
        c['states'].pop(0)
        with self.assertRaisesRegex(ValueError,'levels'):
            contract.threshold(c)
        c=free_channel()
        c['omitted_weight_interval']=[0,F(1,10**20)]
        c['omitted_gap_lower']=F(1,10)
        self.assertEqual(contract.threshold(c)['status'],'unresolved')

    def test_no_qualified_window_from_nonpositive_correlations(self):
        c=free_channel(observable='P')
        result=contract.assess(c,[1,1],[F(1,2),F(1,2)],0,F(1,2),1)
        self.assertFalse(result['window']['qualifies'])


if __name__=='__main__':
    unittest.main()
