"""Local, read-only Linux process dashboard. Python standard library only."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / 'research/vacuum-spectrum/selected-run/index.json'
MONITOR = Path('/tmp/quod-vacuum-completion-monitor/status.json')
TICKS = os.sysconf('SC_CLK_TCK')
PAGE = os.sysconf('SC_PAGE_SIZE')


def parse_stat(raw):
    """The comm field can contain spaces and parentheses; fields start after it."""
    end = raw.rindex(')')
    fields = raw[end + 2:].split()
    return dict(name=raw[raw.index('(') + 1:end], state=fields[0],
                ticks=int(fields[11]) + int(fields[12]), start=int(fields[19]),
                rss=max(0, int(fields[21])) * PAGE)


def read_json(path):
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError('Expected an object')
        return value, None
    except (OSError, ValueError) as exc:
        return {}, type(exc).__name__


class Sampler:
    def __init__(self, pids):
        self.pids = pids
        self.previous = {}
        self.lock = threading.Lock()

    def snapshot(self):
        with self.lock:
            return self._snapshot()

    def _snapshot(self):
        now = time.monotonic()
        uptime = float(Path('/proc/uptime').read_text().split()[0])
        rows, current = [], {}
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                stat = parse_stat((entry / 'stat').read_text())
                # Only identify known scripts; never expose command arguments or environment.
                args = (entry / 'cmdline').read_bytes().split(b'\0')
                scripts = [Path(os.fsdecode(a)).name for a in args[1:] if a.endswith(b'.py')]
                role = ('vacuum solver' if 'vacuum_registered_run.py' in scripts else
                        'completion monitor' if 'vacuum_completion_monitor.py' in scripts else '')
                if self.pids and pid not in self.pids and not role:
                    continue
                key = (pid, stat['start'])
                old = self.previous.get(key)
                cpu = max(0, (stat['ticks'] - old[1]) / TICKS / (now - old[0]) * 100) if old and now > old[0] else None
                current[key] = (now, stat['ticks'])
                rows.append(dict(pid=pid, identity=f'{pid}:{stat["start"]}', name=stat['name'],
                                 role=role, state=stat['state'], cpu=cpu, rss=stat['rss'],
                                 cpu_seconds=stat['ticks'] / TICKS,
                                 elapsed=max(0, uptime - stat['start'] / TICKS)))
            except (OSError, ValueError, IndexError):
                continue  # Process exit or inaccessible entry during sampling.
        self.previous = current
        rows.sort(key=lambda r: (not bool(r['role']), -(r['cpu'] or 0), r['pid']))
        run, run_error = read_json(RUN)
        monitor, monitor_error = read_json(MONITOR)
        cells = run.get('cells', [])
        try:
            checkpoint_age = max(0, time.time() - RUN.stat().st_mtime)
        except OSError:
            checkpoint_age = None
        try:
            heartbeat_age = max(0, time.time() - datetime.fromisoformat(monitor['observed_utc']).timestamp())
        except (KeyError, ValueError, TypeError):
            heartbeat_age = None
        return dict(observed_utc=datetime.now(timezone.utc).isoformat(), processes=rows,
                    missing_pids=sorted(set(self.pids) - {r['pid'] for r in rows}),
                    run=dict(state=run.get('state', 'unavailable'), selected=run.get('selected'),
                             completed=sum(bool(r.get('result')) for r in cells),
                             active=[r['id'] for r in cells if r.get('attempted') and not r.get('result')],
                             checkpoints=len(run.get('checkpoints', [])), checkpoint_age=checkpoint_age,
                             error=run_error),
                    monitor=dict(phase=monitor.get('phase', 'unavailable'), heartbeat_age=heartbeat_age,
                                 error=monitor_error))


def handler(sampler):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Loopback binding plus Host validation prevents DNS rebinding access.
            if self.headers.get('Host') not in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}:
                self.send_error(403)
                return
            route = urlsplit(self.path).path
            if route == '/api/status':
                body, kind = json.dumps(sampler.snapshot()).encode(), 'application/json'
            elif route == '/':
                body, kind = (HERE / 'index.html').read_bytes(), 'text/html; charset=utf-8'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass
    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--pid', type=int, action='append', default=[], help='Filter to these PIDs plus vacuum processes; repeatable')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler(Sampler(args.pid)))
    print(f'Liveness → http://localhost:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
