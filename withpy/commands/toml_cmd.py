"""Parse TOML files and convert to JSON or validate structure.

Uses the tomllib module (Python 3.11+) for parsing. Since tomllib is
read-only, this module only supports TOML-to-JSON conversion, validation,
and dot-path querying.
"""

import argparse
import json
import sys
import tomllib

from withpy.commands.shared import query_dot_path, read_input


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the toml subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("toml", help="Parse TOML and output as JSON")
    p.add_argument("--mode", "-m", default="tojson", choices=["tojson", "validate", "query"], help="Operation mode (default: tojson)")
    p.add_argument("--path", "-p", default=None, help="Dot-path to extract (query mode)")
    p.add_argument("--indent", type=int, default=2, help="JSON indent spaces (default: 2)")
    p.add_argument("input", nargs="?", default=None, help="TOML file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the toml subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        raw = read_input(args.input)
        data = tomllib.loads(raw.decode())
    except tomllib.TOMLDecodeError as e:
        print(f"error: invalid TOML: {e}", file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    match args.mode:
        case "tojson":
            print(json.dumps(data, indent=args.indent, default=str))
            return 0
        case "validate":
            print("valid")
            return 0
        case "query":
            if not args.path:
                print("error: --path is required for query mode", file=sys.stderr)
                return 1
            try:
                result = query_dot_path(data, args.path)
                if isinstance(result, (dict, list)):
                    print(json.dumps(result, indent=args.indent, default=str))
                else:
                    print(result)
                return 0
            except (KeyError, TypeError) as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case _:
            print(f"error: unknown mode: {args.mode}", file=sys.stderr)
            return 1
