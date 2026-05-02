"""Tests for the pydis subcommand."""

import pytest


def test_dis_basic(cli, tmp_path):
    """Pydis disassembles Python source."""
    src = tmp_path / "simple.py"
    src.write_text("x = 1 + 2\n")
    result = cli("pydis", "--mode", "dis", str(src))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "LOAD_CONST" in output or "BINARY_OP" in output or "STORE_NAME" in output


def test_info(cli, tmp_path):
    """Pydis shows code info."""
    src = tmp_path / "func.py"
    src.write_text("def hello():\n    return 42\n")
    result = cli("pydis", "--mode", "info", str(src))
    assert result.returncode == 0


def test_stats(cli, tmp_path):
    """Pydis shows instruction statistics."""
    src = tmp_path / "loop.py"
    src.write_text("for i in range(10):\n    print(i)\n")
    result = cli("pydis", "--mode", "stats", str(src))
    assert result.returncode == 0
    assert b"Total instructions:" in result.stdout


def test_syntax_error(cli, tmp_path):
    """Pydis reports syntax errors."""
    src = tmp_path / "bad.py"
    src.write_text("def broken(\n")
    result = cli("pydis", "--mode", "dis", str(src))
    assert result.returncode == 1
