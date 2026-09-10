"""Registered authority, retained evidence and solver-free replay tests."""
from copy import deepcopy
import gzip
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import vacuum_registered_run as runner
from test_vacuum_run_envelope import manifest


class RegisteredRunTests(unittest.TestCase):
    def test_exact_selection_and_mutations(self):
        value=runner.registration()
        self.assertTrue(runner.validate(value))
        self.assertEqual(len(value['cells']),42)
        for mutate in (lambda v:v['cells'].pop(),lambda v:v['selected_target_ids'].reverse(),
                       lambda v:v['cells'][0].update(g='1'),lambda v:v['tau'].append('25'),
                       lambda v:v['failure_rules'].update(unresolved='retry')):
            changed=deepcopy(value); mutate(changed)
            with self.assertRaises(Exception):runner.validate(changed)

    def test_commit_gate_before_solver(self):
        with patch.object(runner.core,'process_cell') as solver:
            with self.assertRaisesRegex(ValueError,'commit'):
                runner.run(runner.registration(),None)
        solver.assert_not_called()

    def test_registered_cell_path_on_free_development_calibration(self):
        value=manifest(('SU2','U1'))
        for spec in value['cells']:
            spec.update(cutoffs=[8],grids=[512])
            snapshots=[]
            cell,result=runner.execute_cell(spec,value,snapshots.append)
            self.assertEqual(result,{'status':'verified','outcome':'instrument_agreement'})
            self.assertGreater(len(snapshots),2)
            with patch.object(runner.core.scalar,'run',side_effect=AssertionError('solver')):
                self.assertEqual(runner.assess(spec,cell,value),result)
            changed=deepcopy(cell); changed['id']='wrong'
            self.assertEqual(runner.assess(spec,changed,value)['status'],'invalid')
            changed=deepcopy(cell); changed['stages']['certificates']['rungs'].pop()
            self.assertEqual(runner.assess(spec,changed,value)['status'],'invalid')

    def test_checkpoint_failure_stops_before_solver(self):
        value=manifest()
        with patch.object(runner.core,'process_cell') as solver:
            with self.assertRaises(runner.core.CheckpointFailure):
                runner.execute_cell(value['cells'][0],value,lambda _:(_ for _ in ()).throw(OSError('disk full')))
        solver.assert_not_called()

    def test_append_only_evidence(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(runner,'OUTPUT',Path(directory)):
            path=Path(directory)/'cells/00.json.gz'
            ref=runner.write_gzip(path,{'evidence':[1,2]})
            self.assertEqual(runner.digest(path.read_bytes()),ref['sha256'])
            self.assertEqual(runner.digest(gzip.decompress(path.read_bytes())),ref['json_sha256'])
            with self.assertRaises(FileExistsError):runner.write_gzip(path,{'evidence':[]})

    def test_checkpoint_inventory_and_order_cannot_be_truncated(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(runner,'OUTPUT',Path(directory)):
            index={'cells':[{'id':'calibration-a'},{'id':'calibration-b'}],'checkpoints':[]}
            for number,row in enumerate(index['cells']):
                for sequence in range(2):
                    index['checkpoints'].append(runner.write_gzip(
                        Path(directory)/'checkpoints'/f'{number:02d}-{sequence:03d}.json.gz',
                        {'id':row['id'],'step':sequence}))
            self.assertEqual(runner.checkpoint_snapshots(index),
                             [{'id':'calibration-a','step':1},{'id':'calibration-b','step':1}])
            for mutate in (lambda x:x.update(checkpoints=[]),
                           lambda x:x['checkpoints'].pop(),
                           lambda x:x['checkpoints'].reverse(),
                           lambda x:x['checkpoints'].append(deepcopy(x['checkpoints'][0])),
                           lambda x:x['cells'][0].update(id='wrong-cell')):
                changed=deepcopy(index); mutate(changed)
                with self.assertRaises(ValueError):runner.checkpoint_snapshots(changed)

    def test_ordinary_solver_failure_preserves_next_calibration_cell(self):
        value=manifest(('SU2','U1'))
        original=runner.core.scalar.run
        calls=[]
        def injected(*args,**kwargs):
            calls.append(args[0])
            if len(calls)==1:raise RuntimeError('injected scalar solver failure')
            return original(*args,**kwargs)
        outcomes=[]
        with patch.object(runner.core.scalar,'run',side_effect=injected):
            for spec in value['cells']:
                spec.update(cutoffs=[8],grids=[512])
                snapshots=[]
                cell,verdict=runner.execute_cell(spec,value,snapshots.append)
                outcomes.append(verdict['outcome'])
                self.assertTrue(snapshots)
                self.assertEqual(cell['stages']['temporal']['status'],'completed')
        self.assertEqual(calls,['SU2','U1'])
        self.assertEqual(outcomes,['failure','instrument_agreement'])

    def test_terminal_audit_requires_source_pass_and_final_checkpoint_match(self):
        # Integrity-only fixture: no scientific records or numerical requests.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            registration=root/'registration.json'; registration.write_text('{}')
            with patch.object(runner,'OUTPUT',root),patch.object(runner,'REGISTRATION',registration),patch.object(
                    runner,'committed',return_value=True),patch.object(runner.replay,'control_verdict',return_value=True):
                value={'selected_target_ids':['calibration'],'cells':[{'id':'calibration'}]}
                refs=[runner.write_gzip(root/'checkpoints'/f'00-{i:03d}.json.gz',
                                       {'id':'calibration','step':i}) for i in range(2)]
                cell=runner.write_gzip(root/'cells/00.json.gz',{'id':'calibration','step':2})
                index={'registration_commit':'0'*40,'registration_sha256':runner.digest(b'{}'),
                       'source_verification':'failed','control_preflight':{},'checkpoints':refs,
                       'cells':[{'id':'calibration','result':cell}]}
                (root/'index.json').write_text(json.dumps(index))
                with self.assertRaisesRegex(ValueError,'successful final source'):
                    runner.verify_run(value,'0'*40)
                index['source_verification']='passed'
                (root/'index.json').write_text(json.dumps(index))
                with self.assertRaisesRegex(ValueError,'last preserved checkpoint'):
                    runner.verify_run(value,'0'*40)

    def test_control_failure_retains_all_unrun(self):
        value=runner.registration()
        with tempfile.TemporaryDirectory() as directory,patch.object(runner,'OUTPUT',Path(directory)/'run'),patch.object(
                runner,'committed',return_value=True),patch.object(runner.REGISTRATION.__class__,'read_bytes',return_value=b'{}'),patch.object(
                runner.core,'control_preflight',return_value={'bad':'control'}),patch.object(runner.core,'process_cell') as solver:
            result=runner.run(value,'0'*40)
        solver.assert_not_called()
        self.assertEqual(result['state'],'instrument_failure')
        self.assertEqual(result['attempted'],0)
        self.assertEqual(len(result['cells']),42)
        self.assertTrue(all(row['status']=='unrun' for row in result['cells']))


if __name__=='__main__':unittest.main()
