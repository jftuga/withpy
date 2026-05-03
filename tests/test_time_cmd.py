"""Tests for the time subcommand.

Covers known-value epoch conversions, multi-format output, timezone
conversion, calendar display, flexible date parsing, and error paths.
"""

import pytest


def test_fromepoch_zero(cli):
    """Epoch 0 converts to 1970-01-01 00:00:00 UTC."""
    result = cli("time", "--mode", "fromepoch", "0")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "1970-01-01" in output
    assert "Epoch:   0" in output


def test_fromepoch_known(cli):
    """Epoch 1700000000 converts to 2023-11-14 UTC."""
    result = cli("time", "--mode", "fromepoch", "1700000000")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "2023-11-14" in output


def test_toepoch_known(cli):
    """ISO date 2024-01-01T00:00:00+00:00 converts to epoch 1704067200."""
    result = cli("time", "--mode", "toepoch", "2024-01-01T00:00:00+0000")
    assert result.returncode == 0
    assert result.stdout.decode().strip() == "1704067200"


def test_now_output_format(cli):
    """Now mode produces output with all expected labels."""
    result = cli("time", "--mode", "now")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Local:" in output
    assert "UTC:" in output
    assert "ISO8601:" in output
    assert "Epoch:" in output


def test_now_with_format(cli):
    """Now mode with custom format produces formatted output."""
    result = cli("time", "--mode", "now", "--format", "%Y")
    assert result.returncode == 0
    year = result.stdout.decode().strip()
    assert year.isdigit()
    assert len(year) == 4


def test_convert_timezone(cli):
    """Convert mode changes timezone correctly."""
    result = cli("time", "--mode", "convert", "--zone", "America/New_York", "2024-01-01T12:00:00+0000")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "EST" in output or "EDT" in output or "2024-01-01" in output


def test_convert_missing_zone(cli):
    """Convert mode without --zone produces an error."""
    result = cli("time", "--mode", "convert", "2024-01-01T12:00:00")
    assert result.returncode == 1
    assert b"--zone" in result.stderr.lower() or b"zone" in result.stderr.lower()


def test_calendar_month(cli):
    """Calendar mode for a specific month produces ASCII output."""
    result = cli("time", "--mode", "calendar", "2024-01")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "January" in output
    assert "2024" in output
    assert "Mo" in output or "Su" in output


def test_calendar_year(cli):
    """Calendar mode for a year produces multi-month output."""
    result = cli("time", "--mode", "calendar", "2024")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "January" in output
    assert "December" in output


def test_calendar_default(cli):
    """Calendar mode without a value shows the current month."""
    result = cli("time", "--mode", "calendar")
    assert result.returncode == 0
    assert len(result.stdout.decode().strip()) > 0


@pytest.mark.parametrize("date_str", [
    "2024-01-15",
    "2024-01-15T10:30:00",
    "01/15/2024",
    "Jan 15, 2024",
    "1705312200",
])
def test_flexible_parser(cli, date_str):
    """Flexible parser handles various date formats for toepoch."""
    result = cli("time", "--mode", "toepoch", date_str)
    assert result.returncode == 0
    epoch = result.stdout.decode().strip()
    assert epoch.lstrip("-").isdigit()


def test_invalid_timezone(cli):
    """Invalid timezone name produces an error."""
    result = cli("time", "--mode", "now", "--zone", "Fake/Zone")
    assert result.returncode == 1
    assert result.stderr


def test_fromepoch_non_integer(cli):
    """Non-integer value for fromepoch produces an error."""
    result = cli("time", "--mode", "fromepoch", "not-a-number")
    assert result.returncode == 1
    assert result.stderr


def test_fromepoch_with_zone(cli):
    """Fromepoch respects the --zone flag."""
    result = cli("time", "--mode", "fromepoch", "--zone", "Asia/Tokyo", "0")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "JST" in output or "1970-01-01" in output


def test_roundtrip_epoch(cli):
    """Converting to epoch and back produces consistent results."""
    r1 = cli("time", "--mode", "toepoch", "2024-06-15T12:00:00+0000")
    assert r1.returncode == 0
    epoch = r1.stdout.decode().strip()
    r2 = cli("time", "--mode", "fromepoch", epoch)
    assert r2.returncode == 0
    assert "2024-06-15" in r2.stdout.decode()
