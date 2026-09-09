"""Reproduce U(1) scalar comparisons, parity distinctions, and source hashes."""
import hashlib
import json
import unittest

import vacuum_development as baseline
import vacuum_u1_design as u1
import vacuum_u1_design_run as runner


class U1DesignArchiveTests(unittest.TestCase):
    def test_complete_archive_and_comparisons(self):
        raw=(baseline.ROOT/'research/vacuum-spectrum/u1-design-development.json').read_bytes()
        report=json.loads(raw)
        self.assertEqual(report['state'],'completed')
        self.assertTrue(runner.accounting(report))
        self.assertEqual(report['source_sha256'],runner.source_hashes())
        self.assertTrue(report['source_unchanged_during_run'])
        self.assertTrue(report['calibration']['pass'])
        doc=(baseline.ROOT/'research/vacuum-spectrum/U1-DESIGN-RUN.md').read_text()
        self.assertIn(hashlib.sha256(raw).hexdigest(),doc)
        self.assertEqual(sum(len(c['rungs']) for c in report['cells']),90)
        for cell in report['cells']:
            self.assertEqual(cell['status'],'unresolved')
            for method in ('fourier','angle'):
                final=cell['final'][method]
                runner.validate(final)
                self.assertLess(final['full_gap'],final['first_even_gap'])
                rungs=[r for r in cell['rungs'] if r['method']==method]
                self.assertTrue(all(r['status']=='completed' for r in rungs))
                self.assertEqual(baseline.compact(final),rungs[-1]['result'])
                for previous,current in zip(rungs,rungs[1:]):
                    self.assertEqual(current['result']['adjacent_rung_difference'],
                        u1.differences(current['result'],previous['result']))
            cross=u1.differences(cell['final']['angle'],cell['final']['fourier'])
            self.assertEqual(cell['cross_method_difference'],cross)
            self.assertEqual(cell['scalar_agreement'],u1.within_goal(cross) and all(
                u1.within_goal(cell['final'][m]['adjacent_rung_difference']) for m in ('fourier','angle')))
            self.assertTrue(cell['scalar_agreement'])


if __name__=='__main__':
    unittest.main()
