"""Tests for the struct subcommand."""

import pytest


def test_pack_known(cli):
    """Pack >I 42 produces expected hex."""
    result = cli("struct", "--mode", "pack", "--format", ">I", "42")
    assert result.returncode == 0
    assert "0000002a" in result.stdout.decode()


def test_unpack_known(cli):
    """Unpack >I from known hex."""
    result = cli("struct", "--mode", "unpack", "--format", ">I", "0000002a")
    assert result.returncode == 0
    assert "42" in result.stdout.decode()


def test_roundtrip(cli):
    """Pack then unpack produces original values."""
    pack = cli("struct", "--mode", "pack", "--format", ">2H", "1000", "2000")
    assert pack.returncode == 0
    hex_val = pack.stdout.decode().strip()
    unpack = cli("struct", "--mode", "unpack", "--format", ">2H", hex_val)
    assert unpack.returncode == 0
    assert "1000" in unpack.stdout.decode()
    assert "2000" in unpack.stdout.decode()


def test_size(cli):
    """Size mode computes correct struct size."""
    result = cli("struct", "--mode", "size", "--format", ">3I")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "12"


def test_endian_little(cli):
    """Little endian produces different output than big endian."""
    big = cli("struct", "--mode", "pack", "--format", ">H", "256")
    little = cli("struct", "--mode", "pack", "--format", "<H", "256")
    assert big.returncode == 0
    assert little.returncode == 0
    assert big.stdout != little.stdout


def test_wrong_values(cli):
    """Wrong number of values for format produces error."""
    result = cli("struct", "--mode", "pack", "--format", ">3I", "1", "2")
    assert result.returncode == 1


def test_hex_input_values(cli):
    """Pack accepts hex values with 0x prefix."""
    result = cli("struct", "--mode", "pack", "--format", ">I", "0xFF")
    assert result.returncode == 0
    assert "000000ff" in result.stdout.decode()
