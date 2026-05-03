"""Tests for the archive subcommand."""

import os
import pytest


@pytest.mark.parametrize("fmt,ext", [
    ("zip", ".zip"),
    ("tar.gz", ".tar.gz"),
    ("tar.bz2", ".tar.bz2"),
    ("tar.xz", ".tar.xz"),
])
def test_roundtrip(cli, tmp_path, fmt, ext):
    """Create and extract archive preserves file content."""
    src_file = tmp_path / "hello.txt"
    src_file.write_text("hello world\n")
    archive_path = tmp_path / f"test{ext}"
    extract_dir = tmp_path / "extracted"
    result = cli("archive", "--mode", "create", "--format", fmt, "--output", str(archive_path), str(src_file))
    assert result.returncode == 0
    assert archive_path.exists()
    result = cli("archive", "--mode", "extract", "--format", fmt, "--output", str(extract_dir), str(archive_path))
    assert result.returncode == 0
    extracted_file = extract_dir / "hello.txt"
    assert extracted_file.exists()
    assert extracted_file.read_text() == "hello world\n"


def test_list_contents(cli, tmp_path):
    """List mode shows archive contents."""
    src_file = tmp_path / "data.txt"
    src_file.write_text("test data")
    archive_path = tmp_path / "test.zip"
    cli("archive", "--mode", "create", "--output", str(archive_path), str(src_file))
    result = cli("archive", "--mode", "list", str(archive_path))
    assert result.returncode == 0
    assert b"data.txt" in result.stdout


def test_auto_format_detection(cli, tmp_path):
    """Format is auto-detected from extension."""
    src_file = tmp_path / "auto.txt"
    src_file.write_text("auto detect")
    archive_path = tmp_path / "test.tar.gz"
    result = cli("archive", "--mode", "create", "--output", str(archive_path), str(src_file))
    assert result.returncode == 0


def test_missing_archive(cli):
    """Extract of nonexistent file produces error."""
    result = cli("archive", "--mode", "extract", "/nonexistent/archive.zip")
    assert result.returncode == 1


def test_directory_archive(cli, tmp_path):
    """Archiving a directory includes its contents."""
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "a.txt").write_text("file a")
    (sub / "b.txt").write_text("file b")
    archive_path = tmp_path / "dir.zip"
    result = cli("archive", "--mode", "create", "--output", str(archive_path), str(sub))
    assert result.returncode == 0
    list_result = cli("archive", "--mode", "list", str(archive_path))
    assert b"a.txt" in list_result.stdout
    assert b"b.txt" in list_result.stdout
