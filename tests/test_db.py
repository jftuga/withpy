"""Tests for the db subcommand."""

import pytest


def test_query_memory(cli):
    """Query in-memory database with inline SQL."""
    result = cli("db", "--mode", "query", "SELECT 1+1 AS result")
    assert result.returncode == 0
    assert "2" in result.stdout.decode()


def test_import_and_query(cli, tmp_file):
    """Import CSV then query it."""
    csv_path = tmp_file("name,age\nalice,30\nbob,25\n", name="data.csv")
    result = cli("db", "--csv", str(csv_path), "--header", "--table", "people", "--mode", "query", "SELECT name FROM people WHERE age = '30'")
    assert result.returncode == 0
    assert "alice" in result.stdout.decode()


def test_tables(cli, tmp_file):
    """Tables mode lists imported tables."""
    csv_path = tmp_file("x,y\n1,2\n", name="t.csv")
    result = cli("db", "--csv", str(csv_path), "--header", "--table", "mytable", "--mode", "tables")
    assert result.returncode == 0
    assert "mytable" in result.stdout.decode()


def test_schema(cli, tmp_file):
    """Schema mode shows CREATE TABLE."""
    csv_path = tmp_file("col1,col2\na,b\n", name="s.csv")
    result = cli("db", "--csv", str(csv_path), "--header", "--table", "test_tbl", "--mode", "schema")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "CREATE TABLE" in output
    assert "col1" in output


def test_json_format(cli):
    """JSON output format produces valid JSON."""
    result = cli("db", "--mode", "query", "--format", "json", "SELECT 42 AS num, 'hello' AS txt")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "42" in output
    assert "hello" in output
    assert "[" in output


def test_invalid_sql(cli):
    """Invalid SQL produces error."""
    result = cli("db", "--mode", "query", "INVALID SQL GARBAGE")
    assert result.returncode == 1


def test_import_mode(cli, tmp_file):
    """Import mode reports row count."""
    csv_path = tmp_file("a,b\n1,2\n3,4\n5,6\n", name="imp.csv")
    result = cli("db", "--csv", str(csv_path), "--header", "--table", "data", "--mode", "import")
    assert result.returncode == 0
    assert "3" in result.stdout.decode()
