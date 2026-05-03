"""Find files by glob pattern, size, modification time, and type.

Walks directory trees with configurable filters for filename matching,
file type selection, size comparison, modification time comparison, and
maximum recursion depth.
"""

import argparse
import fnmatch
import os
import stat
import sys
import time
from pathlib import Path


def _parse_size(size_str: str) -> tuple[str, int]:
    """Parse a size filter string like '+10M' or '-1K'.

    Args:
        size_str: Size expression with optional +/- prefix and unit suffix.

    Returns:
        Tuple of (comparator '+'/'-'/'=', size in bytes).

    Raises:
        ValueError: If format is invalid.
    """
    multipliers = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3}
    if size_str[0] in ("+", "-"):
        comp = size_str[0]
        rest = size_str[1:]
    else:
        comp = "="
        rest = size_str
    unit = rest[-1].upper() if rest[-1].upper() in multipliers else "B"
    num_str = rest[:-1] if rest[-1].upper() in multipliers else rest
    try:
        value = int(num_str) * multipliers[unit]
    except ValueError:
        raise ValueError(f"invalid size: {size_str}") from None
    return (comp, value)


def _parse_mtime(mtime_str: str) -> tuple[str, float]:
    """Parse a modification time filter like '+7d' or '-1h'.

    Args:
        mtime_str: Time expression with +/- prefix and unit suffix.

    Returns:
        Tuple of (comparator, epoch threshold).

    Raises:
        ValueError: If format is invalid.
    """
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    if mtime_str[0] in ("+", "-"):
        comp = mtime_str[0]
        rest = mtime_str[1:]
    else:
        comp = "-"
        rest = mtime_str
    unit = rest[-1].lower() if rest[-1].lower() in units else "d"
    num_str = rest[:-1] if rest[-1].lower() in units else rest
    try:
        seconds = int(num_str) * units[unit]
    except ValueError:
        raise ValueError(f"invalid mtime: {mtime_str}") from None
    threshold = time.time() - seconds
    return (comp, threshold)


def _matches_size(file_size: int, comp: str, target: int) -> bool:
    """Check if a file size matches the filter.

    Args:
        file_size: Actual file size.
        comp: Comparator (+, -, =).
        target: Target size.

    Returns:
        True if matches.
    """
    match comp:
        case "+":
            return file_size > target
        case "-":
            return file_size < target
        case _:
            return file_size == target


def _matches_mtime(file_mtime: float, comp: str, threshold: float) -> bool:
    """Check if a file's mtime matches the filter.

    Args:
        file_mtime: File modification time (epoch).
        comp: Comparator (+ = older than, - = newer than).
        threshold: Epoch threshold.

    Returns:
        True if matches.
    """
    match comp:
        case "+":
            return file_mtime < threshold
        case _:
            return file_mtime > threshold


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the find subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("find", help="Find files by glob, size, mtime, type")
    p.add_argument("path", nargs="?", default=".", help="Starting directory (default: .)")
    p.add_argument("--name", "-n", default=None, help="Glob pattern for filenames")
    p.add_argument("--iname", default=None, help="Case-insensitive name pattern")
    p.add_argument("--type", "-t", default=None, choices=["f", "d", "l"], help="File type (f=file, d=dir, l=link)")
    p.add_argument("--size", default=None, help="Size filter (+10M, -1K, 100)")
    p.add_argument("--mtime", default=None, help="Modification time filter (+7d, -1h)")
    p.add_argument("--maxdepth", type=int, default=None, help="Maximum recursion depth")
    p.add_argument("--count", action="store_true", help="Only print match count")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the find subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        size_filter = _parse_size(args.size) if args.size else None
        mtime_filter = _parse_mtime(args.mtime) if args.mtime else None
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if not os.path.exists(args.path):
        print(f"error: path not found: {args.path}", file=sys.stderr)
        return 1
    matches: list[str] = []
    base_depth = args.path.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(args.path):
        current_depth = root.count(os.sep) - base_depth
        if args.maxdepth is not None and current_depth >= args.maxdepth:
            dirs.clear()
            continue
        entries: list[tuple[str, str]] = []
        if args.type != "f":
            for d in dirs:
                entries.append((os.path.join(root, d), "d"))
        if args.type != "d":
            for f in files:
                full = os.path.join(root, f)
                if os.path.islink(full):
                    entries.append((full, "l"))
                else:
                    entries.append((full, "f"))
        for path, ftype in entries:
            if args.type and args.type != ftype:
                continue
            basename = os.path.basename(path)
            if args.name and not fnmatch.fnmatch(basename, args.name):
                continue
            if args.iname and not fnmatch.fnmatch(basename.lower(), args.iname.lower()):
                continue
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if size_filter and not _matches_size(st.st_size, *size_filter):
                continue
            if mtime_filter and not _matches_mtime(st.st_mtime, *mtime_filter):
                continue
            matches.append(path)
    if args.count:
        print(len(matches))
    else:
        for m in sorted(matches):
            print(m)
    return 0
