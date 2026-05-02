"""Tests for the info subcommand."""

import json
import pytest


def test_all_mode(cli):
    """All mode produces output with expected sections."""
    result = cli("info", "--mode", "all")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "[os]" in output or "system" in output


def test_os_mode(cli):
    """OS mode contains platform information."""
    result = cli("info", "--mode", "os")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "system" in output.lower() or "Darwin" in output or "Linux" in output


def test_python_mode(cli):
    """Python mode contains version information."""
    result = cli("info", "--mode", "python")
    assert result.returncode == 0
    assert "3.14" in result.stdout.decode()


def test_json_format(cli):
    """JSON output is valid JSON."""
    result = cli("info", "--mode", "all", "--format", "json")
    assert result.returncode == 0
    data = json.loads(result.stdout.decode())
    assert "os" in data


def test_csv_format(cli):
    """CSV format produces rows."""
    result = cli("info", "--mode", "os", "--format", "csv")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "section" in output
    assert "key" in output


def test_xml_format(cli):
    """XML format produces XML output."""
    result = cli("info", "--mode", "os", "--format", "xml")
    assert result.returncode == 0
    assert "<?xml" in result.stdout.decode()


def test_key_lookup(cli):
    """Key flag retrieves a specific value."""
    result = cli("info", "--mode", "os", "--key", "system")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert output in ("Darwin", "Linux", "Windows")
