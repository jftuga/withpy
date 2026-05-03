"""Expand glob patterns and list matching files.

Uses the glob module to expand shell-style wildcards and display
matching file paths with optional metadata (size, modification time).
"""

import argparse
import glob
import os
import stat
import sys
import time


def _format_entry(path: str, show_size: bool, show_time: bool) -> str:
    """Format a file path with optional size and modification time.

    Args:
        path: File path.
        show_size: Whether to include file size.
        show_time: Whether to include modification time.

    Returns:
        Formatted string.
    """
    parts: list[str] = []
    if show_size or show_time:
        try:
            st = os.stat(path)
            if show_size:
                parts.append(f"{st.st_size:>10}")
            if show_time:
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
                parts.append(mtime)
        except OSError:
            if show_size:
                parts.append("         ?")
            if show_time:
                parts.append("???????????????????")
    parts.append(path)
    return "  ".join(parts)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the glob subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("glob", help="Expand glob patterns and list matches")
    p.add_argument("--recursive", "-r", action="store_true", help="Enable ** recursive matching")
    p.add_argument("--size", "-s", action="store_true", help="Show file sizes")
    p.add_argument("--time", "-t", action="store_true", help="Show modification times")
    p.add_argument("--count", "-c", action="store_true", help="Only print match count")
    p.add_argument("--sort", default=None, choices=["name", "size", "time"], help="Sort results")
    p.add_argument("pattern", nargs="+", help="Glob pattern(s) to expand")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the glob subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    matches: list[str] = []
    for pattern in args.pattern:
        results = glob.glob(pattern, recursive=args.recursive)
        matches.extend(results)
    if args.sort:
        match args.sort:
            case "name":
                matches.sort()
            case "size":
                matches.sort(key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0)
            case "time":
                matches.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    if args.count:
        print(len(matches))
        return 0
    for path in matches:
        print(_format_entry(path, args.size, args.time))
    return 0
