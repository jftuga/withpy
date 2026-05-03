"""Tests for the hexdump subcommand."""

import pytest


def test_known_output(cli):
    """Hexdump of 'Hello' matches expected format."""
    result = cli("hexdump", input_data=b"Hello")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "48 65 6c 6c 6f" in output
    assert "|Hello|" in output


def test_offset_display(cli):
    """Hexdump starts with correct offset."""
    result = cli("hexdump", input_data=b"A" * 32)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "00000000" in output
    assert "00000010" in output


def test_width_parameter(cli):
    """Width parameter changes bytes per line."""
    result = cli("hexdump", "--width", "8", input_data=b"ABCDEFGHIJ")
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 2


def test_no_ascii(cli):
    """No-ascii flag suppresses ASCII column."""
    result = cli("hexdump", "--no-ascii", input_data=b"Hello")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "|" not in output
    assert "48 65 6c 6c 6f" in output


def test_offset_parameter(cli):
    """Offset parameter skips initial bytes."""
    result = cli("hexdump", "--offset", "3", input_data=b"ABCHello")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "48 65 6c 6c 6f" in output


def test_length_parameter(cli):
    """Length parameter limits output bytes."""
    result = cli("hexdump", "--length", "3", input_data=b"HelloWorld")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "48 65 6c" in output
    assert "6c 6f" not in output


def test_reverse_roundtrip(cli):
    """Hexdump then reverse produces original data."""
    data = b"Roundtrip test data!"
    dump = cli("hexdump", input_data=data)
    assert dump.returncode == 0
    reverse = cli("hexdump", "--reverse", input_data=dump.stdout)
    assert reverse.returncode == 0
    assert reverse.stdout == data


def test_non_printable(cli):
    """Non-printable bytes shown as dots in ASCII column."""
    result = cli("hexdump", input_data=b"\x00\x01\x02\x7f")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "|....|" in output
