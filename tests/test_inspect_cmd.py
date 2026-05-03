"""Tests for the inspect subcommand."""

import pytest


def test_dns_localhost(cli):
    """Inspect DNS resolves localhost."""
    result = cli("inspect", "--mode", "dns", "localhost")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "127.0.0.1" in output or "::1" in output


def test_dns_invalid(cli):
    """Inspect DNS reports error for invalid hostname."""
    result = cli("inspect", "--mode", "dns", "this.host.does.not.exist.invalid")
    assert b"error" in result.stdout
