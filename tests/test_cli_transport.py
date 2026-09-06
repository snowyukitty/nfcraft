"""Loopback capability tokens must not leave through proxies or redirects."""
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from nfcraft.cli import Client
from nfcraft.errors import OpsError


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://example.invalid/do-not-contact")
            self.end_headers()
            return
        body = b'{"mode":"demo"}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class LocalClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        runtime = Path(self.temp.name) / "demo" / "agent-runtime.json"
        runtime.parent.mkdir()
        runtime.write_text(json.dumps({"origin": f"http://127.0.0.1:{self.server.server_port}", "token": "disposable-test-token"}))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def test_ignores_environment_proxy(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://127.0.0.1:1", "http_proxy": "http://127.0.0.1:1", "NO_PROXY": "", "no_proxy": ""}):
            self.assertEqual(Client(root=self.temp.name).call("/api/state"), {"mode": "demo"})

    def test_refuses_redirect_without_external_request(self):
        with self.assertRaises(OpsError) as exc:
            Client(root=self.temp.name).call("/redirect")
        self.assertEqual(exc.exception.code, "REDIRECT_BLOCKED")
