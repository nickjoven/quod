"""Independent U(1) parity, measure, boundary, and runner checks."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import vacuum_development as baseline
import vacuum_u1_design as u1
import vacuum_u1_design_run as runner


class U1DesignTests(unittest.TestCase):
    def test_calibration_and_named_mutants(self):
        result=u1.calibration()
        self.assertTrue(result['pass'],result)
        self.assertTrue(all(result['mutants_rejected'].values()))

    def test_recovered_free_and_interacting_matrix(self):
        g,eta,k=.7,1.,16
        n=np.arange(-k,k+1)
        matrix=np.diag(4*g*g*n*n)+np.diag(np.full(2*k,-eta/g**2),1)+np.diag(np.full(2*k,-eta/g**2),-1)
        eigen=np.linalg.eigvalsh(matrix)
        record=u1.fourier(g,eta,k)
        self.assertAlmostEqual(record['E0'],eigen[0],places=11)
        self.assertAlmostEqual(record['full_gap'],eigen[1]-eigen[0],places=11)
        free=u1.fourier(g,0,k)
        self.assertAlmostEqual(free['full_gap'],4*g*g,places=12)
        self.assertNotAlmostEqual(record['moments'][0],u1.legacy.fourier(g,eta,k)['moments'][0],places=5)

    def test_recovered_manifest_and_independent_angle(self):
        self.assertEqual(u1.FOURIER_CUTOFFS,(40,80,160,320,640))
        fourier=u1.fourier(.1,1,640)
        angle=u1.angle(.1,1,4800)
        self.assertTrue(u1.within_goal(u1.differences(angle,fourier)))
        self.assertLess(fourier['full_gap'],fourier['first_even_gap'])
        self.assertEqual(fourier['convention'],u1.CONVENTION)

    def test_invalid_and_nonfinite_values_cannot_pass(self):
        for g in (0,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                u1.fourier(g,1,20)
        with self.assertRaises(ValueError):
            u1.angle(.5,1,15)
        diff={'moment_absolute':[0.]*5,'even_gap_relative':[0.]*3,'full_gap_relative':float('nan')}
        self.assertFalse(u1.within_goal(diff))

    def test_nonfinite_rung_does_not_cancel_later_cells(self):
        original=u1.fourier
        calls=[]
        def injected(*args):
            calls.append(1)
            result=original(*args)
            if len(calls)==2:
                result['full_gap']=float('nan')
            return result
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json'
            with patch.object(baseline,'G_VALUES',(.1,.5)), \
                 patch.object(u1,'FOURIER_CUTOFFS',(4,8)), \
                 patch.object(baseline,'ANGLE_INTERIORS',(16,32)), \
                 patch.object(u1,'fourier',side_effect=injected), \
                 patch.object(u1,'calibration',return_value={'pass':True}), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(path),1)
                report=json.loads(path.read_text())
                self.assertTrue(runner.accounting(report))
            self.assertEqual(len(calls),4)
            self.assertEqual([c['status'] for c in report['cells']],['failure','unresolved'])
            self.assertNotIn('result',report['cells'][0]['rungs'][1])

    def test_calibration_failure_checkpoints_all_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json'
            with patch.object(u1,'calibration',side_effect=RuntimeError('injected')),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(path),1)
            report=json.loads(path.read_text())
            self.assertEqual(report['state'],'instrument_failure')
            self.assertEqual(sum(len(c['rungs']) for c in report['cells']),90)


if __name__=='__main__':
    unittest.main()
