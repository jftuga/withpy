"""Read, write, and query INI/configuration files.

Uses configparser to parse INI-style configuration files, extract
values, list sections, and convert between INI and JSON formats.
"""

import argparse
import configparser
import json
import sys

from withpy.commands.shared import read_input_text


def _read_config(text: str) -> configparser.ConfigParser:
    """Parse INI text into a ConfigParser object.

    Args:
        text: INI-format text.

    Returns:
        Parsed ConfigParser instance.

    Raises:
        configparser.Error: If the text is malformed.
    """
    cp = configparser.ConfigParser()
    cp.read_string(text)
    return cp


def _config_to_dict(cp: configparser.ConfigParser) -> dict[str, dict[str, str]]:
    """Convert a ConfigParser to a nested dictionary.

    Args:
        cp: ConfigParser instance.

    Returns:
        Nested dict of section -> key -> value.
    """
    result: dict[str, dict[str, str]] = {}
    for section in cp.sections():
        result[section] = dict(cp[section])
    if cp.defaults():
        result["DEFAULT"] = dict(cp.defaults())
    return result


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the config subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("config", help="Read/write/query INI config files")
    p.add_argument("--mode", "-m", default="get", choices=["get", "sections", "keys", "tojson", "validate"], help="Operation mode (default: get)")
    p.add_argument("--section", "-s", default=None, help="Section name for get/keys mode")
    p.add_argument("--key", "-k", default=None, help="Key name for get mode")
    p.add_argument("input", nargs="?", default=None, help="INI file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the config subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        text = read_input_text(args.input)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        cp = _read_config(text)
    except configparser.Error as e:
        if args.mode == "validate":
            print(f"invalid: {e}", file=sys.stderr)
            return 1
        print(f"error: {e}", file=sys.stderr)
        return 1
    match args.mode:
        case "validate":
            print("valid")
            return 0
        case "sections":
            for section in cp.sections():
                print(section)
            return 0
        case "keys":
            if not args.section:
                print("error: --section required for keys mode", file=sys.stderr)
                return 1
            if not cp.has_section(args.section):
                print(f"error: section not found: {args.section}", file=sys.stderr)
                return 1
            for key in cp[args.section]:
                print(key)
            return 0
        case "get":
            if not args.section:
                print("error: --section required for get mode", file=sys.stderr)
                return 1
            if not cp.has_section(args.section):
                print(f"error: section not found: {args.section}", file=sys.stderr)
                return 1
            if args.key:
                if not cp.has_option(args.section, args.key):
                    print(f"error: key not found: {args.key}", file=sys.stderr)
                    return 1
                print(cp.get(args.section, args.key))
            else:
                for key, val in cp[args.section].items():
                    print(f"{key} = {val}")
            return 0
        case "tojson":
            data = _config_to_dict(cp)
            print(json.dumps(data, indent=2))
            return 0
    return 0
