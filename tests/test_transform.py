"""Tests for the transform subcommand."""

import pytest


def test_upper(cli):
    """Upper mode converts to uppercase."""
    result = cli("transform", "--mode", "upper", input_data=b"hello world")
    assert result.returncode == 0
    assert result.stdout.strip() == b"HELLO WORLD"


def test_lower(cli):
    """Lower mode converts to lowercase."""
    result = cli("transform", "--mode", "lower", input_data=b"HELLO WORLD")
    assert result.returncode == 0
    assert result.stdout.strip() == b"hello world"


def test_title(cli):
    """Title mode capitalizes first letter of each word."""
    result = cli("transform", "--mode", "title", input_data=b"hello world")
    assert result.returncode == 0
    assert result.stdout.strip() == b"Hello World"


def test_snake_case(cli):
    """Snake mode converts camelCase to snake_case."""
    result = cli("transform", "--mode", "snake", input_data=b"helloWorld\n")
    assert result.returncode == 0
    assert b"hello_world" in result.stdout


def test_camel_case(cli):
    """Camel mode converts words to camelCase."""
    result = cli("transform", "--mode", "camel", input_data=b"hello world\n")
    assert result.returncode == 0
    assert b"helloWorld" in result.stdout


def test_regex_replace(cli):
    """Replace mode substitutes regex matches."""
    result = cli("transform", "--mode", "replace", "--pattern", r"\d+", "--replacement", "X", input_data=b"abc123def456")
    assert result.returncode == 0
    assert result.stdout.strip() == b"abcXdefX"


def test_wrap(cli):
    """Wrap mode wraps text at specified width."""
    text = b"word " * 20
    result = cli("transform", "--mode", "wrap", "--width", "20", input_data=text)
    assert result.returncode == 0
    for line in result.stdout.decode().splitlines():
        assert len(line) <= 20


def test_count(cli):
    """Count mode counts regex matches."""
    result = cli("transform", "--mode", "count", "--pattern", r"\d", input_data=b"a1b2c3d4")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "4"


def test_invalid_regex(cli):
    """Invalid regex produces an error."""
    result = cli("transform", "--mode", "replace", "--pattern", "[invalid", input_data=b"test")
    assert result.returncode == 1


def test_normalize(cli):
    """Normalize mode applies Unicode NFC."""
    result = cli("transform", "--mode", "normalize", "--form", "NFC", input_data="é".encode())
    assert result.returncode == 0
