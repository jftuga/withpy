"""Tests for the diff subcommand."""

import pytest


def test_identical_files(cli, tmp_file):
    """Identical files return exit code 0."""
    path = tmp_file("same content\n")
    result = cli("diff", str(path), str(path))
    assert result.returncode == 0


def test_different_files(cli, tmp_path):
    """Different files return exit code 1."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("line one\n")
    f2.write_text("line two\n")
    result = cli("diff", str(f1), str(f2))
    assert result.returncode == 1
    output = result.stdout.decode()
    assert "---" in output or "line" in output


def test_unified_format(cli, tmp_path):
    """Unified format shows +/- markers."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("old line\n")
    f2.write_text("new line\n")
    result = cli("diff", "--format", "unified", str(f1), str(f2))
    assert result.returncode == 1
    output = result.stdout.decode()
    assert "-old line" in output
    assert "+new line" in output


def test_html_format(cli, tmp_path):
    """HTML format produces HTML output."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("alpha\n")
    f2.write_text("beta\n")
    result = cli("diff", "--format", "html", str(f1), str(f2))
    assert result.returncode == 1
    assert b"<table" in result.stdout


def test_context_lines(cli, tmp_path):
    """Context parameter controls surrounding lines."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a\nb\nc\nd\ne\nf\n")
    f2.write_text("a\nb\nX\nd\ne\nf\n")
    result = cli("diff", "--format", "unified", "--context", "1", str(f1), str(f2))
    assert result.returncode == 1


def test_missing_file(cli, tmp_path):
    """Missing file returns exit code 2."""
    f1 = tmp_path / "exists.txt"
    f1.write_text("content\n")
    result = cli("diff", str(f1), "/nonexistent/file.txt")
    assert result.returncode == 2
