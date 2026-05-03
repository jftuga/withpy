"""Tests for the find subcommand."""

import pytest


def test_find_by_name(cli, tmp_path):
    """Find files matching glob pattern."""
    (tmp_path / "a.py").write_text("python")
    (tmp_path / "b.txt").write_text("text")
    (tmp_path / "c.py").write_text("python2")
    result = cli("find", str(tmp_path), "--name", "*.py")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "a.py" in output
    assert "c.py" in output
    assert "b.txt" not in output


def test_find_type_dir(cli, tmp_path):
    """Find only directories."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.txt").write_text("content")
    result = cli("find", str(tmp_path), "--type", "d")
    assert result.returncode == 0
    assert "subdir" in result.stdout.decode()
    assert "file.txt" not in result.stdout.decode()


def test_find_type_file(cli, tmp_path):
    """Find only regular files."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.txt").write_text("content")
    result = cli("find", str(tmp_path), "--type", "f")
    assert result.returncode == 0
    assert "file.txt" in result.stdout.decode()
    assert "subdir" not in result.stdout.decode()


def test_count_flag(cli, tmp_path):
    """Count flag reports match count."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "c.txt").write_text("c")
    result = cli("find", str(tmp_path), "--name", "*.txt", "--count")
    assert result.returncode == 0
    assert "3" in result.stdout.decode()


def test_maxdepth(cli, tmp_path):
    """Maxdepth limits recursion."""
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "deep.txt").write_text("deep")
    (tmp_path / "shallow.txt").write_text("shallow")
    result = cli("find", str(tmp_path), "--maxdepth", "1", "--name", "*.txt")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "shallow.txt" in output
    assert "deep.txt" not in output


def test_nonexistent_path(cli):
    """Non-existent path produces error."""
    result = cli("find", "/nonexistent/path")
    assert result.returncode == 1
