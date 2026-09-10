"""Test non-target calibration coordinates and coordinate-bound exact replay."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

import vacuum_parameterized_certificate as producer
import vacuum_certificate_run as old_su2
import vacuum_u1_design_certificate_run as old_u1


class ParameterizedCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only g=1, an existing development coordinate; no held-out coupling.
        cls.records = {(theory, eta): producer.calculate(theory, '1', eta, 8, [0, F(1,4)])
                       for theory in ('SU2', 'U1') for eta in ('0', '0.5', '1')}

    def test_all_deformations_exact_replay_without_solver(self):
        with patch.object(producer, 'eigh_tridiagonal', side_effect=AssertionError('verifier used solver')):
            for key, record in self.records.items():
                with self.subTest(key=key):
                    self.assertTrue(producer.verify(record))

    def test_eta_one_matches_preserved_producers(self):
        for theory, old in [('SU2',old_su2), ('U1',old_u1)]:
            self.assertEqual(self.records[(theory,'1')]['result'],
                             producer.encode(old.calculate(1,8,[0,F(1,4)])))

    def test_free_producer_integrates_exact_selection(self):
        for theory in ('SU2','U1'):
            channels = producer.verified_channels(self.records[(theory,'0')])
            self.assertEqual([c['threshold']['leading_level'] for c in channels], [1,2])

    def test_wrong_coordinate_budget_and_clock_rejected(self):
        for key,value in [('g','2'), ('eta','1'), ('times',['0','1/2'])]:
            record = deepcopy(self.records[('SU2','0.5')])
            record[key] = value
            self.assertFalse(producer.verify(record), key)
        record = deepcopy(self.records[('U1','0.5')])
        record['result']['scalar_budget_met'] = not record['result']['scalar_budget_met']
        self.assertFalse(producer.verify(record))
        with self.assertRaisesRegex(ValueError, 'coordinate-bound'):
            producer.verified_channels(record)

    def test_parameter_and_vector_failure(self):
        for g,eta,times in [('0','1',[0]), ('1','-1',[0]), ('1','1',[1,0])]:
            with self.assertRaises(ValueError):
                producer.calculate('SU2',g,eta,8,times)
        record = deepcopy(self.records[('U1','0.5')])
        record['result']['candidate_vectors_hex'][0][0] = float(1).hex()
        self.assertFalse(producer.verify(record))

    def test_malformed_endpoint_rows_rejected(self):
        for theory in ('SU2','U1'):
            for malformed in ('invalid', None, []):
                with self.subTest(theory=theory, malformed=malformed):
                    record = deepcopy(self.records[(theory,'0')])
                    key = 'enclosures' if theory == 'SU2' else 'even_enclosures'
                    record['result'][key][0] = malformed
                    self.assertFalse(producer.verify(record))


if __name__ == '__main__':
    unittest.main()
