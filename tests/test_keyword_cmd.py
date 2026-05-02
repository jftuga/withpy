"""Tests for the keyword subcommand."""

import pytest


def test_check_keyword(cli):
    """Keyword check identifies Python keywords."""
    result = cli("keyword", "--mode", "check", "if", "for", "hello")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "if: keyword" in output
    assert "for: keyword" in output
    assert "hello: not a keyword" in output


def test_check_soft_keyword(cli):
    """Keyword check identifies soft keywords."""
    result = cli("keyword", "--mode", "check", "match", "case")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "soft keyword" in output


def test_list(cli):
    """Keyword list shows all keywords."""
    result = cli("keyword", "--mode", "list")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "if" in output
    assert "while" in output
    assert "Total:" in output


def test_filter(cli):
    """Keyword filter extracts only keywords."""
    result = cli("keyword", "--mode", "filter", "hello", "if", "world", "for", "match")
    assert result.returncode == 0
    lines = result.stdout.decode().splitlines()
    assert "if" in lines
    assert "for" in lines
    assert "hello" not in lines
