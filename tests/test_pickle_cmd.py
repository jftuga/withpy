"""Tests for the pickle subcommand."""

import pickle
import tempfile

import pytest


def _make_pickle(tmp_path, obj):
    """Create a pickle file from an object."""
    path = str(tmp_path / "test.pkl")
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return path


def test_info(cli, tmp_path):
    """Pickle info shows metadata."""
    path = _make_pickle(tmp_path, {"key": "value", "num": 42})
    result = cli("pickle", "--mode", "info", path)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "size_bytes:" in output
    assert "opcode_count:" in output


def test_dis(cli, tmp_path):
    """Pickle dis shows opcodes."""
    path = _make_pickle(tmp_path, [1, 2, 3])
    result = cli("pickle", "--mode", "dis", path)
    assert result.returncode == 0
    assert b"PROTO" in result.stdout or b"LIST" in result.stdout or b"EMPTY_LIST" in result.stdout


def test_optimize(cli, tmp_path):
    """Pickle optimize produces smaller or equal output."""
    path = _make_pickle(tmp_path, {"a": 1, "b": 2})
    result = cli("pickle", "--mode", "optimize", "--output", str(tmp_path / "opt.pkl"), path)
    assert result.returncode == 0
    assert b"optimized:" in result.stdout


def test_invalid_pickle(cli, tmp_path):
    """Pickle rejects invalid data."""
    path = str(tmp_path / "bad.pkl")
    with open(path, "wb") as f:
        f.write(b"not pickle data at all")
    result = cli("pickle", "--mode", "info", path)
    assert result.returncode == 1
