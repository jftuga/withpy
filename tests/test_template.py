"""Tests for the template subcommand."""

import pytest


def test_simple_substitution(cli):
    """Template renders simple variable substitution."""
    result = cli("template", "--template", "Hello $name", "--data", '{"name": "World"}')
    assert result.returncode == 0
    assert "Hello World" in result.stdout.decode()


def test_multiple_vars(cli):
    """Template renders multiple variables."""
    result = cli("template", "--template", "$greeting, $name!", "--data", '{"greeting": "Hi", "name": "Alice"}')
    assert result.returncode == 0
    assert "Hi, Alice!" in result.stdout.decode()


def test_safe_substitute_missing(cli):
    """Safe substitution leaves missing variables intact."""
    result = cli("template", "--template", "Hello $name, $missing", "--data", '{"name": "World"}')
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Hello World" in output
    assert "$missing" in output


def test_strict_missing_key(cli):
    """Strict mode fails on missing keys."""
    result = cli("template", "--template", "Hello $missing", "--data", '{"name": "World"}', "--strict")
    assert result.returncode == 1


def test_env_flag(cli):
    """Env flag includes environment variables."""
    result = cli("template", "--template", "Path: $PATH", "--env")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Path: $PATH" not in output
    assert "Path: " in output


def test_file_template(cli, tmp_file):
    """Template loaded from file via @ prefix."""
    tmpl_path = tmp_file("Hello $name\n", name="template.txt")
    result = cli("template", "--template", f"@{tmpl_path}", "--data", '{"name": "File"}')
    assert result.returncode == 0
    assert "Hello File" in result.stdout.decode()


def test_invalid_json_data(cli):
    """Invalid JSON data produces an error."""
    result = cli("template", "--template", "Hello", "--data", "not json")
    assert result.returncode == 1
