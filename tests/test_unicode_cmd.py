"""Tests for the unicode subcommand."""

import pytest


def test_lookup_codepoint(cli):
    """Lookup U+0041 returns LATIN CAPITAL LETTER A."""
    result = cli("unicode", "--mode", "lookup", "U+0041")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "LATIN CAPITAL LETTER A" in output
    assert "U+0041" in output


def test_lookup_character(cli):
    """Lookup a literal character shows its info."""
    result = cli("unicode", "--mode", "lookup", "A")
    assert result.returncode == 0
    assert "LATIN CAPITAL LETTER A" in result.stdout.decode()


def test_name_search(cli):
    """Name search finds characters by name substring."""
    result = cli("unicode", "--mode", "name", "SNOWMAN")
    assert result.returncode == 0
    assert "2603" in result.stdout.decode()


def test_stats_mode(cli):
    """Stats mode counts character categories."""
    result = cli("unicode", "--mode", "stats", "Hello!")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Ll" in output or "Lowercase" in output
    assert "Lu" in output or "Uppercase" in output


def test_normalize(cli):
    """Normalize mode applies NFC normalization."""
    result = cli("unicode", "--mode", "normalize", "--form", "NFC", "é")
    assert result.returncode == 0


def test_invalid_codepoint(cli):
    """Invalid codepoint produces error."""
    result = cli("unicode", "--mode", "lookup", "U+ZZZZ")
    assert result.returncode == 1


def test_lookup_by_name(cli):
    """Lookup by character name works."""
    result = cli("unicode", "--mode", "lookup", "LATIN SMALL LETTER A")
    assert result.returncode == 0
    assert "U+0061" in result.stdout.decode()
