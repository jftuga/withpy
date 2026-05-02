"""Tests for the fetch subcommand."""

import http.server
import json
import subprocess
import sys
import threading
import time

import pytest


class _TestHandler(http.server.BaseHTTPRequestHandler):
    """Simple handler for fetch tests."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/json":
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/json")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            body = b"hello"
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        resp = f"received: {len(body)} bytes".encode()
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


@pytest.fixture
def http_server():
    """Start a local HTTP server for testing."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _TestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port
    server.shutdown()


def test_fetch_get(cli, http_server):
    """Fetch retrieves content from a URL."""
    result = cli("fetch", f"http://127.0.0.1:{http_server}/")
    assert result.returncode == 0
    assert b"hello" in result.stdout


def test_fetch_json(cli, http_server):
    """Fetch retrieves JSON content."""
    result = cli("fetch", f"http://127.0.0.1:{http_server}/json")
    assert result.returncode == 0
    assert b'"status"' in result.stdout


def test_fetch_timing(cli, http_server):
    """Fetch with timing shows duration info."""
    result = cli("fetch", "--timing", f"http://127.0.0.1:{http_server}/")
    assert result.returncode == 0


def test_fetch_post(cli, http_server):
    """Fetch POST sends data."""
    result = cli("fetch", "--method", "POST", "--data", "test payload", f"http://127.0.0.1:{http_server}/post")
    assert result.returncode == 0
    assert b"received:" in result.stdout
