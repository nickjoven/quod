"""Check the offline report's exact payload and executable CAS/data instructions."""
import base64
import contextlib
import copy
import gzip
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import unittest

import vacuum_single_report as report


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class SingleReportTests(unittest.TestCase):
    def test_scalar_error_underestimate_is_rejected(self):
        namespace={}
        exec(compile(report.SCALARS,'<scalar-replay>','exec'),namespace)
        self.assertEqual(namespace['verify_scalar_accuracy'](self.payload),40)
        changed=copy.deepcopy(self.payload)
        record=changed['data']['SU2_scalar_accuracy'][0]['assessment']['methods']['angle_fourth']
        record['gap_relative_error_upper'][0]='0'
        with self.assertRaises(AssertionError):
            namespace['verify_scalar_accuracy'](changed)

    @classmethod
    def setUpClass(cls):
        cls.html = report.OUTPUT.read_text()
        cls.tag = re.search(r'<script id="machine-data" type="application/octet-stream" data-sha256="([0-9a-f]+)">(.*?)</script>', cls.html, re.S)
        cls.raw = gzip.decompress(base64.b64decode(cls.tag.group(2)))
        cls.payload = json.loads(cls.raw)

    def test_exact_payload_sources_and_boundary(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), self.tag.group(1))
        for name, expected in self.payload['source_sha256'].items():
            self.assertEqual(hashlib.sha256((report.D/name).read_bytes()).hexdigest(), expected, name)
        for review in ('combined_error_review', 'analytic_certificate_review', 'future_adapter',
                       'parameterized_certificate', 'parameterized_temporal', 'parameterized_scalar',
                       'run_envelope'):
            for name, expected in self.payload[review]['source_sha256'].items():
                self.assertEqual(hashlib.sha256((report.ROOT/name).read_bytes()).hexdigest(), expected, name)
        for name in ('design-readiness.json', 'result-contract.json', 'pilot-disposition.json', 'vacuum-coercivity-check.json'):
            self.assertEqual(self.payload['data'][name], json.loads((report.D/name).read_text()))
        self.assertEqual(self.payload['cas_program'], report.CAS)
        self.assertEqual(self.payload['report_generator_sha256'],
                         hashlib.sha256(Path(report.__file__).read_bytes()).hexdigest())
        self.assertEqual(self.payload['blockers']['owner_assigned_P_LC_ids'],
                         'optional_in_quod; required_only_for_legacy_ledger_submission')
        self.assertEqual(len(self.payload['data']['design-readiness.json']['targets']), 42)
        for theory, name in [('SU2', 'late-times.json'), ('U1', 'u1-design-semigroup.json')]:
            archive = json.loads((report.D/name).read_text())
            embedded = self.payload['data'][theory+'_time_window_evidence']
            self.assertEqual(len(embedded), 10)
            for actual, source in zip(embedded, archive['cells']):
                self.assertEqual(actual['g'], source['g'])
                self.assertEqual(actual['times'], source['times'])
                self.assertEqual(actual['finest_assessment'], source['window_assessment']['rungs'][-1])
                self.assertEqual(actual['finest_correlation_error_bounds'], source['angle_error_bounds'][-1])

    def test_cas_checks_and_sign_error_rejection(self):
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(report.CAS, '<cas>', 'exec'), {})
            with self.assertRaises(AssertionError):
                exec(compile(report.CAS.replace('expanded-remainder-divergence',
                                                'expanded+remainder-divergence'), '<mutant>', 'exec'), {})

    def test_residual_underestimate_rejected(self):
        namespace = {}
        exec(compile(report.RESIDUALS, '<residual-check>', 'exec'), namespace)
        changed = copy.deepcopy(self.payload)
        changed['data']['SU2_finest_certificates'][0]['result']['vector_bounds'][0]['residual_norm_upper'] = '0'
        with self.assertRaises(AssertionError):
            namespace['verify_residuals'](changed)

    def test_offline_document_and_embedded_verifier(self):
        from html import unescape
        tags = Tags()
        tags.feed(self.html)
        self.assertEqual(sum(t == 'svg' for t, a in tags.tags), 3)
        for tag, attrs in tags.tags:
            if tag == 'svg':
                self.assertEqual(attrs.get('role'), 'img')
                self.assertTrue(attrs.get('aria-label'))
        for tag, attrs in tags.tags:
            if tag in ('script', 'img', 'link', 'iframe'):
                self.assertNotIn('src', attrs)
                self.assertNotIn('href', attrs)
        snippets = [unescape(s) for s in re.findall(r'<pre>(.*?)</pre>', self.html, re.S)]
        executable = next(s for s in snippets if s.startswith('import base64, gzip'))
        previous = Path.cwd()
        try:
            os.chdir(report.D)
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(executable, '<document-verifier>', 'exec'), {})
        finally:
            os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
