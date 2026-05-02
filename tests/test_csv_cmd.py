"""Tests for the csv subcommand."""

import pytest


def test_tojson(cli):
    """Convert CSV with header to JSON objects."""
    csv_data = b"name,age\nalice,30\nbob,25\n"
    result = cli("csv", "--mode", "tojson", input_data=csv_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "alice" in output
    assert "30" in output


def test_fromjson(cli):
    """Convert JSON array to CSV."""
    json_data = b'[{"name":"alice","age":"30"},{"name":"bob","age":"25"}]'
    result = cli("csv", "--mode", "fromjson", input_data=json_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "name" in output
    assert "alice" in output


def test_select_columns(cli):
    """Select mode picks specific columns."""
    csv_data = b"name,age,city\nalice,30,NYC\nbob,25,LA\n"
    result = cli("csv", "--mode", "select", "--columns", "name,city", input_data=csv_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "alice" in output
    assert "NYC" in output
    assert "30" not in output


def test_filter_equals(cli):
    """Filter mode with = operator."""
    csv_data = b"name,age\nalice,30\nbob,25\ncarol,30\n"
    result = cli("csv", "--mode", "filter", "--where", "age=30", input_data=csv_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "alice" in output
    assert "carol" in output
    assert "bob" not in output


def test_filter_regex(cli):
    """Filter mode with ~ regex operator."""
    csv_data = b"name,email\nalice,alice@example.com\nbob,bob@test.org\n"
    result = cli("csv", "--mode", "filter", "--where", "email~example", input_data=csv_data)
    assert result.returncode == 0
    assert b"alice" in result.stdout
    assert b"bob" not in result.stdout


def test_head(cli):
    """Head mode shows first N rows."""
    csv_data = b"n\n1\n2\n3\n4\n5\n"
    result = cli("csv", "--mode", "head", "--count", "3", input_data=csv_data)
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 4  # header + 3 rows


def test_count(cli):
    """Count mode reports row count."""
    csv_data = b"x\n1\n2\n3\n"
    result = cli("csv", "--mode", "count", input_data=csv_data)
    assert result.returncode == 0
    assert "3" in result.stdout.decode()


def test_stats(cli):
    """Stats mode shows column and row counts."""
    csv_data = b"a,b,c\n1,2,3\n4,5,6\n"
    result = cli("csv", "--mode", "stats", input_data=csv_data)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "3" in output
    assert "2" in output
