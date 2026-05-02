"""Tests for the jwt subcommand."""

import base64
import json

import pytest


def _make_jwt(header: dict, payload: dict) -> str:
    """Create a test JWT token."""
    def _b64url(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    return f"{_b64url(header)}.{_b64url(payload)}.fakesignature"


def test_decode_payload(cli):
    """Decode JWT shows payload content."""
    token = _make_jwt({"alg": "HS256"}, {"sub": "user123", "role": "admin"})
    result = cli("jwt", token)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "user123" in output
    assert "admin" in output


def test_decode_header(cli):
    """Decode JWT with --part header shows algorithm."""
    token = _make_jwt({"alg": "RS256", "typ": "JWT"}, {"sub": "test"})
    result = cli("jwt", "--part", "header", token)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "RS256" in output


def test_decode_all(cli):
    """Decode JWT with --part all shows both header and payload."""
    token = _make_jwt({"alg": "HS256"}, {"sub": "test"})
    result = cli("jwt", "--part", "all", token)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Header" in output
    assert "Payload" in output


def test_malformed_token(cli):
    """Malformed token without dots produces an error."""
    result = cli("jwt", "notavalidtoken")
    assert result.returncode == 1
    assert b"error" in result.stderr.lower()


def test_stdin_input(cli):
    """JWT from stdin works."""
    token = _make_jwt({"alg": "HS256"}, {"data": "fromstdin"})
    result = cli("jwt", input_data=token)
    assert result.returncode == 0
    assert b"fromstdin" in result.stdout


def test_expired_token(cli):
    """Token with past exp shows 'expired'."""
    token = _make_jwt({"alg": "HS256"}, {"sub": "test", "exp": 1000000000})
    result = cli("jwt", "--part", "all", token)
    assert result.returncode == 0
    assert b"expired" in result.stdout.lower()


def test_raw_output(cli):
    """Raw mode outputs compact JSON."""
    token = _make_jwt({"alg": "HS256"}, {"sub": "test"})
    result = cli("jwt", "--raw", token)
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    parsed = json.loads(output)
    assert parsed["sub"] == "test"
