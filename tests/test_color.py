"""Tests for the color subcommand."""

import pytest


def test_hex_to_rgb(cli):
    """Convert hex to RGB."""
    result = cli("color", "--from", "hex", "--to", "rgb", "#FF0000")
    assert result.returncode == 0
    assert "255,0,0" in result.stdout.decode()


def test_rgb_to_hex(cli):
    """Convert RGB to hex."""
    result = cli("color", "--from", "rgb", "--to", "hex", "0,255,0")
    assert result.returncode == 0
    assert "00ff00" in result.stdout.decode()


def test_hex_to_hsl(cli):
    """Convert pure red to HSL."""
    result = cli("color", "--from", "hex", "--to", "hsl", "#FF0000")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert output.startswith("0,")


def test_all_output(cli):
    """Convert to all formats."""
    result = cli("color", "--from", "hex", "--to", "all", "#0000FF")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "hex:" in output
    assert "rgb:" in output
    assert "hsl:" in output
    assert "hsv:" in output


def test_palette_count(cli):
    """Palette generates correct number of colors."""
    result = cli("color", "--mode", "palette", "--steps", "8")
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 8


def test_blend(cli):
    """Blend between two colors produces correct count."""
    result = cli("color", "--mode", "blend", "--from", "hex", "--steps", "5", "#000000", "#FFFFFF")
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 5


def test_invalid_hex(cli):
    """Invalid hex color produces an error."""
    result = cli("color", "--from", "hex", "--to", "rgb", "GGGGGG")
    assert result.returncode == 1


def test_roundtrip_hex_rgb_hex(cli):
    """Hex -> RGB -> Hex roundtrip preserves color."""
    r1 = cli("color", "--from", "hex", "--to", "rgb", "#1a2b3c")
    assert r1.returncode == 0
    rgb = r1.stdout.decode().strip()
    r2 = cli("color", "--from", "rgb", "--to", "hex", rgb)
    assert r2.returncode == 0
    assert "1a2b3c" in r2.stdout.decode()
