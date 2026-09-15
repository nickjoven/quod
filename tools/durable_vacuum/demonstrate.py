"""Retain a small crash/recovery/failure experiment, never selected targets."""
import argparse
import json
from pathlib import Path
import time
from unittest.mock import patch

import harness as h


def demonstrate(spec_path, directory):
    spec = json.loads(spec_path.read_text())
    h.validate(spec)
    directory.mkdir()  # No overwriting any prior experiment.
    h.fsync_dir(directory.parent)
    h.publish(directory / 'spec.json', spec)
    with h.locked(directory):
        ledger = h.Ledger(directory, spec)
        with patch.object(h.replay.temporal, 'angle_error_bounds',
                          side_effect=KeyboardInterrupt('deliberate development crash after raw publication')):
            try:
                h.execute(ledger)
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError('crash fixture did not interrupt')
        before = h.summary(h.Ledger(directory, spec))
        original = h.replay.temporal.evolution.propagate
        calls = []

        def fail_one(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError('deliberate development propagation failure; retain terminal outcome')
            return original(*args, **kwargs)

        started = time.monotonic()
        with patch.object(h.replay.temporal.evolution, 'propagate', side_effect=fail_one):
            result = h.execute(h.Ledger(directory, spec), retry_interrupted=True)
        execution_seconds = time.monotonic() - started
        started = time.monotonic()
        with (patch.object(h.replay.temporal.evolution, 'propagate', side_effect=AssertionError('replay invoked solver')),
              patch.object(h.replay.temporal.certificates, 'calculate', side_effect=AssertionError('replay regenerated certificate'))):
            h.validate(spec)
            replayed = h.summary(h.Ledger(directory, spec))
        require_same = h.encoded(replayed) == h.encoded(result)
        if not require_same or len(calls) != 7 or result['terminal'] != 8:
            raise AssertionError('recovery/replay accounting mismatch')
        return {'scope': 'deliberate in-process exception injection, not a physical power-loss test; small calibration only',
                'demonstration_source_sha256': h.digest(Path(__file__).read_bytes()),
                'before_resume': before, 'after_resume': result,
                'fresh_propagation_calls': len(calls), 'saved_propagations_reused': 1,
                'execution_seconds': execution_seconds,
                'replay_seconds': time.monotonic() - started,
                'replay_invoked_propagation_or_certificate_calculation': False,
                'timing_limit': 'small fixture timings do not predict target runtime or replay scaling'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--ledger', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(demonstrate(args.spec, args.ledger), indent=2))
