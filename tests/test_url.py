"""Tests for the url subcommand."""

import pytest


def test_parse_full_url(cli):
    """Parse mode decomposes a full URL."""
    result = cli("url", "--mode", "parse", "https://user:pass@example.com:8080/path?q=1#frag")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "example.com" in output
    assert "8080" in output
    assert "/path" in output


def test_parse_json_format(cli):
    """Parse mode with JSON format produces valid JSON."""
    result = cli("url", "--mode", "parse", "--format", "json", "https://example.com/path")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert '"scheme": "https"' in output
    assert '"host": "example.com"' in output


def test_encode(cli):
    """Encode mode percent-encodes a string."""
    result = cli("url", "--mode", "encode", "hello world&foo=bar")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert "hello+world" in output
    assert "%26" in output


def test_decode(cli):
    """Decode mode percent-decodes a string."""
    result = cli("url", "--mode", "decode", "hello+world%26foo%3Dbar")
    assert result.returncode == 0
    assert "hello world&foo=bar" in result.stdout.decode()


def test_build(cli):
    """Build mode constructs a URL from components."""
    result = cli("url", "--mode", "build", "--scheme", "https", "--host", "example.com", "--port", "443", "--path", "/api")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert "https" in output
    assert "example.com" in output
    assert "/api" in output


def test_params(cli):
    """Params mode extracts query parameters."""
    result = cli("url", "--mode", "params", "https://example.com?name=john&age=30")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "name=john" in output
    assert "age=30" in output


def test_encode_decode_roundtrip(cli):
    """Encode then decode produces original string."""
    original = "hello world & stuff = things"
    enc = cli("url", "--mode", "encode", original)
    assert enc.returncode == 0
    encoded = enc.stdout.decode().strip()
    dec = cli("url", "--mode", "decode", encoded)
    assert dec.returncode == 0
    assert dec.stdout.decode().strip() == original
