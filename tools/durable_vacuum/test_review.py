"""Independent ledger-state mutants; no numerical solver is invoked."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import harness


class IndependentLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.spec = {'certificates': {'SU2': {}}, 'tasks': [
            {'id': 'fixture', 'theory': 'SU2', 'nodes': 32, 'tolerance': [1e-8, 1e-12]}]}
        (self.directory / 'spec.json').write_bytes(harness.encoded(self.spec))
        self.ledger = harness.Ledger(self.directory, self.spec)

    def raw(self, attempt, reused_from=None, signature='a' * 64, result=None):
        self.ledger.append('propagation', 'fixture', attempt, input_sha256=signature,
                           reused_from=reused_from, result=result or {'fixture': 1})

    def interrupted_raw(self):
        self.ledger.append('started', 'fixture', 0)
        self.raw(0)
        self.ledger.append('interrupted', 'fixture', 0, reason='explicit acknowledgement')
        self.ledger.append('started', 'fixture', 1)

    def test_reuse_requires_existing_prior_raw_event(self):
        self.interrupted_raw()
        self.raw(1, reused_from=999)
        with self.assertRaises(ValueError): self.ledger.audit()

    def test_saved_raw_cannot_be_silently_recomputed(self):
        self.interrupted_raw()
        self.raw(1, reused_from=None)
        with self.assertRaises(ValueError): self.ledger.audit()

    def test_reuse_must_reference_newest_retained_raw(self):
        self.interrupted_raw()
        self.raw(1, reused_from=1)
        self.ledger.append('interrupted', 'fixture', 1, reason='explicit acknowledgement')
        self.ledger.append('started', 'fixture', 2)
        self.raw(2, reused_from=1)
        with self.assertRaises(ValueError): self.ledger.audit()

    def test_reuse_requires_identical_input_digest(self):
        self.interrupted_raw()
        self.raw(1, reused_from=1, signature='b' * 64)
        with self.assertRaises(ValueError): self.ledger.audit()

    def test_reuse_requires_identical_raw_result(self):
        self.interrupted_raw()
        self.raw(1, reused_from=1, result={'fixture': 2})
        with self.assertRaises(ValueError): self.ledger.audit()

    def test_failed_propagation_cannot_discard_saved_success(self):
        self.ledger.append('started', 'fixture', 0)
        self.raw(0)
        output = {'status': 'failed', 'result': {'rungs': [{'evolutions': [
            {'status': 'failed', 'propagation_status': 'failed', 'assessment_status': 'not_attempted'}]}]}}
        verdict = {'status': 'verified', 'stage_status': 'failed', 'common_sample_pairs': []}
        self.ledger.append('outcome', 'fixture', 0, output=output, verification=verdict)
        with patch.object(harness.replay, 'verify', return_value=verdict):
            with self.assertRaises(ValueError): self.ledger.audit()

    def test_unacknowledged_retry_is_rejected(self):
        self.ledger.append('started', 'fixture', 0)
        self.ledger.append('started', 'fixture', 1)
        with self.assertRaises(ValueError): self.ledger.audit()

    def test_orphan_artifact_prevents_resume(self):
        (self.directory / '.pending-orphan').write_text('partial')
        with self.assertRaisesRegex(ValueError, 'orphan'):
            harness.Ledger(self.directory, self.spec)

    def test_no_replace_publication_preserves_existing_evidence(self):
        path = self.directory / 'artifact.json'
        harness.publish(path, {'version': 1})
        with self.assertRaises(FileExistsError): harness.publish(path, {'version': 2})
        self.assertEqual(json.loads(path.read_text()), {'version': 1})


if __name__ == '__main__': unittest.main()
