"""Tests for the sort subcommand."""

import pytest


def test_alpha_sort(cli):
    """Sort alpha orders lines alphabetically."""
    result = cli("sort", "--mode", "alpha", input_data=b"cherry\napple\nbanana\n")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert lines == ["apple", "banana", "cherry"]


def test_numeric_sort(cli):
    """Sort numeric orders by number value."""
    result = cli("sort", "--mode", "numeric", input_data=b"10\n2\n100\n1\n")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert lines == ["1", "2", "10", "100"]


def test_length_sort(cli):
    """Sort length orders by line length."""
    result = cli("sort", "--mode", "length", input_data=b"aa\naaa\na\n")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert lines == ["a", "aa", "aaa"]


def test_reverse(cli):
    """Sort reverse flag reverses order."""
    result = cli("sort", "--mode", "alpha", "--reverse", input_data=b"a\nb\nc\n")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert lines == ["c", "b", "a"]


def test_top_n(cli):
    """Sort top returns largest N items."""
    result = cli("sort", "--mode", "top", "--count", "2", input_data=b"5\n1\n9\n3\n")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert "9" in lines
    assert "5" in lines
    assert len(lines) == 2


def test_unique(cli):
    """Sort unique removes duplicates."""
    result = cli("sort", "--mode", "alpha", "--unique", input_data=b"b\na\nb\na\nc\n")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert lines == ["a", "b", "c"]


def test_rank(cli):
    """Sort rank assigns positions."""
    result = cli("sort", "--mode", "rank", input_data=b"banana\napple\ncherry\n")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "1\tapple" in output or "2\tbanana" in output
