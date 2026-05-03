"""Sort and rank lines using various algorithms and keys.

Uses heapq for top-N/bottom-N extraction, bisect for ranked insertion,
and standard sorting with multiple key functions for flexible line
ordering.
"""

import argparse
import bisect
import heapq
import sys

from withpy.commands.shared import read_input_text


def _sort_numeric(lines: list[str], reverse: bool) -> list[str]:
    """Sort lines by numeric value where possible.

    Args:
        lines: Input lines.
        reverse: Whether to reverse the sort.

    Returns:
        Sorted lines.
    """
    def key_fn(line: str) -> tuple[int, float, str]:
        try:
            return (0, float(line.strip()), line)
        except ValueError:
            return (1, 0.0, line)
    return sorted(lines, key=key_fn, reverse=reverse)


def _sort_length(lines: list[str], reverse: bool) -> list[str]:
    """Sort lines by length.

    Args:
        lines: Input lines.
        reverse: Whether to reverse the sort.

    Returns:
        Sorted lines.
    """
    return sorted(lines, key=len, reverse=reverse)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the sort subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("sort", help="Sort lines (alpha, numeric, length, top-N)")
    p.add_argument("--mode", "-m", default="alpha", choices=["alpha", "numeric", "length", "top", "bottom", "rank"], help="Sort mode (default: alpha)")
    p.add_argument("--reverse", "-r", action="store_true", help="Reverse sort order")
    p.add_argument("--unique", "-u", action="store_true", help="Remove duplicate lines")
    p.add_argument("--count", "-n", type=int, default=10, help="Number of items for top/bottom (default: 10)")
    p.add_argument("--field", "-f", type=int, default=None, help="Sort by field number (1-based, whitespace-delimited)")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the sort subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    text = read_input_text(args.input)
    lines = text.splitlines()
    if args.unique:
        seen: set[str] = set()
        unique_lines: list[str] = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        lines = unique_lines
    if args.field is not None:
        def field_key(line: str) -> str:
            parts = line.split()
            idx = args.field - 1
            return parts[idx] if 0 <= idx < len(parts) else ""
        key_fn = field_key
    else:
        key_fn = None
    match args.mode:
        case "alpha":
            result = sorted(lines, key=key_fn, reverse=args.reverse)
            for line in result:
                print(line)
        case "numeric":
            result = _sort_numeric(lines, args.reverse)
            for line in result:
                print(line)
        case "length":
            result = _sort_length(lines, args.reverse)
            for line in result:
                print(line)
        case "top":
            if key_fn:
                largest = heapq.nlargest(args.count, lines, key=key_fn)
            else:
                try:
                    largest = heapq.nlargest(args.count, lines, key=lambda x: float(x.strip()))
                except ValueError:
                    largest = heapq.nlargest(args.count, lines)
            for line in largest:
                print(line)
        case "bottom":
            if key_fn:
                smallest = heapq.nsmallest(args.count, lines, key=key_fn)
            else:
                try:
                    smallest = heapq.nsmallest(args.count, lines, key=lambda x: float(x.strip()))
                except ValueError:
                    smallest = heapq.nsmallest(args.count, lines)
            for line in smallest:
                print(line)
        case "rank":
            sorted_lines = sorted(set(lines))
            for line in lines:
                rank = bisect.bisect_left(sorted_lines, line) + 1
                print(f"{rank}\t{line}")
    return 0
