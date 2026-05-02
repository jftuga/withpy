"""Tests for the netrc subcommand."""

import pytest


_SAMPLE_NETRC = """\
machine github.com
login user1
password secret123

machine gitlab.com
login user2
password pass456
"""


def test_lookup(cli, tmp_path):
    """Netrc lookup finds credentials for a host."""
    f = tmp_path / ".netrc"
    f.write_text(_SAMPLE_NETRC)
    result = cli("netrc", "--mode", "lookup", "--file", str(f), "github.com")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "user1" in output
    assert "secret123" in output


def test_hosts(cli, tmp_path):
    """Netrc hosts lists all machines."""
    f = tmp_path / ".netrc"
    f.write_text(_SAMPLE_NETRC)
    result = cli("netrc", "--mode", "hosts", "--file", str(f))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "github.com" in output
    assert "gitlab.com" in output


def test_dump_json(cli, tmp_path):
    """Netrc dump in JSON format."""
    f = tmp_path / ".netrc"
    f.write_text(_SAMPLE_NETRC)
    result = cli("netrc", "--mode", "dump", "--file", str(f), "--format", "json")
    assert result.returncode == 0
    assert b'"github.com"' in result.stdout


def test_lookup_missing_host(cli, tmp_path):
    """Netrc lookup errors on unknown host."""
    f = tmp_path / ".netrc"
    f.write_text(_SAMPLE_NETRC)
    result = cli("netrc", "--mode", "lookup", "--file", str(f), "unknown.com")
    assert result.returncode == 1


def test_file_not_found(cli, tmp_path):
    """Netrc errors on missing file."""
    result = cli("netrc", "--mode", "hosts", "--file", str(tmp_path / "nofile"))
    assert result.returncode == 1
