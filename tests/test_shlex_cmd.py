"""Tests for the shlex subcommand."""

import pytest


def test_split_basic(cli):
    """Shlex split tokenizes a command string."""
    result = cli("shlex", "--mode", "split", "echo", "hello world")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert "echo" in output
    assert "hello" in output


def test_split_quoted(cli):
    """Shlex split handles quoted strings."""
    result = cli("shlex", "--mode", "split", 'echo "hello world"')
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert "echo" in output
    assert "hello world" in output


def test_quote(cli):
    """Shlex quote wraps unsafe strings."""
    result = cli("shlex", "--mode", "quote", "hello world; rm -rf /")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert "'" in output or '"' in output


def test_join(cli):
    """Shlex join creates a properly quoted command line."""
    result = cli("shlex", "--mode", "join", "echo", "hello world", "foo bar")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert "echo" in output
    assert "hello world" in output or "'hello world'" in output
