"""Tests for the serve subcommand."""

import base64
import http.client
import os
import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(
    "GITHUB_ACTIONS" in os.environ,
    reason="serve tests require a local network listener; skipped in GitHub Actions",
)


def _extract_port(line: str) -> int:
    """Extract port number from serve output line like 'serving ... at http://0.0.0.0:12345/'."""
    import re
    m = re.search(r":(\d+)/?$", line.strip())
    return int(m.group(1)) if m else 0


@pytest.fixture
def file_server(tmp_path):
    """Start a file server on a random port and yield (port, proc)."""
    (tmp_path / "hello.txt").write_text("hello world")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "nested.txt").write_text("nested")
    proc = subprocess.Popen(
        [sys.executable, "-m", "withpy", "serve", "--addr", "127.0.0.1", "--port", "0", "--dir", str(tmp_path), "--quiet"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    line = proc.stdout.readline().decode()
    port = _extract_port(line)
    time.sleep(0.1)
    yield port, proc
    proc.terminate()
    proc.wait()


@pytest.fixture
def auth_server(tmp_path):
    """Start a file server with basic auth."""
    (tmp_path / "secret.txt").write_text("secret data")
    proc = subprocess.Popen(
        [sys.executable, "-m", "withpy", "serve", "--addr", "127.0.0.1", "--port", "0", "--dir", str(tmp_path), "--quiet", "--auth", "admin:pass123"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    line = proc.stdout.readline().decode()
    port = _extract_port(line)
    time.sleep(0.1)
    yield port, proc
    proc.terminate()
    proc.wait()


def test_serve_file(file_server):
    """Server serves files correctly."""
    port, _ = file_server
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", "/hello.txt")
    resp = conn.getresponse()
    assert resp.status == 200
    assert resp.read() == b"hello world"
    conn.close()


def test_serve_404(file_server):
    """Server returns 404 for missing files."""
    port, _ = file_server
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", "/nonexistent.txt")
    resp = conn.getresponse()
    assert resp.status == 404
    conn.close()


def test_serve_auth_required(auth_server):
    """Server returns 401 without credentials."""
    port, _ = auth_server
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", "/secret.txt")
    resp = conn.getresponse()
    assert resp.status == 401
    conn.close()


def test_serve_auth_success(auth_server):
    """Server grants access with correct credentials."""
    port, _ = auth_server
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    creds = base64.b64encode(b"admin:pass123").decode()
    conn.request("GET", "/secret.txt", headers={"Authorization": f"Basic {creds}"})
    resp = conn.getresponse()
    assert resp.status == 200
    assert resp.read() == b"secret data"
    conn.close()
