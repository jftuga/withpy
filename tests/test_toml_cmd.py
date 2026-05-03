"""Tests for the toml subcommand."""

import pytest


def test_tojson_basic(cli):
    """Convert simple TOML to JSON."""
    toml_data = b'[section]\nkey = "value"\nnumber = 42\n'
    result = cli("toml", input_data=toml_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert '"section"' in output
    assert '"key"' in output
    assert '"value"' in output
    assert "42" in output


def test_validate_valid(cli):
    """Valid TOML passes validation."""
    result = cli("toml", "--mode", "validate", input_data=b'key = "value"\n')
    assert result.returncode == 0
    assert b"valid" in result.stdout.lower()


def test_validate_invalid(cli):
    """Invalid TOML fails validation."""
    result = cli("toml", "--mode", "validate", input_data=b'[invalid\nkey value\n')
    assert result.returncode == 1


def test_query_path(cli):
    """Query mode extracts nested value."""
    toml_data = b'[database]\nhost = "localhost"\nport = 5432\n'
    result = cli("toml", "--mode", "query", "--path", "database.host", input_data=toml_data)
    assert result.returncode == 0
    assert "localhost" in result.stdout.decode()


def test_query_missing_path(cli):
    """Query with missing path returns error."""
    result = cli("toml", "--mode", "query", "--path", "nonexistent", input_data=b'key = "value"\n')
    assert result.returncode == 1


def test_nested_tables(cli):
    """Nested TOML tables convert correctly."""
    toml_data = b'[server]\n[server.database]\nname = "mydb"\n'
    result = cli("toml", input_data=toml_data)
    assert result.returncode == 0
    assert "mydb" in result.stdout.decode()


def test_array_of_tables(cli):
    """TOML array of tables converts to JSON array."""
    toml_data = b'[[items]]\nname = "a"\n[[items]]\nname = "b"\n'
    result = cli("toml", input_data=toml_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert '"a"' in output
    assert '"b"' in output
