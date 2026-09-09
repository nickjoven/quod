"""Verify recovered source snapshots and reproduce the owner's lessons query."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'research/vacuum-spectrum/source-recovery'


def verify():
    manifest = json.loads((DIRECTORY / 'manifest.json').read_text())
    for path, record in manifest['snapshots'].items():
        if hashlib.sha256((DIRECTORY / path).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('snapshot drift: ' + path)
    litcheck = DIRECTORY.parent / 'ym_vacuum_gap_litcheck.md'
    if hashlib.sha256(litcheck.read_bytes()).hexdigest() != manifest['litcheck_sha256']:
        raise ValueError('LITCHECK draft drift')
    output = (DIRECTORY / 'lessons-query.txt').read_bytes()
    if hashlib.sha256(output).hexdigest() != manifest['query_sha256']:
        raise ValueError('query output drift')
    # The original tool discovers its ledger via git; supply an isolated fixture
    # repository, preserving both captured source files byte-for-byte.
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory)
        subprocess.run(['git', 'init', '-q', directory], check=True)
        (fixture / 'LESSONS.md').write_bytes((DIRECTORY / 'lessons-ledger.txt').read_bytes())
        (fixture / 'lessons.py').write_bytes((DIRECTORY / 'lessons-tool.py.txt').read_bytes())
        result = subprocess.run(['python3', str(fixture / 'lessons.py'), *manifest['query_keywords']],
                                cwd=fixture, capture_output=True, check=False)
        if result.returncode != manifest['query_exit_code'] or result.stdout != output:
            raise ValueError('owner lessons query does not reproduce')
        draft = json.loads((DIRECTORY / 'draft-lessons-query.json').read_text())
        draft_output = (DIRECTORY / 'draft-lessons-query.txt').read_bytes()
        if draft['source_commit'] != manifest['commit'] or hashlib.sha256(draft_output).hexdigest() != draft['output_sha256']:
            raise ValueError('draft query provenance drift')
        result = subprocess.run(['python3', str(fixture / 'lessons.py'), *draft['keywords']],
                                cwd=fixture, capture_output=True, check=False)
        if result.returncode != draft['exit_code'] or result.stdout != draft_output:
            raise ValueError('draft lessons query does not reproduce')
        if draft_output.decode().strip().splitlines()[-1] != 'cite: ' + ', '.join(draft['expected_ids']):
            raise ValueError('draft lessons IDs differ')
    return {'verified': True, 'source_commit': manifest['commit'],
            'lessons': output.decode().strip().splitlines()[-1],
            'draft_lessons': draft['expected_ids']}


if __name__ == '__main__':
    print(json.dumps(verify()))
