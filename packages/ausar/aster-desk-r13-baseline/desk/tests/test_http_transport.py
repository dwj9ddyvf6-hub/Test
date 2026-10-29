import os
import socket
import ssl
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import httpx

from backend.http_transport import ResponseTooLarge, _ResolverPool, bounded_http


class HTTPTransportTests(unittest.TestCase):
    def test_resolver_saturation_rejects_new_work_and_recovers(self):
        pool = _ResolverPool()
        release = threading.Event()
        try:
            futures = [pool.submit(release.wait) for _ in range(4)]
            with self.assertRaises(OSError):
                pool.submit(lambda: "queued beyond capacity")
            release.set()
            for future in futures:
                self.assertTrue(future.result(timeout=1))
            self.assertEqual(pool.submit(lambda: "recovered").result(timeout=1), "recovered")
        finally:
            release.set()
            pool.shutdown(wait=True, cancel_futures=True)
        with self.assertRaises(RuntimeError):
            pool.submit(lambda: None)

    def test_slow_resolver_does_not_hold_interpreter_shutdown(self):
        script = '''
import os, socket, time
from backend.http_transport import bounded_http
os.environ['NO_PROXY'] = os.environ['no_proxy'] = 'fixture.invalid'
def slow(*args, **kwargs):
    time.sleep(3)
    raise socket.gaierror('Synthetic slow DNS')
socket.getaddrinfo = slow
try:
    bounded_http('GET', 'http://fixture.invalid', timeout_seconds=.2)
except TimeoutError:
    print('deadline reached')
'''
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=1.5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("deadline reached", result.stdout)

    def test_slow_dns_does_not_extend_deadline_or_send_after_cancellation(self):
        resolving, resolved = threading.Event(), threading.Event()
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append(True)
                self.send_response(200)
                self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        thread.start()
        def slow_resolution(*args, **kwargs):
            resolving.set()
            time.sleep(0.7)
            resolved.set()
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", server.server_port))]
        # This regression targets a lookup already in progress. Preload normal
        # verified CA trust so concurrent builds cannot spend its tiny deadline
        # on SSL-context construction before it reaches the synthetic resolver.
        context = ssl.create_default_context()
        original_client = httpx.AsyncClient
        def client(**kwargs):
            return original_client(verify=context, **kwargs)
        started = time.monotonic()
        try:
            with patch.dict(os.environ, {"NO_PROXY": "fixture.invalid", "no_proxy": "fixture.invalid"}), patch("socket.getaddrinfo", side_effect=slow_resolution), patch("backend.http_transport.httpx.AsyncClient", side_effect=client):
                with self.assertRaises(TimeoutError):
                    bounded_http("POST", "http://fixture.invalid:" + str(server.server_port), b"synthetic fixture", timeout_seconds=0.2)
            self.assertTrue(resolving.is_set())
            self.assertLess(time.monotonic() - started, 0.5)
            self.assertTrue(resolved.wait(timeout=1))
            self.assertEqual(received, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)

    def test_total_deadline_stops_a_real_continuously_streaming_response(self):
        observed = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                observed.append(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                self.send_response(200)
                self.send_header("Content-Length", "40")
                self.end_headers()
                try:
                    for _ in range(40):
                        self.wfile.write(b" ")
                        self.wfile.flush()
                        time.sleep(0.03)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        thread.start()
        started = time.monotonic()
        try:
            # The managed proxy remains configured; loopback alone is exempt.
            with patch.dict(os.environ, {"NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"}):
                with self.assertRaises(TimeoutError):
                    bounded_http("POST", "http://127.0.0.1:" + str(server.server_port),
                                 b"synthetic local audit probe", timeout_seconds=0.2)
            self.assertLess(time.monotonic() - started, 1.1)
            self.assertEqual(observed, [b"synthetic local audit probe"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)

    def fixture_client(self, handler):
        original = httpx.AsyncClient
        def factory(**kwargs):
            self.assertTrue(kwargs["trust_env"])
            return original(transport=httpx.MockTransport(handler), **kwargs)
        return patch("backend.http_transport.httpx.AsyncClient", side_effect=factory)

    def test_statuses_body_and_no_redirect_are_preserved(self):
        received = []
        def handler(request):
            received.append((request.method, request.content, request.headers.get("Authorization")))
            return httpx.Response(302, headers={"location": "https://other.invalid"}, content=b"redirect receipt")
        with self.fixture_client(handler):
            result = bounded_http("POST", "https://fixture.invalid", b"{}", {"Authorization": "fixture"})
        self.assertEqual(result, (302, b"redirect receipt"))
        self.assertEqual(received, [("POST", b"{}", "fixture")])

    def test_read_redirects_can_be_enabled_and_non_success_status_returned(self):
        received = []
        def handler(request):
            received.append(str(request.url))
            if len(received) == 1:
                return httpx.Response(302, headers={"location": "https://fixture.invalid/next"})
            return httpx.Response(429, content=b"limited")
        with self.fixture_client(handler):
            self.assertEqual(bounded_http("GET", "https://fixture.invalid", follow_redirects=True), (429, b"limited"))
        self.assertEqual(len(received), 2)

    def test_response_limit_rejects_oversize_and_accepts_exact_bound(self):
        with self.fixture_client(lambda request: httpx.Response(200, content=b"abc")):
            self.assertEqual(bounded_http("GET", "https://fixture.invalid", maximum_bytes=3), (200, b"abc"))
            with self.assertRaises(ResponseTooLarge):
                bounded_http("GET", "https://fixture.invalid", maximum_bytes=2)

    def test_invalid_bounds_do_not_make_a_request(self):
        with patch("backend.http_transport.httpx.AsyncClient") as client:
            for value in (True, 0, -1, float("nan"), float("inf")):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    bounded_http("GET", "https://unused.invalid", timeout_seconds=value)
            for value in (True, -1, 1.5, "3"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    bounded_http("GET", "https://unused.invalid", maximum_bytes=value)
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
