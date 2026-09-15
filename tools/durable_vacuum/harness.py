"""Development-only durable temporal task ledger; never resumes the selected run."""
import argparse
import ast
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import vacuum_temporal_replay as replay


class DurabilityError(BaseException):
    """Storage failure must escape the numerical kernel's Exception handler."""


def encoded(value):
    return replay.encoded(value).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def environment():
    paths = {Path(__file__).resolve()}
    todo = [ROOT / 'scripts/vacuum_temporal_replay.py']
    while todo:
        path = todo.pop()
        if path in paths:
            continue
        paths.add(path)
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                if name and name.startswith('vacuum_'):
                    candidate = ROOT / 'scripts' / (name.split('.')[0] + '.py')
                    require(candidate.exists(), 'missing local source')
                    todo.append(candidate)
    return {'python': platform.python_version(),
            'dependencies': {p: version(p) for p in ('numpy', 'scipy', 'sympy', 'mpmath')},
            'sources': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(paths)},
            'threads': {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')}}


def fixture(theory):
    require(theory in ('SU2', 'U1'), 'calibration theory required')
    return replay.temporal.certificates.calculate(theory, '1', '0', 8, [0, '1/8', '1/4'])


def protocol():
    return {'schema_version': 1, 'scope': 'development calibration only; no selected target authority',
            'environment': environment(),
            'tasks': [{'id': f'{theory}:{n}:{i}', 'theory': theory, 'nodes': n,
                       'tolerance': tolerance} for theory in ('SU2', 'U1') for n in (32, 64)
                      for i, tolerance in enumerate(([1e-8, 1e-12], [1e-10, 1e-14]))],
            'failure_rules': 'Terminal failed/unresolved outcomes are retained, never retried. Interrupted attempts require explicit acknowledgement. Saved propagation is reused only on exact input identity; mismatch stops execution.'}


def specification():
    return dict(protocol(), certificates={theory: fixture(theory) for theory in ('SU2', 'U1')})


def validate(spec):
    require(encoded({k: v for k, v in spec.items() if k != 'certificates'}) == encoded(protocol()),
            'specification, calibration or environment drift')
    require(set(spec['certificates']) == {'SU2', 'U1'}, 'calibration inventory drift')
    for theory, certificate in spec['certificates'].items():
        require(certificate['theory'] == theory and certificate['g'] == '1' and certificate['eta'] == '0'
                and certificate['cutoff'] == 8 and certificate['times'] == ['0', '1/8', '1/4'],
                'calibration coordinates or clock drift')
        require(replay.temporal.certificates.verify(certificate), 'invalid stored calibration certificate')


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish(path, value):
    """Durable no-replace commit; unlinked temporary files are forensic evidence."""
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(encoded(value) + b'\n')
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, path)  # atomic, fails if destination already exists
        fsync_dir(path.parent)
        os.unlink(temporary)
        fsync_dir(path.parent)
    except BaseException:
        # Leave the pending bytes and any committed destination intact.
        raise


@contextmanager
def locked(directory):
    require(directory.is_dir(), 'initialize a ledger first')
    with (directory / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class Ledger:
    def __init__(self, directory, spec):
        self.directory, self.spec = directory, spec
        self.binding = digest(encoded(spec))
        self.events = []
        expected = {'spec.json', '.lock'}
        for path in sorted(directory.glob('event-*.json')):
            expected.add(path.name)
            event = json.loads(path.read_text())
            number = len(self.events)
            require(path.name == f'event-{number:06d}.json', 'noncontiguous event inventory')
            sha = event.pop('sha256')
            require(sha == digest(encoded(event)), 'event checksum mismatch')
            require(event['sequence'] == number and event['spec_sha256'] == self.binding and
                    event['previous'] == (self.events[-1]['sha256'] if self.events else None), 'event chain mismatch')
            event['sha256'] = sha
            self.events.append(event)
        extra = {p.name for p in directory.iterdir()} - expected
        require(not extra, 'uncommitted/orphan evidence requires manual inspection: ' + ', '.join(sorted(extra)))
        self.audit()

    def append(self, kind, task, attempt, **payload):
        event = dict(sequence=len(self.events), spec_sha256=self.binding,
                     previous=self.events[-1]['sha256'] if self.events else None,
                     observed_utc=datetime.now(timezone.utc).isoformat(),
                     kind=kind, task=task, attempt=attempt, **payload)
        event['sha256'] = digest(encoded(event))
        try:
            publish(self.directory / f'event-{len(self.events):06d}.json', event)
        except BaseException as exc:
            raise DurabilityError(f'journal publication failed: {type(exc).__name__}: {exc}') from exc
        self.events.append(event)

    def audit(self):
        tasks = {t['id']: t for t in self.spec['tasks']}
        starts, terminal, raw, interrupted = {}, {}, {}, set()
        for e in self.events:
            require(e['task'] in tasks, 'unknown task')
            key = (e['task'], e['attempt'])
            kind = e['kind']
            if kind == 'started':
                require(e['task'] not in terminal and key not in starts, 'duplicate or terminal task start')
                prior = [k for k in starts if k[0] == e['task']]
                require(e['attempt'] == len(prior) and all(k in interrupted for k in prior), 'unacknowledged interrupted attempt')
                starts[key] = e
            else:
                require(key in starts and key not in interrupted and e['task'] not in terminal, 'event outside active attempt')
                if kind == 'interrupted':
                    interrupted.add(key)
                elif kind == 'propagation':
                    require(key not in raw and isinstance(e['input_sha256'], str) and len(e['input_sha256']) == 64,
                            'duplicate or unbound propagation')
                    encoded(e['result'])
                    ref = e.get('reused_from')
                    retained = [r for k, r in raw.items() if k[0] == e['task'] and k in interrupted]
                    require(ref == (retained[-1]['sequence'] if retained else None),
                            'latest interrupted propagation must be reused')
                    if ref is not None:
                        require(type(ref) is int and 0 <= ref < e['sequence'], 'invalid reuse reference')
                        previous = self.events[ref]
                        previous_key = (previous['task'], previous['attempt'])
                        require(previous['kind'] == 'propagation' and previous['task'] == e['task']
                                and previous_key in interrupted and previous_key in raw,
                                'reuse requires prior interrupted propagation for same task')
                        require(previous['input_sha256'] == e['input_sha256'] and
                                encoded(previous['result']) == encoded(e['result']), 'reused propagation changed')
                    raw[key] = e
                elif kind == 'outcome':
                    task = tasks[e['task']]
                    verdict = replay.verify(self.spec['certificates'][task['theory']], e['output'],
                                            [task['nodes']], [task['tolerance']])
                    require(verdict['status'] == 'verified' and encoded(verdict) == encoded(e['verification']), 'invalid task replay')
                    slot = e['output']['result']['rungs'][0]['evolutions'][0]
                    if slot.get('propagation_status') == 'completed':
                        require(key in raw and encoded(raw[key]['result']) == encoded(slot['result']), 'outcome/raw propagation mismatch')
                    else:
                        require(key not in raw, 'outcome discards saved successful propagation')
                    terminal[e['task']] = e
                else:
                    raise ValueError('unknown event kind')
        return starts, terminal, raw, interrupted


def input_digest(matrix, e0, vectors, times, rtol, atol):
    import numpy as np
    matrix = matrix.tocsc(copy=True)
    matrix.sort_indices()
    h = hashlib.sha256(encoded({'shape': matrix.shape, 'e0': e0, 'rtol': rtol, 'atol': atol}))
    for value in (matrix.data, matrix.indices, matrix.indptr, vectors, times):
        array = np.ascontiguousarray(value)
        h.update(encoded({'dtype': array.dtype.str, 'shape': array.shape}))
        h.update(array.tobytes())
    return h.hexdigest()


def execute(ledger, retry_interrupted=False):
    """Single-threaded adapter; wrapping is local to this development process."""
    validate(ledger.spec)
    for task in ledger.spec['tasks']:
        starts, terminal, raw, interrupted = ledger.audit()
        name = task['id']
        if name in terminal:
            continue
        prior = [key for key in starts if key[0] == name]
        active = [key for key in prior if key not in interrupted]
        if active:
            require(retry_interrupted, 'interrupted attempt; explicit --retry-interrupted required')
            ledger.append('interrupted', name, active[-1][1], reason='operator acknowledged interrupted attempt; retained all evidence')
        cached = [raw[key] for key in prior if key in raw]
        saved = cached[-1] if cached else None
        attempt = len(prior)
        validate(ledger.spec)
        ledger.append('started', name, attempt)
        original = replay.temporal.evolution.propagate

        def durable_propagate(*args, **kwargs):
            signature = input_digest(*args, **kwargs)
            if saved:
                if signature != saved['input_sha256']:
                    raise DurabilityError('saved propagation input mismatch; refusing recomputation')
                observed = deepcopy(saved['result'])
            else:
                observed = original(*args, **kwargs)
            ledger.append('propagation', name, attempt, input_sha256=signature,
                          reused_from=saved['sequence'] if saved else None, result=observed)
            return observed

        replay.temporal.evolution.propagate = durable_propagate
        started = time.monotonic()
        try:
            output = replay.temporal.run(ledger.spec['certificates'][task['theory']],
                                         [task['nodes']], [task['tolerance']])
        finally:
            replay.temporal.evolution.propagate = original
        verdict = replay.verify(ledger.spec['certificates'][task['theory']], output,
                                [task['nodes']], [task['tolerance']])
        # Retain even invalid assessment output; later audit refuses qualification/reuse.
        ledger.append('outcome', name, attempt, output=output, verification=verdict,
                      elapsed_seconds=time.monotonic() - started)
        require(verdict['status'] == 'verified', 'output retained but arithmetic replay failed')
        validate(ledger.spec)
    return summary(ledger)


def summary(ledger):
    starts, terminal, raw, interrupted = ledger.audit()
    return {'scope': 'development task evidence only; no full-ladder qualification or uniform gap claim',
            'spec_sha256': ledger.binding, 'tasks': len(ledger.spec['tasks']),
            'terminal': len(terminal), 'outcomes': {k: e['output']['status'] for k, e in terminal.items()},
            'raw_propagations': len(raw), 'interrupted_attempts': len(interrupted),
            'pending_attempts': [list(k) for k in starts if k not in interrupted and k[0] not in terminal],
            'events': len(ledger.events),
            'replay_scope': 'hash-chain integrity and stored error/window arithmetic; no propagation rerun or execution authentication'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'init', 'run', 'replay'))
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--retry-interrupted', action='store_true')
    args = parser.parse_args()
    if args.action == 'prepare':
        publish(args.spec, specification())
        return
    spec = json.loads(args.spec.read_text())
    validate(spec)
    require(args.ledger is not None, '--ledger required')
    require(not args.ledger.resolve().is_relative_to(ROOT / 'research/vacuum-spectrum/selected-run'), 'selected evidence directory forbidden')
    if args.action == 'init':
        args.ledger.mkdir()  # exclusive; existing evidence is never overwritten
        fsync_dir(args.ledger.parent)
        publish(args.ledger / 'spec.json', spec)
        return
    with locked(args.ledger):
        require(encoded(json.loads((args.ledger / 'spec.json').read_text())) == encoded(spec), 'ledger specification mismatch')
        ledger = Ledger(args.ledger, spec)
        result = execute(ledger, args.retry_interrupted) if args.action == 'run' else summary(ledger)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
