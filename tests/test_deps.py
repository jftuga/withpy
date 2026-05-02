"""Tests for the deps subcommand."""

import pytest


def test_sort_simple(cli):
    """Topological sort of simple DAG."""
    graph = b'{"a": ["b"], "b": ["c"], "c": []}'
    result = cli("deps", "--mode", "sort", input_data=graph)
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert lines.index("c") < lines.index("b") < lines.index("a")


def test_cycle_detection(cli):
    """Cycle in graph produces error."""
    graph = b'{"a": ["b"], "b": ["c"], "c": ["a"]}'
    result = cli("deps", "--mode", "check", input_data=graph)
    assert result.returncode == 1
    assert b"cycle" in result.stderr.lower()


def test_no_cycle(cli):
    """Acyclic graph passes check."""
    graph = b'{"a": ["b"], "b": [], "c": ["b"]}'
    result = cli("deps", "--mode", "check", input_data=graph)
    assert result.returncode == 0
    assert b"no cycle" in result.stdout.lower()


def test_dot_output(cli):
    """DOT mode produces valid graphviz format."""
    graph = b'{"a": ["b"], "b": []}'
    result = cli("deps", "--mode", "dot", input_data=graph)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "digraph" in output
    assert '"a" -> "b"' in output


def test_levels(cli):
    """Levels mode groups nodes by depth."""
    graph = b'{"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}'
    result = cli("deps", "--mode", "levels", input_data=graph)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Level 0" in output


def test_pairs_format(cli):
    """Pairs input format works."""
    pairs = b"a b\nb c\nc\n"
    result = cli("deps", "--mode", "sort", "--format", "pairs", input_data=pairs)
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert "c" in lines
    assert "a" in lines
