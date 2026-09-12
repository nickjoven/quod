import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from server import PAGE, Sampler, handler, parse_stat, read_json


class Tests(unittest.TestCase):
    def test_stat_with_parentheses_and_spaces(self):
        fields = ['0'] * 22
        fields[0] = 'S'
        fields[11:13] = ['10', '20']
        fields[19] = '500'
        fields[21] = '3'
        value = parse_stat('123 (name ) with spaces) ' + ' '.join(fields))
        self.assertEqual(value, dict(name='name ) with spaces', state='S', ticks=30, start=500, rss=3 * PAGE))

    def test_missing_and_partial_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.json'
            self.assertEqual(read_json(path)[1], 'FileNotFoundError')
            path.write_text('{')
            self.assertEqual(read_json(path)[1], 'JSONDecodeError')
            path.write_text('[]')
            self.assertEqual(read_json(path)[1], 'ValueError')

    def test_live_sampler_identity_and_cpu_warmup(self):
        sampler = Sampler([os.getpid(), 2147483647])
        first = sampler.snapshot()
        process = next(p for p in first['processes'] if p['pid'] == os.getpid())
        self.assertIsNone(process['cpu'])
        self.assertIn(2147483647, first['missing_pids'])
        second = next(p for p in sampler.snapshot()['processes'] if p['pid'] == os.getpid())
        self.assertEqual(process['identity'], second['identity'])
        self.assertGreaterEqual(second['cpu'], 0)
        self.assertNotIn('cmdline', process)

    def test_http_routes_and_host_guard(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler(Sampler([os.getpid()])))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = http.client.HTTPConnection('127.0.0.1', server.server_port)
            for path, expected in [('/', 200), ('/api/status', 200), ('/../server.py', 404)]:
                client.request('GET', path)
                response = client.getresponse()
                self.assertEqual(response.status, expected)
                body = response.read()
                if path == '/api/status':
                    self.assertIn('processes', json.loads(body))
                if path == '/':
                    self.assertIn(b'LIVENESS', body)
            client.request('GET', '/api/status', headers={'Host': 'untrusted.example'})
            response = client.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
