"""Tests for the random subcommand."""

import pytest


def test_shuffle_seeded(cli, tmp_path):
    """Random shuffle with seed is deterministic."""
    f = tmp_path / "lines.txt"
    f.write_text("a\nb\nc\nd\ne\n")
    r1 = cli("random", "--mode", "shuffle", "--seed", "42", str(f))
    r2 = cli("random", "--mode", "shuffle", "--seed", "42", str(f))
    assert r1.returncode == 0
    assert r1.stdout == r2.stdout


def test_sample(cli, tmp_path):
    """Random sample returns requested count."""
    f = tmp_path / "data.txt"
    f.write_text("one\ntwo\nthree\nfour\nfive\n")
    result = cli("random", "--mode", "sample", "--count", "2", "--seed", "1", str(f))
    assert result.returncode == 0
    lines = [l for l in result.stdout.decode().splitlines() if l.strip()]
    assert len(lines) == 2


def test_choice(cli):
    """Random choice picks from provided items."""
    result = cli("random", "--mode", "choice", "--seed", "7", "apple", "banana", "cherry")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert output in ("apple", "banana", "cherry")


def test_dice(cli):
    """Random dice produces valid roll."""
    result = cli("random", "--mode", "dice", "--seed", "99", "2d6")
    assert result.returncode == 0
    val = int(result.stdout.decode().strip().splitlines()[0])
    assert 2 <= val <= 12


def test_int_range(cli):
    """Random int respects min/max."""
    result = cli("random", "--mode", "int", "--min", "10", "--max", "10", "--seed", "1")
    assert result.returncode == 0
    assert result.stdout.strip() == b"10"


def test_float(cli):
    """Random float produces value in [0, 1)."""
    result = cli("random", "--mode", "float", "--seed", "5")
    assert result.returncode == 0
    val = float(result.stdout.decode().strip())
    assert 0.0 <= val < 1.0
