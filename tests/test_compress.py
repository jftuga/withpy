"""Tests for the compress subcommand."""

import pytest


@pytest.mark.parametrize("fmt", ["gzip", "zlib", "bz2", "lzma"])
def test_roundtrip(cli, fmt):
    """Compress then decompress produces original data."""
    data = b"The quick brown fox jumps over the lazy dog" * 10
    enc = cli("compress", "--format", fmt, input_data=data)
    assert enc.returncode == 0
    assert enc.stdout != data
    dec = cli("compress", "--mode", "decompress", "--format", fmt, input_data=enc.stdout)
    assert dec.returncode == 0
    assert dec.stdout == data


def test_compression_reduces_size(cli):
    """Compressed output is smaller than input for compressible data."""
    data = b"A" * 10000
    result = cli("compress", "--format", "gzip", input_data=data)
    assert result.returncode == 0
    assert len(result.stdout) < len(data)


def test_level_parameter(cli):
    """Compression level affects output size."""
    data = b"Hello world! " * 100
    r1 = cli("compress", "--format", "gzip", "--level", "1", input_data=data)
    r9 = cli("compress", "--format", "gzip", "--level", "9", input_data=data)
    assert r1.returncode == 0
    assert r9.returncode == 0
    assert len(r9.stdout) <= len(r1.stdout)


def test_decompress_garbage(cli):
    """Decompressing invalid data produces an error."""
    result = cli("compress", "--mode", "decompress", "--format", "gzip", input_data=b"not compressed data")
    assert result.returncode == 1


def test_auto_detect_gzip(cli):
    """Decompress auto-detects gzip format."""
    data = b"auto detect test"
    enc = cli("compress", "--format", "gzip", input_data=data)
    assert enc.returncode == 0
    dec = cli("compress", "--mode", "decompress", input_data=enc.stdout)
    assert dec.returncode == 0
    assert dec.stdout == data


def test_file_input(cli, tmp_file):
    """Compress works with file input."""
    path = tmp_file(b"file content to compress")
    result = cli("compress", "--format", "zlib", str(path))
    assert result.returncode == 0
    assert len(result.stdout) > 0
