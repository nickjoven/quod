"""Check the recovered design bundle against its original checksum manifest."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'research/vacuum-spectrum'


def verify():
    directory = ROOT / 'design-bundle'
    manifest_bytes = (directory / 'manifest.json').read_bytes()
    provenance = json.loads((directory / 'archive-provenance.json').read_text())
    if hashlib.sha256(manifest_bytes).hexdigest() != provenance['manifest_sha256']:
        raise ValueError('bundle manifest drift')
    manifest = json.loads(manifest_bytes)
    for name, expected in manifest['sha256'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('invalid bundle path')
        if hashlib.sha256((directory / path).read_bytes()).hexdigest() != expected:
            raise ValueError('bundle file drift: ' + name)
    if (ROOT / 'ym_vacuum_gap_litcheck.md').read_bytes() != (directory / 'notes/ym_vacuum_gap_litcheck.md').read_bytes():
        raise ValueError('previously recovered draft differs')
    return {'verified': True, 'files_checked': len(manifest['sha256']),
            'registered': False, 'pilot_code_in_bundle': False}


if __name__ == '__main__':
    print(json.dumps(verify()))
