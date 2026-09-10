"""Presentation-only fixtures preserve unavailable and broad interval evidence."""
from copy import deepcopy
import contextlib
import io
import unittest

import vacuum_selected_report as report


def fixture():
    # Synthetic reporting rows, not numerical target evaluations.
    rows=[{'id':f'fixture-{i}','theory':'SU2','g':'1','eta':'0','status':'failure',
           'full_gap_interval':None,'thresholds':{},'constraints':{'complete':False},
           'raw':{'path':f'cells/{i:02d}.json.gz','sha256':'fixture','json_sha256':'fixture'},
           'verification':{'status':'verified','outcome':'failure'},
           'vacuum_component_intervals':{k:None for k in report.VACUUM_COMPONENTS}}
          for i in range(42)]
    value={'data':{'selected-summary.json':{'registration_commit':'fixture','registration_sha256':'fixture-sha','cells':rows,
                'verification':{'status':'verified','cells':42},'deformation_comparisons':[]},
            'selected-registration.json':{'registered':True,'target_execution_authorized':True,
                'selected_target_ids':[r['id'] for r in rows]},
            'selected-run/index.json':{'registration_commit':'fixture','registration_sha256':'fixture-sha'},
            'selected-run/verification.json':{'status':'verified','cells':42}}}
    return bind(value)


def bind(value):
    """Bind intentional synthetic outcomes before introducing presentation mutants."""
    data=value['data']; rows=data['selected-summary.json']['cells']
    data['selected-registration.json']['cells']=[{k:r[k] for k in ('id','theory','g','eta')} for r in rows]
    data['selected-run/index.json']['cells']=[{'id':r['id'],'status':r['status'],
        'result':deepcopy(r['raw']),'verification':deepcopy(r['verification'])} for r in rows]
    return value


class SelectedReportTests(unittest.TestCase):
    def check(self,value):
        namespace={}; exec(report.CHECKS,namespace)
        with contextlib.redirect_stdout(io.StringIO()):
            return namespace['verify_selected'](value)

    def test_failed_free_rows_with_missing_evidence_are_retained(self):
        self.assertEqual(self.check(fixture()),42)

    def test_broad_gap_and_signed_moment_intervals_remain_unresolved(self):
        value=fixture(); row=value['data']['selected-summary.json']['cells'][0]
        row.update(status='unresolved',full_gap_interval=['-1','4'])
        row['vacuum_component_intervals']['mean_P']=['-1/10','1/10']
        self.assertEqual(self.check(bind(value)),42)
        row.update(status='instrument_agreement',constraints={'complete':True})
        with self.assertRaises(AssertionError):self.check(bind(value))

    def test_vacuum_component_difference_uses_outward_subtraction(self):
        value=fixture(); summary=value['data']['selected-summary.json']
        base,changed=summary['cells'][:2]
        base['vacuum_component_intervals']['mean_P']=['-1/10','1/10']
        changed['eta']='1'
        changed['vacuum_component_intervals']['mean_P']=['1/5','2/5']
        difference=report.subtract(changed['vacuum_component_intervals']['mean_P'],
                                   base['vacuum_component_intervals']['mean_P'])
        self.assertEqual(difference,['1/10','1/2'])
        summary['deformation_comparisons']=[{'cell':changed['id'],'reference':base['id'],
                                            'difference_intervals':{'mean_P':difference}}]
        self.assertEqual(self.check(bind(value)),42)
        invalid=deepcopy(value)
        invalid['data']['selected-summary.json']['deformation_comparisons'][0]['difference_intervals']['mean_P']=['0','0']
        with self.assertRaises(AssertionError):self.check(invalid)

    def test_finite_family_minimum_is_exact_and_requires_every_gap(self):
        value=fixture(); summary=value['data']['selected-summary.json']
        summary['finite_family_full_gap_lower']=None
        self.assertEqual(self.check(value),42)
        for row in summary['cells']:row['full_gap_interval']=['2999/1000','3001/1000']
        summary['finite_family_full_gap_lower']='2999/1000'
        self.assertEqual(self.check(value),42)
        summary['finite_family_full_gap_lower']='3'
        with self.assertRaises(AssertionError):self.check(value)

    def test_coordinate_status_reference_and_verdict_drift_rejected(self):
        mutations=[lambda d:d['selected-summary.json']['cells'][0].update(g='2'),
                   lambda d:d['selected-summary.json']['cells'][0].update(theory='U1'),
                   lambda d:d['selected-summary.json']['cells'][0].update(eta='1'),
                   lambda d:d['selected-summary.json']['cells'][0].update(status='unresolved'),
                   lambda d:d['selected-summary.json']['cells'][0]['raw'].update(path='other.json.gz'),
                   lambda d:d['selected-summary.json']['cells'][0]['verification'].update(status='invalid'),
                   lambda d:d['selected-summary.json']['verification'].update(cells=41),
                   lambda d:d['selected-summary.json'].update(registration_sha256='different')]
        for mutate in mutations:
            value=fixture(); mutate(value['data'])
            with self.assertRaises(AssertionError):self.check(value)


if __name__=='__main__':unittest.main()
