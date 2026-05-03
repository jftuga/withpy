"""JSON pretty-printing, compaction, validation, and dot-path querying.

Provides modes for formatting JSON, validating structure, extracting
values via dot-path notation, listing keys, and reporting the top-level
JSON type.
"""

import argparse
import json
import sys

from withpy.commands.shared import query_dot_path, read_input_text


def _json_type_name(data: object) -> str:
    """Return the JSON type name of a value.

    Args:
        data: A parsed JSON value.

    Returns:
        One of: object, array, string, number, boolean, null.
    """
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "boolean"
    if isinstance(data, int | float):
        return "number"
    if isinstance(data, str):
        return "string"
    if isinstance(data, list):
        return "array"
    if isinstance(data, dict):
        return "object"
    return "unknown"


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the json subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("json", help="JSON pretty-print, compact, validate, query")
    p.add_argument("--mode", "-m", default="pretty", choices=["pretty", "compact", "validate", "query", "keys", "type"], help="Operation mode (default: pretty)")
    p.add_argument("--indent", type=int, default=2, help="Indent spaces for pretty mode (default: 2)")
    p.add_argument("--sort-keys", action="store_true", help="Sort object keys in output")
    p.add_argument("--path", "-p", default=None, help="Dot-path for query mode (e.g. 'a.b[0].c')")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the json subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    text = read_input_text(args.input)
    match args.mode:
        case "validate":
            try:
                json.loads(text)
                print("valid")
                return 0
            except json.JSONDecodeError as e:
                print(f"invalid: line {e.lineno} column {e.colno}: {e.msg}", file=sys.stderr)
                return 1
        case "pretty":
            try:
                data = json.loads(text)
                print(json.dumps(data, indent=args.indent, sort_keys=args.sort_keys, ensure_ascii=False))
                return 0
            except json.JSONDecodeError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "compact":
            try:
                data = json.loads(text)
                print(json.dumps(data, separators=(",", ":"), sort_keys=args.sort_keys, ensure_ascii=False))
                return 0
            except json.JSONDecodeError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "query":
            if not args.path:
                print("error: --path is required for query mode", file=sys.stderr)
                return 1
            try:
                data = json.loads(text)
                result = query_dot_path(data, args.path)
                if isinstance(result, (dict, list)):
                    print(json.dumps(result, indent=args.indent, ensure_ascii=False))
                else:
                    print(result)
                return 0
            except json.JSONDecodeError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            except (KeyError, IndexError, TypeError) as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "keys":
            try:
                data = json.loads(text)
                if not isinstance(data, dict):
                    print("error: top-level value is not an object", file=sys.stderr)
                    return 1
                for key in data:
                    print(key)
                return 0
            except json.JSONDecodeError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "type":
            try:
                data = json.loads(text)
                print(_json_type_name(data))
                return 0
            except json.JSONDecodeError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case _:
            print(f"error: unknown mode: {args.mode}", file=sys.stderr)
            return 1
