"""Actual free-certificate producer path and lossless failure adaptation."""
from copy import deepcopy
from fractions import Fraction as F
import unittest

import vacuum_certified as su2
import vacuum_u1_design_certified as u1
import vacuum_future_adapter as adapter


def free_certificate(theory):
    # g=1 is a development calibration coordinate, not a target coupling.
    g, eta, size = F(1), F(0), 6
    if theory == 'SU2':
        eigen = su2.eigenvalue_enclosures(g, eta, size)
        vectors = [[float(i == k) for i in range(size)] for k in range(4)]
        bounds = [su2.eigenvector_bound(g, eta, q, k, eigen) for k, q in enumerate(vectors)]
        overlaps = su2.overlap_intervals(vectors, bounds)
        vacuum = su2.vacuum_intervals(vectors[0], bounds[0])
        result = {'enclosures': eigen}
        key = 'first_three_gap_intervals'
    else:
        eigen = u1.enclosures(g, eta, size, 'even')
        vectors = [[float(abs(i-size) == k) for i in range(2*size+1)] for k in range(4)]
        bounds = [u1.vector_bound(g, eta, q, k, eigen) for k, q in enumerate(vectors)]
        overlaps, vacuum = u1.observables(vectors, bounds)
        result = {'even_enclosures': eigen}
        key = 'first_three_even_gap_intervals'
    result.update(bound_status='bounded', overlaps=overlaps, vacuum=vacuum)
    result[key] = [(e['lower']-eigen[0]['upper'],e['upper']-eigen[0]['lower']) for e in eigen[1:4]]
    return result


class FutureAdapterTests(unittest.TestCase):
    def test_real_free_certificates_resolve_both_observables(self):
        for theory, gap in [('SU2', F(8)), ('U1', F(16))]:
            with self.subTest(theory=theory):
                result = free_certificate(theory)
                original = deepcopy(result)
                rows = adapter.adapt_channels(theory, 1, 0, result)
                self.assertEqual(result, original)
                self.assertEqual([r['threshold']['leading_level'] for r in rows], [1, 2])
                lo, hi = map(F, rows[1]['threshold']['gap_interval'])
                self.assertLessEqual(lo, gap)
                self.assertGreaterEqual(hi, gap)
                self.assertFalse(rows[1]['threshold']['full_gap_claim_supported'])
                # Changing eta cannot carry the free selection proof with it.
                interacting = adapter.adapt_channels(theory, 1, F(1, 2), result)
                self.assertEqual(interacting[1]['threshold']['status'], 'unresolved')

    def test_contradictory_free_weight_rejected(self):
        result = free_certificate('SU2')
        result['overlaps'][0][1]['weight_lower'] = F(1, 10)
        result['overlaps'][0][1]['weight_upper'] = F(1, 5)
        with self.assertRaisesRegex(ValueError, 'contradicts free'):
            adapter.adapt_channels('SU2', 1, 0, result)

    def test_failed_certificate_retains_partial_rungs(self):
        stages = {'scalar': {'status': 'completed', 'result': {'e0': 0}},
                  'certificates': {'status': 'failed', 'reason': 'injected final-rung failure',
                                   'rungs': [{'status': 'completed', 'result': {'partial': True}},
                                             {'status': 'failed', 'reason': 'injected failure'}]},
                  'temporal': {'status': 'unresolved', 'reason': 'certificate unavailable'}}
        output = adapter.adapt_cell('SU2', 1, 0, stages)
        self.assertEqual(output['status'], 'failure')
        self.assertEqual(output['stages'], stages)
        self.assertEqual(output['channels'], [])
        self.assertFalse(output['target_execution_authorized'])
        stages['certificates']['rungs'].clear()
        self.assertEqual(len(output['stages']['certificates']['rungs']), 2)

    def test_partial_temporal_failure_keeps_valid_channels(self):
        stages = {'scalar': {'status': 'completed', 'result': {'fixture': True}},
                  'certificates': {'status': 'completed', 'result': free_certificate('SU2')},
                  'temporal': {'status': 'failed', 'reason': 'injected propagation failure'}}
        output = adapter.adapt_cell('SU2', 1, 0, stages)
        self.assertEqual(output['status'], 'failure')
        self.assertEqual(len(output['channels']), 2)
        stages['temporal'] = {'status': 'completed', 'result': {'fixture': True}}
        output = adapter.adapt_cell('SU2', 1, 0, stages)
        self.assertEqual(output['status'], 'available')
        self.assertEqual(output['precision_status'], 'not_assessed')
        del stages['scalar']
        self.assertEqual(adapter.adapt_cell('SU2', 1, 0, stages)['status'], 'failure')

    def test_missing_result_and_blank_failure_reason_rejected(self):
        stages = {'scalar': {'status': 'completed'},
                  'certificates': {'status': 'failed', 'reason': 'failure'},
                  'temporal': {'status': 'unresolved', 'reason': 'waiting'}}
        self.assertEqual(adapter.adapt_cell('SU2', 1, 0, stages)['status'], 'failure')
        stages['scalar'] = {'status': 'completed', 'result': {}}
        stages['certificates']['reason'] = '   '
        output = adapter.adapt_cell('SU2', 1, 0, stages)
        self.assertIn('invalid stage evidence', output['reason'])

    def test_malformed_stage_containers_preserved_as_failure(self):
        for stages in (None, [], {'scalar': None},
                       {'scalar': {'status': 'completed', 'result': {}},
                        'certificates': {'status': 'completed', 'result': 'invalid'},
                        'temporal': {'status': 'unresolved', 'reason': None}}):
            with self.subTest(stages=stages):
                output = adapter.adapt_cell('SU2', 1, 0, stages)
                self.assertEqual(output['status'], 'failure')
                self.assertEqual(output['stages'], stages)


if __name__ == '__main__':
    unittest.main()
