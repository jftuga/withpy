"""Tests for the iter subcommand."""

import pytest


def test_combinations(cli):
    """Iter combinations produces correct pairs."""
    result = cli("iter", "--mode", "combinations", "--r", "2", "a", "b", "c")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert "a,b" in output
    assert "a,c" in output
    assert "b,c" in output
    assert len(output) == 3


def test_permutations(cli):
    """Iter permutations produces all orderings."""
    result = cli("iter", "--mode", "permutations", "x", "y")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert "x,y" in output
    assert "y,x" in output


def test_product(cli):
    """Iter product produces cartesian product."""
    result = cli("iter", "--mode", "product", "--r", "2", "0", "1")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert len(output) == 4


def test_chunk(cli):
    """Iter chunk splits items into groups."""
    result = cli("iter", "--mode", "chunk", "--size", "2", "a", "b", "c", "d", "e")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert output[0] == "a,b"
    assert output[1] == "c,d"
    assert output[2] == "e"


def test_accumulate_numbers(cli):
    """Iter accumulate sums numbers."""
    result = cli("iter", "--mode", "accumulate", "1", "2", "3", "4")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert output == ["1", "3", "6", "10"]


def test_reduce_numbers(cli):
    """Iter reduce produces a single sum."""
    result = cli("iter", "--mode", "reduce", "5", "10", "15")
    assert result.returncode == 0
    assert result.stdout.strip() == b"30"


def test_unique(cli):
    """Iter unique deduplicates items."""
    result = cli("iter", "--mode", "unique", "a", "b", "a", "c", "b")
    assert result.returncode == 0
    output = result.stdout.decode().splitlines()
    assert output == ["a", "b", "c"]
