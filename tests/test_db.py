"""Tests for the db subcommand."""

import csv
import io
from pathlib import Path

from tests.conftest import CliRunner


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


def test_csv_query(cli: CliRunner) -> None:
    """CSV query output preserves headers, quoting, numbers, and NULLs."""
    result = cli("db", "--format", "csv", "SELECT 1 AS value, 'hello, world' AS text, NULL AS empty")
    assert result.returncode == 0, result.stderr.decode()
    assert list(csv.reader(io.StringIO(result.stdout.decode()))) == [
        ["value", "text", "empty"], ["1", "hello, world", ""],
    ]


def test_csv_export(cli: CliRunner, tmp_path: Path) -> None:
    """CSV export preserves imported rows and quoted fields."""
    source = tmp_path / "data.csv"
    source.write_text('name,value\n"hello, world",42\n', encoding="utf-8")
    result = cli("db", "--csv", str(source), "--header", "--mode", "export", "--format", "csv")
    assert result.returncode == 0, result.stderr.decode()
    assert list(csv.reader(io.StringIO(result.stdout.decode()))) == [
        ["name", "value"], ["hello, world", "42"],
    ]


def test_csv_windows_newlines() -> None:
    """Windows stdout translation must not introduce empty CSV records."""
    from withpy.commands.db import _db_format_csv_output

    output = io.BytesIO()
    with io.TextIOWrapper(output, encoding="utf-8", newline="\r\n") as stdout:
        stdout.write(_db_format_csv_output(["value", "text"], [(1, 'hello, "world"')]))
        stdout.flush()
        assert output.getvalue() == b'value,text\r\n1,"hello, ""world"""\r\n'
