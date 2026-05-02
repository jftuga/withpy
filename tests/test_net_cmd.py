"""Tests for the net subcommand."""

import socket
import subprocess
import sys
import time

import pytest


@pytest.fixture
def echo_server():
    """Start an echo server and yield its port."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "withpy", "net", "--mode", "echo", "--port", "0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    line = proc.stdout.readline().decode()
    port = int(line.strip().split(":")[-1])
    time.sleep(0.1)
    yield port
    proc.terminate()
    proc.wait()


def test_check_closed_port(cli):
    """Check a port that is not listening."""
    result = cli("net", "--mode", "check", "--host", "localhost", "--port", "19999", "--timeout", "0.5")
    assert result.returncode == 1
    assert b"closed" in result.stdout


def test_resolve_localhost(cli):
    """Resolve localhost returns an address."""
    result = cli("net", "--mode", "resolve", "--host", "localhost")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "127.0.0.1" in output or "::1" in output


def test_scan_no_ports_arg(cli):
    """Scan without --ports produces error."""
    result = cli("net", "--mode", "scan", "--host", "localhost")
    assert result.returncode == 1


def test_check_no_port(cli):
    """Check without --port produces error."""
    result = cli("net", "--mode", "check", "--host", "localhost")
    assert result.returncode == 1
