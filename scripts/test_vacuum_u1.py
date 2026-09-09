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
import vacuum_u1 as u1
import vacuum_u1_run as runner


class U1Tests(unittest.TestCase):
    def test_calibration_and_named_mutants(self):
        result=u1.calibration()
        self.assertTrue(result['pass'],result)
        self.assertTrue(all(result['mutants_rejected'].values()))

    def test_parity_embeddings_are_complete_and_orthogonal(self):
        even,odd=u1.parity_embeddings(32)
        np.testing.assert_allclose((even.T@even).toarray(),np.eye(17),atol=1e-15)
        np.testing.assert_allclose((odd.T@odd).toarray(),np.eye(15),atol=1e-15)
        np.testing.assert_allclose((even.T@odd).toarray(),0,atol=1e-15)
        np.testing.assert_allclose((even@even.T+odd@odd.T).toarray(),np.eye(32),atol=1e-15)

    def test_full_gap_is_not_even_observable_threshold(self):
        fourier=u1.fourier(.1,1,320)
        angle=u1.angle(.1,1,4800)
        self.assertLess(fourier['full_gap'],.51*fourier['first_even_gap'])
        self.assertTrue(u1.within_goal(u1.differences(angle,fourier)))
        self.assertLess(np.max(abs(np.asarray(angle['odd_overlap_numerical']))),1e-12)
        self.assertEqual(fourier['even_parity_defect'],0)

    def test_free_dense_matrix_and_fourth_order_ladder(self):
        matrix,_=u1.periodic_matrix(.5,0,16)
        eigen=np.linalg.eigvalsh(matrix.toarray())
        h=2*np.pi/16
        lam=4*np.sin(np.pi*np.arange(16)/16)**2/h**2
        expected=np.sort(.25*(lam+h*h*lam*lam/12))
        np.testing.assert_allclose(eigen,expected,atol=1e-12)
        reference=u1.fourier(.1,1,320)
        errors=[max(u1.differences(u1.angle(.1,1,n),reference)['even_gap_relative']) for n in (600,1200,2400)]
        self.assertTrue(14 < errors[0]/errors[1] < 18,errors)
        self.assertTrue(14 < errors[1]/errors[2] < 18,errors)

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
                 patch.object(baseline,'CHARACTER_J',(4,8)), \
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
