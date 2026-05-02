"""Tests for the json subcommand."""

import pytest


def test_pretty_print(cli):
    """Pretty mode formats JSON with indentation."""
    result = cli("json", "--mode", "pretty", input_data=b'{"a":1,"b":2}')
    assert result.returncode == 0
    output = result.stdout.decode()
    assert '"a": 1' in output
    assert '"b": 2' in output


def test_compact(cli):
    """Compact mode removes whitespace."""
    result = cli("json", "--mode", "compact", input_data=b'{"a": 1, "b": 2}')
    assert result.returncode == 0
    assert result.stdout.strip() == b'{"a":1,"b":2}'


def test_validate_valid(cli):
    """Validate mode returns 0 for valid JSON."""
    result = cli("json", "--mode", "validate", input_data=b'[1, 2, 3]')
    assert result.returncode == 0
    assert b"valid" in result.stdout.lower()


def test_validate_invalid(cli):
    """Validate mode returns 1 for invalid JSON."""
    result = cli("json", "--mode", "validate", input_data=b'{bad json}')
    assert result.returncode == 1


def test_query_simple(cli):
    """Query mode extracts a nested value."""
    data = b'{"a": {"b": {"c": 42}}}'
    result = cli("json", "--mode", "query", "--path", "a.b.c", input_data=data)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "42"


def test_query_array_index(cli):
    """Query mode supports array indexing."""
    data = b'{"items": [10, 20, 30]}'
    result = cli("json", "--mode", "query", "--path", "items[1]", input_data=data)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "20"


def test_query_missing_key(cli):
    """Query mode with missing key returns error."""
    data = b'{"a": 1}'
    result = cli("json", "--mode", "query", "--path", "b", input_data=data)
    assert result.returncode == 1


def test_keys(cli):
    """Keys mode lists top-level keys."""
    data = b'{"alpha": 1, "beta": 2, "gamma": 3}'
    result = cli("json", "--mode", "keys", input_data=data)
    assert result.returncode == 0
    keys = result.stdout.decode().strip().splitlines()
    assert "alpha" in keys
    assert "beta" in keys
    assert "gamma" in keys


def test_type_object(cli):
    """Type mode identifies objects."""
    result = cli("json", "--mode", "type", input_data=b'{}')
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "object"


def test_type_array(cli):
    """Type mode identifies arrays."""
    result = cli("json", "--mode", "type", input_data=b'[]')
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "array"


def test_sort_keys(cli):
    """Sort-keys flag produces sorted output."""
    data = b'{"z": 1, "a": 2, "m": 3}'
    result = cli("json", "--mode", "pretty", "--sort-keys", input_data=data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert output.index('"a"') < output.index('"m"') < output.index('"z"')
