"""Verify supplied v3 payloads and preserve the original numerical design."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / 'research/vacuum-spectrum'


class V3BundleTests(unittest.TestCase):
    def test_payload_integrity(self):
        directory = ROOT / 'design-bundle-v3'
        manifest_bytes = (directory / 'manifest.json').read_bytes()
        manifest = json.loads(manifest_bytes)
        provenance = json.loads((directory / 'archive-provenance.json').read_text())
        self.assertEqual(manifest['artifact_version'], 3)
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), provenance['manifest_sha256'])
        self.assertEqual(set(provenance['members']), set(manifest['sha256']) | {'manifest.json'})
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
        self.assertEqual(actual, set(provenance['members']) | {'archive-provenance.json'})
        for name, expected in manifest['sha256'].items():
            with self.subTest(member=name):
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn('..', Path(name).parts)
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)
        self.assertFalse(manifest['target_cells_run'])
        self.assertFalse(manifest['github_issue_created'])

    def test_numerical_specification_preserved(self):
        name = 'notes/ym_vacuum_gap_registration_draft.md'
        old = (ROOT / 'design-bundle' / name).read_text()
        new = (ROOT / 'design-bundle-v3' / name).read_text()
        start = '## Scope and proposed question'
        final = '## Before this draft becomes a registration'
        self.assertEqual(old[old.index(start):old.index(final)],
                         new[new.index(start):new.index('## Version 2 follow-on benchmark note')])
        self.assertEqual(old[old.index(final):], new[new.index(final):])


if __name__ == '__main__':
    unittest.main()
