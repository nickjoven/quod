"""Exact parity and squared-hopping checks, including false-certificate mutants."""
import contextlib
import copy
from fractions import Fraction as F
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import vacuum_development as baseline
import vacuum_u1_design_certified as c
import vacuum_u1_design_certificate_run as runner


class U1DesignCertificateTests(unittest.TestCase):
    def test_exact_decimal_parameter_mapping(self):
        d,s,b,tail=c.parameters('.1',1,40,'even')
        self.assertEqual(d[1],F(1,25))
        self.assertEqual(b,-100)
        self.assertEqual(s[0],20000)
        self.assertEqual(tail,F(41**2,25)-200)

    def test_free_sector_endpoints_and_degeneracy(self):
        even=c.enclosures('.5',0,20,'even')
        odd=c.enclosures('.5',0,20,'odd',count=4)
        self.assertTrue(c.verify('.5',0,20,'even',even))
        self.assertTrue(c.verify('.5',0,20,'odd',odd))
        for parity,rows in (('even',even),('odd',odd)):
            for k,row in enumerate(rows):
                exact=F((k+(parity=='odd'))**2)
                self.assertLessEqual(row['lower'],exact)
                self.assertGreaterEqual(row['upper'],exact)
        fields=c.gap_fields(even,odd)
        self.assertTrue(fields['even_ground_below_odd_certified'])
        self.assertFalse(fields['full_gap_odd_certified'])
        self.assertLessEqual(fields['full_gap_interval'][0],F(1))
        self.assertGreaterEqual(fields['full_gap_interval'][1],F(1))

    def test_exact_free_even_observables(self):
        cutoff=20
        eigen=c.enclosures('.5',0,cutoff,'even')
        vectors=np.zeros((4,2*cutoff+1));vectors[0,cutoff]=1
        for k in range(1,4):
            vectors[k,cutoff-k]=vectors[k,cutoff+k]=1
        bounds=[c.vector_bound('.5',0,q,k,eigen) for k,q in enumerate(vectors)]
        overlaps,vacuum=c.observables(vectors,bounds)
        for row,expected in zip(overlaps,((F(1,2),0),(0,F(1,8)),(0,0))):
            for actual,weight in zip(row,expected):
                self.assertLessEqual(actual['weight_lower'],weight)
                self.assertGreaterEqual(actual['weight_upper'],weight)
                self.assertEqual(actual['nonzero_certified'],weight>0)
        for actual,value in zip(vacuum['raw_moments'],(F(0),F(1,2),F(0),F(3,8))):
            self.assertLessEqual(actual[0],value)
            self.assertGreaterEqual(actual[1],value)

    def test_parity_leakage_is_rejected_and_both_tails_count(self):
        eigen=c.enclosures('.5',1,4,'even')
        q=np.zeros(9);q[0]=q[-1]=1
        result=c.vector_bound('.5',1,q,0,eigen)
        mu=result['rayleigh_reference']
        self.assertGreaterEqual(result['residual_norm_upper']**2,(16-mu)**2+32)
        q[0]+=1e-10
        with self.assertRaisesRegex(ValueError,'reflection-even'):
            c.vector_bound('.5',1,q,0,eigen)

    def test_replay_detects_false_endpoint_and_vector_bounds(self):
        record=runner.shared.encode(runner.calculate(.7,20,[F(0),F(1)]))
        self.assertTrue(runner.verify_result(.7,record,[F(0),F(1)]))
        mutated=copy.deepcopy(record)
        mutated['odd_enclosures'][0]['upper']='-1000'
        self.assertFalse(runner.verify_result(.7,mutated,[F(0),F(1)]))
        mutated=copy.deepcopy(record)
        mutated['vector_bounds'][0]['distance_upper']='0'
        self.assertFalse(runner.verify_result(.7,mutated,[F(0),F(1)]))

    def test_nonfinite_failure_retains_remaining_requests(self):
        original=runner.calculate
        calls=[]
        def injected(*args):
            calls.append(1)
            result=original(*args)
            if len(calls)==2:
                result['invalid']=float('nan')
            return result
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json'
            with patch.object(baseline,'G_VALUES',(.1,.15)),patch.object(runner.development.u1,'FOURIER_CUTOFFS',(4,8)), \
                 patch.object(runner.development,'accounting',return_value=True), \
                 patch.object(runner,'calculate',side_effect=injected),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(output),1)
                report=json.loads(output.read_text())
                self.assertTrue(runner.accounting(report))
            self.assertEqual(len(calls),4)
            self.assertEqual([cell['status'] for cell in report['cells']],['failure','unresolved'])
            self.assertNotIn('result',report['cells'][0]['rungs'][1])


if __name__=='__main__':
    unittest.main()
