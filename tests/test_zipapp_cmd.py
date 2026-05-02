"""Tests for the zipapp subcommand."""

import os

import pytest


def test_create_and_info(cli, tmp_path):
    """Zipapp creates an archive and info reads it."""
    src = tmp_path / "myapp"
    src.mkdir()
    (src / "__main__.py").write_text("print('hello')\n")
    (src / "helper.py").write_text("x = 1\n")
    output = str(tmp_path / "myapp.pyz")
    result = cli("zipapp", "--mode", "create", "--output", output, str(src))
    assert result.returncode == 0
    assert os.path.isfile(output)
    result = cli("zipapp", "--mode", "info", output)
    assert result.returncode == 0
    assert b"has_main: yes" in result.stdout


def test_list(cli, tmp_path):
    """Zipapp list shows archive contents."""
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "__main__.py").write_text("pass\n")
    output = str(tmp_path / "pkg.pyz")
    cli("zipapp", "--mode", "create", "--output", output, str(src))
    result = cli("zipapp", "--mode", "list", output)
    assert result.returncode == 0
    assert b"__main__.py" in result.stdout


def test_create_not_dir(cli, tmp_path):
    """Zipapp rejects non-directory source."""
    path = str(tmp_path / "notadir")
    result = cli("zipapp", "--mode", "create", path)
    assert result.returncode == 1
    assert b"not a directory" in result.stderr


def test_info_not_found(cli, tmp_path):
    """Zipapp info rejects missing file."""
    result = cli("zipapp", "--mode", "info", str(tmp_path / "missing.pyz"))
    assert result.returncode == 1
