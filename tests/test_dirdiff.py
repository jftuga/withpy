"""Tests for the dirdiff subcommand."""

import pytest


def test_identical_dirs(cli, tmp_path):
    """Identical directories report no differences."""
    d1 = tmp_path / "left"
    d2 = tmp_path / "right"
    d1.mkdir()
    d2.mkdir()
    (d1 / "file.txt").write_text("same")
    (d2 / "file.txt").write_text("same")
    result = cli("dirdiff", str(d1), str(d2))
    assert result.returncode == 0
    assert "Identical" in result.stdout.decode() or "identical" in result.stdout.decode().lower()


def test_left_only(cli, tmp_path):
    """File only in left dir appears in left-only."""
    d1 = tmp_path / "left"
    d2 = tmp_path / "right"
    d1.mkdir()
    d2.mkdir()
    (d1 / "only_left.txt").write_text("left")
    (d1 / "common.txt").write_text("same")
    (d2 / "common.txt").write_text("same")
    result = cli("dirdiff", "--mode", "left-only", str(d1), str(d2))
    assert result.returncode == 0
    assert "only_left" in result.stdout.decode()


def test_right_only(cli, tmp_path):
    """File only in right dir appears in right-only."""
    d1 = tmp_path / "left"
    d2 = tmp_path / "right"
    d1.mkdir()
    d2.mkdir()
    (d2 / "only_right.txt").write_text("right")
    result = cli("dirdiff", "--mode", "right-only", str(d1), str(d2))
    assert result.returncode == 0
    assert "only_right" in result.stdout.decode()


def test_diff_files(cli, tmp_path):
    """Files with different content appear in report."""
    d1 = tmp_path / "left"
    d2 = tmp_path / "right"
    d1.mkdir()
    d2.mkdir()
    (d1 / "changed.txt").write_text("version 1")
    (d2 / "changed.txt").write_text("version 2")
    result = cli("dirdiff", str(d1), str(d2))
    assert result.returncode == 0
    assert "changed.txt" in result.stdout.decode()
    assert "Differing" in result.stdout.decode() or "differ" in result.stdout.decode().lower()


def test_nonexistent_dir(cli):
    """Non-existent directory produces error."""
    result = cli("dirdiff", "/nonexistent1", "/nonexistent2")
    assert result.returncode == 1
