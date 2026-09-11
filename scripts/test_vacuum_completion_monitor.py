"""Completion monitoring cannot run targets or publish incomplete evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import vacuum_completion_monitor as monitor


def fixture():
    value=monitor.manifest()
    index={'state':'running','registration_commit':monitor.REGISTRATION_COMMIT,
           'registration_sha256':value['registration_sha256'],'selected':42,'attempted':22,
           'cells':[{'id':name,'attempted':i<22,'result':{'path':f'cells/{i:02d}.json.gz'} if i<21 else None}
                    for i,name in enumerate(monitor.registered.core.baseline.target_ids())]}
    return value,index


class CompletionMonitorTests(unittest.TestCase):
    def test_publication_context_rejects_detached_mismatched_and_multiple_destinations(self):
        import subprocess
        responses=[b'topic\n',b'origin/topic\n',b'git@example.test:repo.git\n',b'git@example.test:repo.git\n']
        with patch.object(monitor.subprocess,'check_output',side_effect=responses):
            context=monitor.publication_context()
        self.assertEqual(context['branch'],'topic')
        for changed in ([responses[0],b'origin/other\n',*responses[2:]],
                        [*responses[:3],b'one\ntwo\n']):
            with patch.object(monitor.subprocess,'check_output',side_effect=changed):
                with self.assertRaises(ValueError):monitor.publication_context()
        with patch.object(monitor.subprocess,'check_output',side_effect=subprocess.CalledProcessError(1,['git'])):
            with self.assertRaisesRegex(ValueError,'attached'):monitor.publication_context()

    def test_branch_remote_and_upstream_changes_drift_manifest(self):
        expected=monitor.manifest()
        for key in ('branch','origin_url','origin_push_url','upstream'):
            changed=dict(expected['publication']);changed[key]='different'
            with patch.object(monitor,'publication_context',return_value=changed):
                self.assertNotEqual(expected,monitor.manifest())

    def test_only_complete_inventory_triggers_finalization(self):
        value,index=fixture()
        self.assertFalse(monitor.inspect(index,value))
        index['state']='completed'
        with self.assertRaisesRegex(ValueError,'incomplete'):monitor.inspect(index,value)
        index['attempted']=42
        for i,row in enumerate(index['cells']):row.update(attempted=True,result={'path':f'cells/{i:02d}.json.gz'})
        self.assertTrue(monitor.inspect(index,value))
        index['cells'].pop()
        with self.assertRaisesRegex(ValueError,'inventory'):monitor.inspect(index,value)

    def test_drift_and_failure_cannot_trigger_finalization(self):
        value,index=fixture()
        for mutate in (lambda x:x.update(registration_sha256='bad'),lambda x:x.update(state='instrument_failure'),
                       lambda x:x['cells'].reverse()):
            changed=deepcopy(index);mutate(changed)
            with self.assertRaises(ValueError):monitor.inspect(changed,value)

    def test_command_plan_contains_no_target_execution(self):
        commands=monitor.commands()
        self.assertEqual(commands[0][2],'verify')
        self.assertEqual(commands[1][1],'scripts/vacuum_selected_report.py')
        self.assertTrue(all('run' not in c for c in commands))

    def test_different_invocation_or_missing_pid_not_accepted(self):
        valid=b'python3\0scripts/vacuum_registered_run.py\0run\0--registration-commit\0'+monitor.REGISTRATION_COMMIT.encode()+b'\0'
        with patch.object(Path,'read_bytes',return_value=valid):self.assertTrue(monitor.original_process_alive(123))
        with patch.object(Path,'read_bytes',return_value=valid.replace(b'run\0',b'prepare\0')):self.assertFalse(monitor.original_process_alive(123))
        with patch.object(Path,'read_bytes',side_effect=FileNotFoundError):self.assertFalse(monitor.original_process_alive(123))

    def test_interruption_stops_monitor_without_restarting_target(self):
        value,index=fixture()
        with tempfile.TemporaryDirectory() as directory,patch.object(monitor,'RUNTIME',Path(directory)),patch.object(
                Path,'read_text',side_effect=[json.dumps(value),json.dumps(index)]),patch.object(
                monitor,'validate'),patch.object(monitor,'manifest',return_value=value),patch.object(monitor,'original_process_alive',return_value=False),patch.object(
                monitor,'finalize') as finalize,patch.object(monitor,'status') as status:
            with self.assertRaisesRegex(RuntimeError,'original process'):monitor.watch(123,'a'*40)
        finalize.assert_not_called()
        self.assertEqual(status.call_args.args[0],'needs_attention')

    def test_source_drift_stops_waiting_before_finalization(self):
        value,index=fixture()
        with tempfile.TemporaryDirectory() as directory,patch.object(monitor,'RUNTIME',Path(directory)),patch.object(
                Path,'read_text',return_value=json.dumps(value)),patch.object(monitor,'validate'),patch.object(
                monitor,'manifest',return_value={}),patch.object(monitor,'finalize') as finalize,patch.object(monitor,'status'):
            with self.assertRaisesRegex(ValueError,'drift'):monitor.watch(123,'a'*40)
        finalize.assert_not_called()

    def test_existing_staged_work_prevents_publication(self):
        value,index=fixture();index['state']='completed';index['attempted']=42
        for i,row in enumerate(index['cells']):row.update(attempted=True,result={'path':f'cells/{i:02d}.json.gz'})
        with patch.object(monitor,'validate'),patch.object(monitor.subprocess,'check_output',return_value=b'user-file\n'),patch.object(
                monitor.subprocess,'run') as command:
            with self.assertRaisesRegex(ValueError,'staged'):monitor.finalize(index,value,'a'*40)
        command.assert_not_called()


    def test_failed_verification_preserves_log_and_never_stages_or_pushes(self):
        import subprocess
        value,index=fixture(); index.update(state='completed',attempted=42,checkpoints=[])
        for i,row in enumerate(index['cells']):row.update(attempted=True,result={'path':f'cells/{i:02d}.json.gz'})
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); data=root/'research/vacuum-spectrum'; (data/'selected-run').mkdir(parents=True)
            calls=[]
            def command(args,**kwargs):
                calls.append(args)
                if args==value['commands'][0]:raise subprocess.CalledProcessError(1,args)
            with patch.object(monitor,'ROOT',root),patch.object(monitor,'D',data),patch.object(
                    monitor,'validate'),patch.object(monitor,'status'),patch.object(
                    monitor.subprocess,'check_output',return_value=b''),patch.object(
                    monitor.subprocess,'run',side_effect=command):
                with self.assertRaises(subprocess.CalledProcessError):monitor.finalize(index,value,'a'*40)
            self.assertEqual(calls[-1],value['commands'][0])
            self.assertTrue((data/'selected-run/completion-validation.txt').exists())
            self.assertFalse(any(c[:2] in (['git','add'],['git','commit'],['git','push']) for c in calls))

    def test_successful_finalization_uses_scoped_paths_after_all_checks(self):
        value,index=fixture(); index.update(state='completed',attempted=42,checkpoints=[{'path':'checkpoints/00-000.json.gz'}])
        for i,row in enumerate(index['cells']):row.update(attempted=True,result={'path':f'cells/{i:02d}.json.gz'})
        verdict={'status':'verified','cells':42,'outcomes':{'instrument_agreement':42}}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); data=root/'research/vacuum-spectrum'; (data/'selected-run').mkdir(parents=True)
            calls=[]
            def command(args,**kwargs):
                calls.append(args)
                if args==value['commands'][0]:(data/'selected-run/verification.json').write_text(json.dumps(verdict))
            def output(args,**kwargs):return b'b'*40 if args==['git','rev-parse','HEAD'] else b''
            with patch.object(monitor,'ROOT',root),patch.object(monitor,'D',data),patch.object(
                    monitor,'validate'),patch.object(monitor,'publication_context',return_value=value['publication']),patch.object(monitor,'status') as status,patch.object(
                    monitor.subprocess,'check_output',side_effect=output),patch.object(
                    monitor.subprocess,'run',side_effect=command):monitor.finalize(index,value,'a'*40)
            self.assertEqual(calls[1:5],value['commands'])
            staged=next(c for c in calls if c[:2]==['git','add'])
            self.assertEqual(staged[2],'--')
            self.assertEqual(len(staged[3:]),6+42+1)
            self.assertTrue(all(p.startswith('research/vacuum-spectrum/') for p in staged[3:]))
            committed=next(c for c in calls if c[:2]==['git','commit'])
            self.assertIn('--only',committed)
            self.assertEqual(committed[committed.index('--')+1:],staged[3:])
            self.assertEqual(calls[-1],['git','push','origin','HEAD:refs/heads/'+value['publication']['branch']])
            self.assertEqual(status.call_args.args[0],'completed_and_pushed')
            self.assertIn('U(1) results remains pending',(data/'AUTONOMOUS-STATUS.md').read_text())


if __name__=='__main__':unittest.main()
