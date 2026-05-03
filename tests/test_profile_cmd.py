"""Tests for the profile subcommand."""

import pytest


def test_profile_simple_script(cli, tmp_file):
    """Profile a simple script and get output."""
    script = tmp_file("x = sum(range(1000))\n", name="simple.py")
    result = cli("profile", str(script))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "function calls" in output.lower() or "ncalls" in output.lower()


def test_profile_with_function(cli, tmp_file):
    """Profile script with named function appears in output."""
    code = "def my_func():\n    return sum(range(100))\n\nmy_func()\n"
    script = tmp_file(code, name="func.py")
    result = cli("profile", str(script))
    assert result.returncode == 0
    assert "my_func" in result.stdout.decode()


def test_sort_by_tottime(cli, tmp_file):
    """Sort by tottime changes output."""
    script = tmp_file("x = list(range(100))\n", name="sort.py")
    result = cli("profile", "--sort", "tottime", str(script))
    assert result.returncode == 0


def test_nonexistent_script(cli):
    """Non-existent script produces error."""
    result = cli("profile", "/nonexistent/script.py")
    assert result.returncode == 1


def test_syntax_error_script(cli, tmp_file):
    """Script with syntax error produces error."""
    script = tmp_file("def broken(\n", name="bad.py")
    result = cli("profile", str(script))
    assert result.returncode == 1
