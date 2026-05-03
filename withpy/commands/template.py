"""Render string.Template templates from JSON data.

Loads a template string (or file) and substitutes variables using data
from a JSON file or environment variables. Supports both safe substitution
(leaving unknown variables intact) and strict mode (raising on missing keys).
"""

import argparse
import json
import os
import string
import sys

from withpy.commands.shared import read_input_text


def _load_template(template_arg: str) -> str:
    """Load a template from a string argument or file reference.

    Args:
        template_arg: Template string, or @filepath to load from file.

    Returns:
        The template content string.

    Raises:
        OSError: If the referenced file cannot be read.
    """
    if template_arg.startswith("@"):
        path = template_arg[1:]
        with open(path, "r") as f:
            return f.read()
    return template_arg


def _load_data(data_arg: str | None) -> dict:
    """Load JSON data from a file, stdin reference, or literal string.

    Args:
        data_arg: Path to JSON file, "@-" for stdin, or None.

    Returns:
        Parsed dictionary from JSON.

    Raises:
        ValueError: If JSON parsing fails.
        OSError: If the file cannot be read.
    """
    if data_arg is None:
        return {}
    if data_arg == "@-":
        text = sys.stdin.read()
    elif data_arg.startswith("@"):
        with open(data_arg[1:], "r") as f:
            text = f.read()
    else:
        text = data_arg
    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON data: {e}") from e
    if not isinstance(result, dict):
        raise ValueError("JSON data must be an object (dict)")
    return result


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the template subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("template", help="Render string.Template from JSON data")
    p.add_argument("--template", "-t", required=True, help="Template string or @filepath")
    p.add_argument("--data", "-d", default=None, help="JSON data: literal, @filepath, or @- for stdin")
    p.add_argument("--strict", action="store_true", help="Fail on missing keys (default: leave $var intact)")
    p.add_argument("--env", action="store_true", help="Include environment variables in data")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the template subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        tmpl_str = _load_template(args.template)
        data = _load_data(args.data)
        if args.env:
            env_data = dict(os.environ)
            env_data.update(data)
            data = env_data
        tmpl = string.Template(tmpl_str)
        if args.strict:
            result = tmpl.substitute(data)
        else:
            result = tmpl.safe_substitute(data)
        sys.stdout.write(result)
        if result and not result.endswith("\n"):
            sys.stdout.write("\n")
        return 0
    except (KeyError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
