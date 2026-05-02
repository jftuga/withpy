"""Tests for the config subcommand."""

import pytest


_SAMPLE_INI = """\
[database]
host = localhost
port = 5432
name = mydb

[app]
debug = true
secret = abc123
"""


def test_sections(cli, tmp_path):
    """Config sections lists all sections."""
    f = tmp_path / "test.ini"
    f.write_text(_SAMPLE_INI)
    result = cli("config", "--mode", "sections", str(f))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "database" in output
    assert "app" in output


def test_get_section(cli, tmp_path):
    """Config get shows all keys in a section."""
    f = tmp_path / "test.ini"
    f.write_text(_SAMPLE_INI)
    result = cli("config", "--mode", "get", "--section", "database", str(f))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "host = localhost" in output
    assert "port = 5432" in output


def test_get_key(cli, tmp_path):
    """Config get with key returns specific value."""
    f = tmp_path / "test.ini"
    f.write_text(_SAMPLE_INI)
    result = cli("config", "--mode", "get", "--section", "database", "--key", "port", str(f))
    assert result.returncode == 0
    assert result.stdout.strip() == b"5432"


def test_tojson(cli, tmp_path):
    """Config tojson converts INI to JSON."""
    f = tmp_path / "test.ini"
    f.write_text(_SAMPLE_INI)
    result = cli("config", "--mode", "tojson", str(f))
    assert result.returncode == 0
    assert b'"database"' in result.stdout
    assert b'"localhost"' in result.stdout


def test_validate(cli, tmp_path):
    """Config validate confirms valid INI."""
    f = tmp_path / "test.ini"
    f.write_text(_SAMPLE_INI)
    result = cli("config", "--mode", "validate", str(f))
    assert result.returncode == 0
    assert b"valid" in result.stdout


def test_missing_section(cli, tmp_path):
    """Config get errors on missing section."""
    f = tmp_path / "test.ini"
    f.write_text(_SAMPLE_INI)
    result = cli("config", "--mode", "get", "--section", "nosuch", str(f))
    assert result.returncode == 1
