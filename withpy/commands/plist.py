"""Read, write, and convert Apple plist files.

Supports parsing plist XML and binary formats, converting to/from JSON,
validation, and key listing. Handles special plist types (datetime, bytes)
by converting them to JSON-compatible representations.
"""

import argparse
import base64
import datetime
import json
import plistlib
import sys

from withpy.commands.shared import read_input


def _plist_to_jsonable(obj: object) -> object:
    """Convert plist-native types to JSON-serializable equivalents.

    Args:
        obj: A plist value (possibly containing datetime or bytes).

    Returns:
        JSON-serializable equivalent.
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode()
    if isinstance(obj, dict):
        return {k: _plist_to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_plist_to_jsonable(item) for item in obj]
    return obj


def _json_to_plistable(obj: object) -> object:
    """Convert JSON values back to plist-native types where possible.

    Args:
        obj: A JSON-deserialized value.

    Returns:
        Value suitable for plistlib serialization.
    """
    if isinstance(obj, dict):
        return {k: _json_to_plistable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_to_plistable(item) for item in obj]
    return obj


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the plist subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("plist", help="Read/write/convert Apple plist files")
    p.add_argument("--mode", "-m", default="tojson", choices=["tojson", "fromjson", "validate", "keys"], help="Operation mode (default: tojson)")
    p.add_argument("--format", "-f", default="xml", choices=["xml", "binary"], help="Output plist format (default: xml)")
    p.add_argument("--output", "-o", default=None, help="Output file (default: stdout)")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the plist subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        raw = read_input(args.input)
        match args.mode:
            case "tojson":
                data = plistlib.loads(raw)
                jsonable = _plist_to_jsonable(data)
                output = json.dumps(jsonable, indent=2, ensure_ascii=False)
                print(output)
            case "fromjson":
                json_data = json.loads(raw.decode())
                plist_data = _json_to_plistable(json_data)
                fmt = plistlib.FMT_BINARY if args.format == "binary" else plistlib.FMT_XML
                result = plistlib.dumps(plist_data, fmt=fmt)
                if args.output:
                    with open(args.output, "wb") as f:
                        f.write(result)
                else:
                    sys.stdout.buffer.write(result)
            case "validate":
                plistlib.loads(raw)
                print("valid")
            case "keys":
                data = plistlib.loads(raw)
                if not isinstance(data, dict):
                    print("error: top-level plist value is not a dictionary", file=sys.stderr)
                    return 1
                for key in data:
                    print(key)
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (plistlib.InvalidFileException, json.JSONDecodeError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
