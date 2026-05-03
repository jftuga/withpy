"""CSV processing: JSON conversion, column selection, row filtering.

Provides modes for converting between CSV and JSON formats, selecting
specific columns, filtering rows by value or regex, displaying head
rows, and computing basic statistics about CSV structure.
"""

import argparse
import csv
import io
import json
import re
import sys

from withpy.commands.shared import read_input_text


def _csv_to_json(text: str, delimiter: str, no_header: bool) -> str:
    """Convert CSV text to JSON.

    Args:
        text: CSV content.
        delimiter: Column delimiter character.
        no_header: If True, output arrays instead of objects.

    Returns:
        JSON string.
    """
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return "[]"
    if no_header:
        return json.dumps(rows, indent=2)
    headers = rows[0]
    records = [dict(zip(headers, row)) for row in rows[1:]]
    return json.dumps(records, indent=2)


def _json_to_csv(text: str, delimiter: str) -> str:
    """Convert JSON array of objects to CSV.

    Args:
        text: JSON content (array of objects).
        delimiter: Column delimiter.

    Returns:
        CSV string.

    Raises:
        ValueError: If JSON is not an array of objects.
    """
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("JSON input must be an array")
    if not data:
        return ""
    if not isinstance(data[0], dict):
        raise ValueError("JSON array elements must be objects")
    headers = list(data[0].keys())
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerow(headers)
    for record in data:
        writer.writerow(record.get(h, "") for h in headers)
    return output.getvalue()


def _select_columns(text: str, columns: str, delimiter: str, no_header: bool) -> str:
    """Select specific columns from CSV.

    Args:
        text: CSV content.
        columns: Comma-separated column names or indices.
        delimiter: Column delimiter.
        no_header: If True, use numeric indices.

    Returns:
        CSV with selected columns only.
    """
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return ""
    if no_header:
        indices = [int(c.strip()) for c in columns.split(",")]
    else:
        headers = rows[0]
        col_names = [c.strip() for c in columns.split(",")]
        indices = []
        for name in col_names:
            if name.isdigit():
                indices.append(int(name))
            elif name in headers:
                indices.append(headers.index(name))
            else:
                raise ValueError(f"column not found: {name}")
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    for row in rows:
        writer.writerow(row[i] for i in indices if i < len(row))
    return output.getvalue()


def _filter_rows(text: str, where: str, delimiter: str, no_header: bool) -> str:
    """Filter CSV rows by a condition.

    Args:
        text: CSV content.
        where: Filter expression (column=value or column~regex).
        delimiter: Column delimiter.
        no_header: If True, use numeric column indices.

    Returns:
        Filtered CSV content.

    Raises:
        ValueError: If filter expression is invalid.
    """
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return ""
    if "~" in where:
        col_ref, pattern = where.split("~", 1)
    elif "=" in where:
        col_ref, pattern = where.split("=", 1)
    else:
        raise ValueError(f"invalid filter: {where} (use column=value or column~regex)")
    is_regex = "~" in where
    col_ref = col_ref.strip()
    if no_header:
        col_idx = int(col_ref)
        start = 0
    else:
        headers = rows[0]
        if col_ref.isdigit():
            col_idx = int(col_ref)
        elif col_ref in headers:
            col_idx = headers.index(col_ref)
        else:
            raise ValueError(f"column not found: {col_ref}")
        start = 1
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    if not no_header:
        writer.writerow(rows[0])
    for row in rows[start:]:
        if col_idx >= len(row):
            continue
        val = row[col_idx]
        if is_regex:
            if re.search(pattern, val):
                writer.writerow(row)
        else:
            if val == pattern:
                writer.writerow(row)
    return output.getvalue()


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the csv subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("csv", help="CSV/JSON conversion, filter, select columns")
    p.add_argument("--mode", "-m", default="tojson", choices=["tojson", "fromjson", "select", "filter", "head", "count", "stats"], help="Operation mode (default: tojson)")
    p.add_argument("--columns", "-c", default=None, help="Comma-separated column names or indices")
    p.add_argument("--where", default=None, help="Filter: column=value or column~regex")
    p.add_argument("--delimiter", "-d", default=",", help="CSV delimiter (default: comma)")
    p.add_argument("--no-header", action="store_true", help="CSV has no header row")
    p.add_argument("--count", "-n", type=int, default=10, help="Number of rows for head mode (default: 10)")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the csv subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        text = read_input_text(args.input)
        match args.mode:
            case "tojson":
                print(_csv_to_json(text, args.delimiter, args.no_header))
            case "fromjson":
                result = _json_to_csv(text, args.delimiter)
                sys.stdout.write(result)
            case "select":
                if not args.columns:
                    print("error: --columns required for select mode", file=sys.stderr)
                    return 1
                result = _select_columns(text, args.columns, args.delimiter, args.no_header)
                sys.stdout.write(result)
            case "filter":
                if not args.where:
                    print("error: --where required for filter mode", file=sys.stderr)
                    return 1
                result = _filter_rows(text, args.where, args.delimiter, args.no_header)
                sys.stdout.write(result)
            case "head":
                reader = csv.reader(io.StringIO(text), delimiter=args.delimiter)
                output = io.StringIO()
                writer = csv.writer(output, delimiter=args.delimiter, lineterminator="\n")
                for i, row in enumerate(reader):
                    if i >= args.count + (0 if args.no_header else 1):
                        break
                    writer.writerow(row)
                sys.stdout.write(output.getvalue())
            case "count":
                reader = csv.reader(io.StringIO(text), delimiter=args.delimiter)
                rows = list(reader)
                count = len(rows) - (0 if args.no_header else 1)
                print(count)
            case "stats":
                reader = csv.reader(io.StringIO(text), delimiter=args.delimiter)
                rows = list(reader)
                if not rows:
                    print("empty CSV")
                    return 0
                num_cols = len(rows[0])
                num_rows = len(rows) - (0 if args.no_header else 1)
                print(f"columns: {num_cols}")
                print(f"rows:    {num_rows}")
                if not args.no_header:
                    print(f"headers: {', '.join(rows[0])}")
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, csv.Error, json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
