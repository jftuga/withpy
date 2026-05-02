"""Tests for the glob subcommand."""

import os

import pytest


def test_basic_glob(cli, tmp_path):
    """Glob matches files by pattern."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "c.py").write_text("c")
    pattern = str(tmp_path / "*.txt")
    result = cli("glob", pattern)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "a.txt" in output
    assert "b.txt" in output
    assert "c.py" not in output


def test_count(cli, tmp_path):
    """Glob count reports match count."""
    (tmp_path / "x.log").write_text("")
    (tmp_path / "y.log").write_text("")
    pattern = str(tmp_path / "*.log")
    result = cli("glob", "--count", pattern)
    assert result.returncode == 0
    assert result.stdout.strip() == b"2"


def test_recursive(cli, tmp_path):
    """Glob recursive matches nested files."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.txt").write_text("")
    pattern = str(tmp_path / "**" / "*.txt")
    result = cli("glob", "--recursive", pattern)
    assert result.returncode == 0
    assert b"deep.txt" in result.stdout


def test_no_matches(cli, tmp_path):
    """Glob with no matches produces empty output."""
    pattern = str(tmp_path / "*.nonexistent")
    result = cli("glob", "--count", pattern)
    assert result.returncode == 0
    assert result.stdout.strip() == b"0"


def test_size_flag(cli, tmp_path):
    """Glob with --size shows file sizes."""
    (tmp_path / "file.dat").write_bytes(b"x" * 100)
    pattern = str(tmp_path / "*.dat")
    result = cli("glob", "--size", pattern)
    assert result.returncode == 0
    assert b"100" in result.stdout
