"""SQLite database operations: query, import CSV, export, schema inspection.

Provides modes for executing SQL queries against SQLite databases,
importing CSV files as tables, exporting table contents, and inspecting
database schemas. Supports in-memory databases for ad-hoc CSV querying.
"""

import argparse
import csv
import io
import json
import sqlite3
import sys

from withpy.commands.shared import read_input_text


def _format_table(headers: list[str], rows: list[tuple]) -> str:
    """Format query results as an aligned text table.

    Args:
        headers: Column names.
        rows: Row data tuples.

    Returns:
        Formatted table string.
    """
    if not rows:
        return "(no rows)"
    widths = [len(h) for h in headers]
    str_rows = [[str(v) if v is not None else "NULL" for v in row] for row in rows]
    for row in str_rows:
        for i, val in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(val))
    lines: list[str] = []
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("  ".join("-" * w for w in widths))
    for row in str_rows:
        lines.append("  ".join(val.ljust(widths[i]) if i < len(widths) else val for i, val in enumerate(row)))
    return "\n".join(lines)


def _format_csv_output(headers: list[str], rows: list[tuple]) -> str:
    """Format query results as CSV.

    Args:
        headers: Column names.
        rows: Row data tuples.

    Returns:
        CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def _format_json_output(headers: list[str], rows: list[tuple]) -> str:
    """Format query results as JSON.

    Args:
        headers: Column names.
        rows: Row data tuples.

    Returns:
        JSON string.
    """
    records = [dict(zip(headers, row)) for row in rows]
    return json.dumps(records, indent=2, default=str)


def _import_csv(conn: sqlite3.Connection, csv_text: str, table: str, has_header: bool) -> int:
    """Import CSV data into a SQLite table.

    Args:
        conn: SQLite connection.
        csv_text: CSV content.
        table: Target table name.
        has_header: Whether CSV has a header row.

    Returns:
        Number of rows imported.
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return 0
    if has_header:
        headers = rows[0]
        data_rows = rows[1:]
    else:
        headers = [f"col{i}" for i in range(len(rows[0]))]
        data_rows = rows
    cols = ", ".join(f'"{h}" TEXT' for h in headers)
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols})')
    placeholders = ", ".join("?" * len(headers))
    conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', data_rows)
    conn.commit()
    return len(data_rows)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the db subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("db", help="SQLite queries on .db or CSV-as-table")
    p.add_argument("--mode", "-m", default="query", choices=["query", "import", "schema", "tables", "export"], help="Operation mode (default: query)")
    p.add_argument("--db", "-d", default=":memory:", help="SQLite database file (default: :memory:)")
    p.add_argument("--table", "-t", default="data", help="Table name for import/export (default: data)")
    p.add_argument("--csv", default=None, help="CSV file to import as table")
    p.add_argument("--format", "-f", default="table", choices=["table", "csv", "json"], help="Output format (default: table)")
    p.add_argument("--header", action="store_true", help="CSV has header row")
    p.add_argument("sql", nargs="?", default=None, help="SQL query to execute")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the db subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        conn = sqlite3.connect(args.db)
        if args.csv:
            csv_text = read_input_text(args.csv if args.csv != "-" else None)
            count = _import_csv(conn, csv_text, args.table, args.header)
            if args.mode == "import":
                print(f"imported {count} rows into '{args.table}'")
                conn.close()
                return 0
        match args.mode:
            case "query":
                if not args.sql:
                    print("error: SQL query required", file=sys.stderr)
                    conn.close()
                    return 1
                cursor = conn.execute(args.sql)
                if cursor.description:
                    headers = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    match args.format:
                        case "table":
                            print(_format_table(headers, rows))
                        case "csv":
                            sys.stdout.write(_format_csv_output(headers, rows))
                        case "json":
                            print(_format_json_output(headers, rows))
                else:
                    conn.commit()
                    print(f"({conn.total_changes} rows affected)")
            case "import":
                if not args.csv:
                    print("error: --csv required for import mode", file=sys.stderr)
                    conn.close()
                    return 1
            case "schema":
                cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
                for row in cursor:
                    if row[0]:
                        print(row[0] + ";")
            case "tables":
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                for row in cursor:
                    print(row[0])
            case "export":
                cursor = conn.execute(f'SELECT * FROM "{args.table}"')
                headers = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                match args.format:
                    case "table":
                        print(_format_table(headers, rows))
                    case "csv":
                        sys.stdout.write(_format_csv_output(headers, rows))
                    case "json":
                        print(_format_json_output(headers, rows))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                conn.close()
                return 1
        conn.close()
        return 0
    except (sqlite3.Error, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
