"""Tests for the tokenize subcommand."""

import pytest


def test_tokenize_basic(cli, tmp_path):
    """Tokenize produces token output for Python source."""
    src = tmp_path / "hello.py"
    src.write_text("x = 1 + 2\n")
    result = cli("tokenize", "--mode", "tokens", str(src))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "NAME" in output
    assert "NUMBER" in output


def test_stats(cli, tmp_path):
    """Tokenize stats shows token distribution."""
    src = tmp_path / "sample.py"
    src.write_text("def foo(a, b):\n    return a + b\n")
    result = cli("tokenize", "--mode", "stats", str(src))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Total tokens:" in output
    assert "NAME" in output


def test_json_output(cli, tmp_path):
    """Tokenize json mode outputs valid JSON."""
    src = tmp_path / "t.py"
    src.write_text("print('hi')\n")
    result = cli("tokenize", "--mode", "json", str(src))
    assert result.returncode == 0
    assert b'"type"' in result.stdout


def test_invalid_syntax(cli, tmp_path):
    """Tokenize handles files with unclosed strings."""
    src = tmp_path / "bad.py"
    src.write_text("x = 'unclosed\n")
    result = cli("tokenize", "--mode", "tokens", str(src))
    assert result.returncode == 1
