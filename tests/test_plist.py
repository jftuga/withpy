"""Tests for the plist subcommand."""

import pytest


_SAMPLE_PLIST = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Name</key>
    <string>Test App</string>
    <key>Version</key>
    <integer>42</integer>
    <key>Enabled</key>
    <true/>
</dict>
</plist>"""


def test_tojson(cli):
    """Convert plist to JSON."""
    result = cli("plist", "--mode", "tojson", input_data=_SAMPLE_PLIST)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Test App" in output
    assert "42" in output


def test_keys(cli):
    """Keys mode lists top-level keys."""
    result = cli("plist", "--mode", "keys", input_data=_SAMPLE_PLIST)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Name" in output
    assert "Version" in output
    assert "Enabled" in output


def test_validate_valid(cli):
    """Valid plist passes validation."""
    result = cli("plist", "--mode", "validate", input_data=_SAMPLE_PLIST)
    assert result.returncode == 0
    assert b"valid" in result.stdout.lower()


def test_validate_invalid(cli):
    """Invalid plist fails validation."""
    result = cli("plist", "--mode", "validate", input_data=b"not a plist")
    assert result.returncode == 1


def test_fromjson_roundtrip(cli):
    """JSON to plist to JSON roundtrip preserves data."""
    json_data = b'{"key": "value", "number": 123}'
    to_plist = cli("plist", "--mode", "fromjson", input_data=json_data)
    assert to_plist.returncode == 0
    back = cli("plist", "--mode", "tojson", input_data=to_plist.stdout)
    assert back.returncode == 0
    output = back.stdout.decode()
    assert "value" in output
    assert "123" in output
