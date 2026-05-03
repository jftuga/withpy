"""Split and quote shell commands safely.

Uses the shlex module to parse shell command strings into tokens
and to properly quote strings for safe shell usage.
"""

import argparse
import shlex
import sys

from withpy.commands.shared import read_input_text


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the shlex subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("shlex", help="Split/quote shell commands safely")
    p.add_argument("--mode", "-m", default="split", choices=["split", "quote", "join"], help="Operation mode (default: split)")
    p.add_argument("input", nargs="*", default=None, help="Command string(s) or words to join")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the shlex subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    match args.mode:
        case "split":
            if args.input:
                text = " ".join(args.input)
            else:
                text = read_input_text(None).strip()
            try:
                tokens = shlex.split(text)
                for token in tokens:
                    print(token)
                return 0
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "quote":
            if args.input:
                text = " ".join(args.input)
            else:
                text = read_input_text(None).strip()
            print(shlex.quote(text))
            return 0
        case "join":
            if not args.input:
                words = read_input_text(None).strip().splitlines()
            else:
                words = args.input
            print(shlex.join(words))
            return 0
    return 0
