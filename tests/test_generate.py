"""Tests for the generate subcommand."""

import pytest


def test_uuid4_format(cli):
    """UUID4 output matches 8-4-4-4-12 hex format."""
    result = cli("generate", "--mode", "uuid")
    assert result.returncode == 0
    uuid = result.stdout.decode().strip()
    parts = uuid.split("-")
    assert len(parts) == 5
    assert [len(p) for p in parts] == [8, 4, 4, 4, 12]


def test_uuid4_unique(cli):
    """Multiple UUID4 outputs are unique."""
    result = cli("generate", "--mode", "uuid", "--count", "3")
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 3
    assert len(set(lines)) == 3


def test_uuid5_deterministic(cli):
    """UUID5 with same namespace+name produces the same UUID."""
    r1 = cli("generate", "--mode", "uuid", "--uuid-version", "5", "--namespace", "dns", "--name", "example.com")
    r2 = cli("generate", "--mode", "uuid", "--uuid-version", "5", "--namespace", "dns", "--name", "example.com")
    assert r1.returncode == 0
    assert r1.stdout == r2.stdout


def test_uuid5_missing_namespace(cli):
    """UUID5 without namespace produces an error."""
    result = cli("generate", "--mode", "uuid", "--uuid-version", "5", "--name", "test")
    assert result.returncode == 1


def test_token_length(cli):
    """Token mode generates output of approximately the requested length."""
    result = cli("generate", "--mode", "token", "--length", "16", "--format", "hex")
    assert result.returncode == 0
    token = result.stdout.decode().strip()
    assert len(token) == 16


def test_password_charset(cli):
    """Password mode with digits charset only produces digits."""
    result = cli("generate", "--mode", "password", "--length", "20", "--charset", "digits")
    assert result.returncode == 0
    pwd = result.stdout.decode().strip()
    assert pwd.isdigit()
    assert len(pwd) == 20


def test_bytes_mode(cli):
    """Bytes mode produces hex output."""
    result = cli("generate", "--mode", "bytes", "--length", "8")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert len(output) == 16
    int(output, 16)


def test_count_multiple(cli):
    """Count flag generates the correct number of items."""
    result = cli("generate", "--mode", "password", "--count", "5", "--length", "10")
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 5
