"""Tests for the calc subcommand."""

import pytest


def test_basic_arithmetic(cli):
    """Basic arithmetic expressions evaluate correctly."""
    result = cli("calc", "2+2")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "4"


def test_float_division(cli):
    """Division produces float results."""
    result = cli("calc", "10/3")
    assert result.returncode == 0
    assert "3.333" in result.stdout.decode()


def test_power(cli):
    """Exponentiation works."""
    result = cli("calc", "2**10")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "1024"


def test_math_function(cli):
    """Math functions are supported."""
    result = cli("calc", "sqrt(16)")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "4"


def test_constants(cli):
    """Math constants are available."""
    result = cli("calc", "pi")
    assert result.returncode == 0
    assert "3.14159" in result.stdout.decode()


def test_complex_expression(cli):
    """Nested expressions evaluate correctly."""
    result = cli("calc", "sqrt(9)+2*3")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "9"


def test_reject_import(cli):
    """Import statements are rejected."""
    result = cli("calc", "import os")
    assert result.returncode == 1


def test_reject_builtins(cli):
    """Disallowed functions are rejected."""
    result = cli("calc", "open('/etc/passwd')")
    assert result.returncode == 1


def test_hex_output(cli):
    """Hex output base works."""
    result = cli("calc", "--base", "hex", "255")
    assert result.returncode == 0
    assert "0xff" in result.stdout.decode()


def test_stats_mode(cli):
    """Stats mode computes basic statistics."""
    result = cli("calc", "--mode", "stats", "1", "2", "3", "4", "5")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "mean" in output
    assert "3" in output


def test_precision(cli):
    """Precision flag limits decimal places."""
    result = cli("calc", "--precision", "2", "1/3")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "0.33"
