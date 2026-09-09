"""Replay all U(1) exact sector, overlap, moment and correlation certificates."""
from fractions import Fraction as F
import hashlib
import json
import unittest

import vacuum_development as baseline
import vacuum_u1_design_certificate_run as runner


class U1DesignCertificateArchiveTests(unittest.TestCase):
    def test_full_exact_replay_and_budgets(self):
        raw=(baseline.ROOT/'research/vacuum-spectrum/u1-design-certificates.json').read_bytes()
        report=json.loads(raw)
        self.assertEqual(report['state'],'completed')
        self.assertTrue(runner.accounting(report))
        self.assertEqual(report['source_sha256'],runner.source_hashes())
        self.assertTrue(report['source_unchanged_during_run'])
        source=(baseline.ROOT/'research/vacuum-spectrum/u1-design-development.json').read_bytes()
        self.assertEqual(report['input_sha256'],hashlib.sha256(source).hexdigest())
        source=json.loads(source)
        doc=(baseline.ROOT/'research/vacuum-spectrum/U1-DESIGN-CERTIFICATES-RUN.md').read_text()
        self.assertIn(hashlib.sha256(raw).hexdigest(),doc)
        for cell,prior in zip(report['cells'],source['cells']):
            self.assertEqual(cell['status'],'unresolved')
            times=[F(t) for t in cell['times']]
            expected=[F(float(t)) for t in runner.np.asarray(runner.TAU)/prior['final']['fourier']['first_even_gap']]
            self.assertEqual(times,expected)
            for rung in cell['rungs']:
                self.assertEqual(rung['status'],'completed')
                record=rung['result']
                self.assertTrue(runner.verify_result(cell['g'],record,times))
                even=runner.decode_eigen(record['even_enclosures'])
                gaps=[(r['lower']-even[0]['upper'],r['upper']-even[0]['lower']) for r in even[1:4]]
                self.assertEqual(record['first_three_even_gap_intervals'],runner.shared.encode(gaps))
                full=record['parity']['full_gap_interval']
                if full is not None:
                    gaps.append(tuple(F(v) for v in full))
                gap_ok=len(gaps)==4 and all(lo>0 and (hi-lo)/(2*lo)<=F(1,10**6) for lo,hi in gaps)
                vacuum=record['vacuum']
                moments=[] if vacuum is None else [*vacuum['raw_moments'][:2],vacuum['covariance'][0][0],
                                                  vacuum['covariance'][1][1],vacuum['covariance'][0][1]]
                moment_ok=len(moments)==5 and all((F(hi)-F(lo))/2<=F(1,10**6) for lo,hi in moments)
                self.assertEqual(record['scalar_budget_met'],bool(gap_ok and moment_ok))
                self.assertEqual(record['bound_status'],'bounded' if record['correlations'] is not None else 'unresolved')
                if record['overlaps'] is not None:
                    self.assertEqual(record['first_even_overlap_certified'],[F(o['weight_lower'])>0 for o in record['overlaps'][0]])
            final=cell['rungs'][-1]['result']
            self.assertTrue(final['scalar_budget_met'])
            self.assertEqual(final['first_even_overlap_certified'],[True,True])
            self.assertTrue(final['parity']['full_gap_odd_certified'])


if __name__=='__main__':
    unittest.main()
