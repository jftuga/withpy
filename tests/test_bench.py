"""Tests for the bench subcommand."""

import http.server
import threading

import pytest


class _BenchHandler(http.server.BaseHTTPRequestHandler):
    """Fast handler for bench tests."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")


@pytest.fixture
def bench_server():
    """Start a local server for bench testing."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _BenchHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port
    server.shutdown()


def test_bench_basic(cli, bench_server):
    """Bench makes requests and reports stats."""
    result = cli("bench", f"http://127.0.0.1:{bench_server}/", "--requests", "10", "--concurrency", "2")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "requests" in output.lower() or "completed" in output.lower()


def test_bench_single(cli, bench_server):
    """Bench with 1 request succeeds."""
    result = cli("bench", f"http://127.0.0.1:{bench_server}/", "--requests", "1")
    assert result.returncode == 0
