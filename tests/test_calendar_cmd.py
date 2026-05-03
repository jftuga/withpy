"""Tests for the calendar subcommand."""

import pytest


def test_weekday_known(cli):
    """2024-01-01 is Monday."""
    result = cli("calendar", "--mode", "weekday", "2024-01-01")
    assert result.returncode == 0
    assert "Monday" in result.stdout.decode()


def test_easter_2024(cli):
    """Easter 2024 is March 31."""
    result = cli("calendar", "--mode", "easter", "--year", "2024")
    assert result.returncode == 0
    assert "2024-03-31" in result.stdout.decode()


def test_iso_week(cli):
    """ISO week for 2024-01-01 is week 1."""
    result = cli("calendar", "--mode", "weeks", "2024-01-01")
    assert result.returncode == 0
    assert "week 1" in result.stdout.decode()


def test_add_days(cli):
    """Adding 7 days to Jan 28 gives Feb 4."""
    result = cli("calendar", "--mode", "add", "--days", "7", "2024-01-28")
    assert result.returncode == 0
    assert "2024-02-04" in result.stdout.decode()


def test_add_weeks(cli):
    """Adding 2 weeks to Jan 1 gives Jan 15."""
    result = cli("calendar", "--mode", "add", "--weeks", "2", "2024-01-01")
    assert result.returncode == 0
    assert "2024-01-15" in result.stdout.decode()


def test_month_display(cli):
    """Month mode shows ASCII calendar."""
    result = cli("calendar", "--mode", "month", "--year", "2024", "--month", "1")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "January" in output
    assert "2024" in output


def test_year_display(cli):
    """Year mode shows all 12 months."""
    result = cli("calendar", "--mode", "year", "--year", "2024")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "January" in output
    assert "December" in output


def test_invalid_date(cli):
    """Invalid date format produces error."""
    result = cli("calendar", "--mode", "weekday", "not-a-date")
    assert result.returncode == 1
