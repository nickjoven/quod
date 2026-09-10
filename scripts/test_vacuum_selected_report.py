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


class LiveReportTests(unittest.TestCase):
    def fixture(self):
        import hashlib,json
        value=fixture(); data=value['data']; registration=data['selected-registration.json']
        rows=deepcopy(data['selected-summary.json']['cells'])
        for row in rows:
            row.update(status='unrun',attempted=False,raw=None,thresholds={},finest_certificate=None)
            row.pop('verification')
        rows[0].update(status='running',attempted=True)
        index={'cells':[{'id':r['id'],'status':r['status'],'attempted':r['attempted'],'result':r['raw']} for r in rows]}
        snapshot={'registration':registration,'index':index,'rows':rows,
                  'counts':{'selected':42,'attempted':1,'completed':0,'incomplete':1,'unattempted':41},
                  'snapshot_index_sha256':hashlib.sha256(json.dumps(index,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()}
        return {'data':{'selected-live-snapshot.json':snapshot}}

    def check(self,value):
        namespace={};exec(report.LIVE_CHECKS,namespace)
        with contextlib.redirect_stdout(io.StringIO()):return namespace['verify_live'](value)

    def test_live_inventory_and_certificate_binding(self):
        self.assertEqual(self.check(self.fixture())['incomplete'],1)
        for mutate in (lambda x:x['registration']['cells'].pop(),
                       lambda x:x['index']['cells'].pop(),
                       lambda x:x['index']['cells'][0].update(id='wrong'),
                       lambda x:x['rows'][0].update(full_gap_interval=['1','2'])):
            value=self.fixture(); mutate(value['data']['selected-live-snapshot.json'])
            with self.assertRaises(AssertionError):self.check(value)
        value=self.fixture(); x=value['data']['selected-live-snapshot.json']; row=x['rows'][0]
        row.update(status='instrument_agreement',raw={'path':'fixture'},
                   verification={'status':'verified','outcome':'instrument_agreement'},
                   full_gap_interval=['2','4'],finest_certificate={'theory':'SU2','g':'1','eta':'0',
                   'result':{'first_three_gap_intervals':[['2','4']]}})
        x['index']['cells'][0].update(status=row['status'],result=row['raw'],verification=row['verification'])
        x['counts'].update(completed=1,incomplete=0)
        import hashlib,json
        x['snapshot_index_sha256']=hashlib.sha256(json.dumps(x['index'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        self.check(value)
        row['full_gap_interval']=['3','4']
        with self.assertRaises(AssertionError):self.check(value)

    def test_live_checkpoint_prefix_and_active_extras(self):
        import gzip,json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory, patch.object(report.registered,'OUTPUT',Path(directory)):
            output=Path(directory); (output/'checkpoints').mkdir()
            def write(number,sequence,identity):
                raw=json.dumps({'id':identity,'sequence':sequence}).encode(); compressed=gzip.compress(raw)
                path=f'checkpoints/{number:02d}-{sequence:03d}.json.gz'; (output/path).write_bytes(compressed)
                return {'path':path,'sha256':report.registered.digest(compressed),'json_sha256':report.registered.digest(raw)}
            refs=[write(0,0,'done'),write(0,1,'done'),write(1,0,'active')]
            extra=write(1,1,'active')
            index={'cells':[{'id':'done','attempted':True,'result':{}},{'id':'active','attempted':True,'result':None}],
                   'checkpoints':refs}
            last,audit=report.live_checkpoints(index)
            self.assertEqual(last[0]['id'],'done'); self.assertEqual(audit['listed_verified'],3)
            self.assertEqual(audit['newer_active_files_not_in_snapshot'],[extra['path']])
            for mutated in ([refs[0],refs[2]], [refs[1],refs[0],refs[2]], refs+[refs[2]]):
                with self.assertRaises(ValueError):report.live_checkpoints(dict(index,checkpoints=mutated))
            bad=deepcopy(index); bad['cells'][0]['id']='wrong'
            with self.assertRaises(ValueError):report.live_checkpoints(bad)
            write(0,2,'done')
            with self.assertRaises(ValueError):report.live_checkpoints(index)


if __name__=='__main__':unittest.main()
