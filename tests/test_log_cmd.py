"""Tests for the log subcommand."""

import pytest


_SAMPLE_LOG = """2024-01-01 10:00:00 INFO Starting application
2024-01-01 10:00:01 DEBUG Loading config
2024-01-01 10:00:02 WARNING Disk space low
2024-01-01 10:00:03 ERROR Connection failed
2024-01-01 10:00:04 INFO Retrying connection
2024-01-01 10:00:05 ERROR Timeout reached
2024-01-01 10:00:06 CRITICAL System shutdown
2024-01-01 10:00:07 INFO Cleanup complete
"""


def test_tail(cli, tmp_file):
    """Tail shows last N lines."""
    path = tmp_file(_SAMPLE_LOG, name="app.log")
    result = cli("log", "--mode", "tail", "--lines", "3", str(path))
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 3
    assert "Cleanup complete" in lines[-1]


def test_grep(cli, tmp_file):
    """Grep filters by regex pattern."""
    path = tmp_file(_SAMPLE_LOG, name="app.log")
    result = cli("log", "--mode", "grep", "--pattern", "ERROR", str(path))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Connection failed" in output
    assert "Timeout reached" in output
    assert "INFO" not in output


def test_level_filter(cli, tmp_file):
    """Level mode filters by minimum level."""
    path = tmp_file(_SAMPLE_LOG, name="app.log")
    result = cli("log", "--mode", "level", "--level", "ERROR", str(path))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "ERROR" in output
    assert "CRITICAL" in output
    assert "INFO" not in output
    assert "DEBUG" not in output


def test_stats(cli, tmp_file):
    """Stats mode counts log levels."""
    path = tmp_file(_SAMPLE_LOG, name="app.log")
    result = cli("log", "--mode", "stats", str(path))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "ERROR" in output
    assert "INFO" in output


def test_parse(cli, tmp_file):
    """Parse mode outputs JSON."""
    path = tmp_file(_SAMPLE_LOG, name="app.log")
    result = cli("log", "--mode", "parse", str(path))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "timestamp" in output
    assert "level" in output


def test_nonexistent_file(cli):
    """Non-existent file produces error."""
    result = cli("log", "--mode", "tail", "/nonexistent/file.log")
    assert result.returncode == 1


def test_grep_no_pattern(cli, tmp_file):
    """Grep without pattern produces error."""
    path = tmp_file("log\n", name="app.log")
    result = cli("log", "--mode", "grep", str(path))
    assert result.returncode == 1
