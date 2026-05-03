"""Tests for the repr subcommand."""

import pytest


def test_pprint_mode(cli):
    """Repr pprint formats JSON as Python pprint."""
    result = cli("repr", "--mode", "pprint", input_data=b'{"key": [1, 2, 3]}')
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "key" in output
    assert "[1, 2, 3]" in output


def test_repr_mode(cli):
    """Repr repr shows Python repr."""
    result = cli("repr", "--mode", "repr", input_data=b'{"a": true, "b": null}')
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "True" in output
    assert "None" in output


def test_depth_mode(cli):
    """Repr depth measures nesting."""
    result = cli("repr", "--mode", "depth", input_data=b'{"a": {"b": {"c": 1}}}')
    assert result.returncode == 0
    assert b"max_depth: 3" in result.stdout


def test_invalid_json(cli):
    """Repr rejects invalid JSON."""
    result = cli("repr", "--mode", "pprint", input_data=b"not json")
    assert result.returncode == 1
