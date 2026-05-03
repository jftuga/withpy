"""Tests for the encode and decode subcommands.

Covers round-trip encoding/decoding for all supported formats, known-value
checks, and error paths for invalid input and unknown formats.
"""

import pytest


_FORMATS = ["base64", "base32", "hex", "ascii85", "url", "html", "quopri"]


@pytest.mark.parametrize("fmt", _FORMATS)
def test_roundtrip(cli, fmt):
    """Encoding then decoding produces the original input."""
    original = b"Hello, World! 123 ~!@#"
    enc = cli("encode", "--format", fmt, input_data=original)
    assert enc.returncode == 0
    dec = cli("decode", "--format", fmt, input_data=enc.stdout.strip())
    assert dec.returncode == 0
    assert dec.stdout.strip() == original


def test_roundtrip_utf16(cli):
    """UTF-16 encode/decode round-trips correctly."""
    original = b"Hello UTF-16"
    enc = cli("encode", "--format", "utf16", input_data=original)
    assert enc.returncode == 0
    dec = cli("decode", "--format", "utf16", input_data=enc.stdout.rstrip(b"\n"))
    assert dec.returncode == 0
    assert dec.stdout.strip() == original


def test_hex_known_value(cli):
    """Hex encoding of 'Hello' produces the known hex string."""
    result = cli("encode", "--format", "hex", input_data=b"Hello")
    assert result.returncode == 0
    assert result.stdout.strip() == b"48656c6c6f"


def test_base64_known_value(cli):
    """Base64 encoding of 'Hello, World!' produces the known string."""
    result = cli("encode", "--format", "base64", input_data=b"Hello, World!")
    assert result.returncode == 0
    assert result.stdout.strip() == b"SGVsbG8sIFdvcmxkIQ=="


def test_html_known_value(cli):
    """HTML encoding of '<div>' produces entity-escaped output."""
    result = cli("encode", "--format", "html", input_data=b"<div>")
    assert result.returncode == 0
    assert result.stdout.strip() == b"&lt;div&gt;"


def test_url_known_value(cli):
    """URL encoding of 'hello world' produces plus-encoded output."""
    result = cli("encode", "--format", "url", input_data=b"hello world")
    assert result.returncode == 0
    assert result.stdout.strip() == b"hello+world"


def test_base32_known_value(cli):
    """Base32 encoding of 'Hello' produces the known string."""
    result = cli("encode", "--format", "base32", input_data=b"Hello")
    assert result.returncode == 0
    assert result.stdout.strip() == b"JBSWY3DP"


def test_quopri_roundtrip_unicode(cli):
    """Quoted-printable handles non-ASCII bytes correctly."""
    original = "café".encode("utf-8")
    enc = cli("encode", "--format", "quopri", input_data=original)
    assert enc.returncode == 0
    dec = cli("decode", "--format", "quopri", input_data=enc.stdout.strip())
    assert dec.returncode == 0
    assert dec.stdout.strip() == original


def test_encode_from_file(cli, tmp_file):
    """Encoding reads from a file argument."""
    f = tmp_file("Hello")
    result = cli("encode", "--format", "hex", str(f))
    assert result.returncode == 0
    assert b"48656c6c6f" in result.stdout


def test_invalid_hex_decode(cli):
    """Decoding invalid hex produces an error."""
    result = cli("decode", "--format", "hex", input_data=b"ZZZZ")
    assert result.returncode == 1
    assert result.stderr


def test_invalid_base64_decode(cli):
    """Decoding invalid base64 produces an error."""
    result = cli("decode", "--format", "base64", input_data=b"!!!not-base64!!!")
    assert result.returncode == 1
    assert result.stderr
