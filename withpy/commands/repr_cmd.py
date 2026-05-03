"""Format data as Python repr or pprint output.

Uses pprint and copy to format JSON data as Python literals,
with options for width control and deep copying. Useful for
generating Python code from JSON data.
"""

import argparse
import copy
import json
import pprint
import sys

from withpy.commands.shared import read_input_text


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the repr subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("repr", help="Format JSON data as Python repr/pprint")
    p.add_argument("--mode", "-m", default="pprint", choices=["pprint", "repr", "literal", "depth"], help="Output mode (default: pprint)")
    p.add_argument("--width", "-w", type=int, default=80, help="Line width for pprint (default: 80)")
    p.add_argument("--max-depth", type=int, default=None, help="Maximum nesting depth to display")
    p.add_argument("--compact", action="store_true", help="Compact output for pprint")
    p.add_argument("input", nargs="?", default=None, help="JSON file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the repr subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    text = read_input_text(args.input)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 1
    data = copy.deepcopy(data)
    match args.mode:
        case "pprint":
            pprint.pprint(data, width=args.width, depth=args.max_depth, compact=args.compact)
        case "repr":
            print(repr(data))
        case "literal":
            output = pprint.pformat(data, width=args.width, depth=args.max_depth, compact=args.compact)
            print(output)
        case "depth":
            depth = _measure_depth(data)
            print(f"max_depth: {depth}")
            print(f"top_type: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"top_keys: {len(data)}")
            elif isinstance(data, list):
                print(f"top_items: {len(data)}")
    return 0


def _measure_depth(obj: object, current: int = 0) -> int:
    """Measure the maximum nesting depth of a data structure.

    Args:
        obj: Data structure to measure.
        current: Current depth level.

    Returns:
        Maximum depth.
    """
    if isinstance(obj, dict):
        if not obj:
            return current + 1
        return max(_measure_depth(v, current + 1) for v in obj.values())
    if isinstance(obj, list):
        if not obj:
            return current + 1
        return max(_measure_depth(v, current + 1) for v in obj)
    return current
