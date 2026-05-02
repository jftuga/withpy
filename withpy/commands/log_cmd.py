"""Log file viewing: tail, grep, level filtering, and statistics.

Provides modes for tailing log files, filtering by regex pattern or
log level, computing log statistics, and parsing structured log lines
into JSON format.
"""

import argparse
import json
import re
import sys


_LEVEL_PATTERN = re.compile(r'\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b')

_LOG_LINE_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.,]?\d*)\s+(\w+)\s+(.+)$')


def _tail_lines(path: str, count: int) -> list[str]:
    """Read the last N lines of a file efficiently.

    Args:
        path: File path.
        count: Number of lines to return.

    Returns:
        Last N lines of the file.
    """
    with open(path, "r") as f:
        lines = f.readlines()
    return lines[-count:]


def _grep_lines(path: str, pattern: str) -> list[str]:
    """Filter lines matching a regex pattern.

    Args:
        path: File path.
        pattern: Regex pattern to match.

    Returns:
        Matching lines.

    Raises:
        re.error: If pattern is invalid.
    """
    compiled = re.compile(pattern)
    results: list[str] = []
    with open(path, "r") as f:
        for line in f:
            if compiled.search(line):
                results.append(line)
    return results


def _filter_by_level(path: str, level: str) -> list[str]:
    """Filter log lines by minimum log level.

    Args:
        path: File path.
        level: Minimum level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Lines at or above the specified level.
    """
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    min_idx = levels.index(level)
    results: list[str] = []
    with open(path, "r") as f:
        for line in f:
            match = _LEVEL_PATTERN.search(line)
            if match:
                line_level = match.group(1)
                if levels.index(line_level) >= min_idx:
                    results.append(line)
    return results


def _compute_stats(path: str) -> str:
    """Compute statistics about a log file.

    Args:
        path: File path.

    Returns:
        Formatted statistics.
    """
    level_counts: dict[str, int] = {
        "DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0,
    }
    total = 0
    first_time = None
    last_time = None
    with open(path, "r") as f:
        for line in f:
            total += 1
            match = _LEVEL_PATTERN.search(line)
            if match:
                level_counts[match.group(1)] += 1
            time_match = re.match(r'^(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})', line)
            if time_match:
                ts = time_match.group(1)
                if first_time is None:
                    first_time = ts
                last_time = ts
    lines: list[str] = [
        f"Total lines: {total}",
        f"Time range:  {first_time or 'unknown'} to {last_time or 'unknown'}",
        "",
        "Level counts:",
    ]
    for level, count in level_counts.items():
        if count > 0:
            lines.append(f"  {level:<10} {count:>6}")
    return "\n".join(lines)


def _parse_log(path: str) -> str:
    """Parse structured log lines into JSON.

    Args:
        path: File path.

    Returns:
        JSON array of parsed log entries.
    """
    entries: list[dict[str, str]] = []
    with open(path, "r") as f:
        for line in f:
            match = _LOG_LINE_PATTERN.match(line.rstrip())
            if match:
                entries.append({
                    "timestamp": match.group(1),
                    "level": match.group(2),
                    "message": match.group(3),
                })
            else:
                stripped = line.rstrip()
                if stripped:
                    entries.append({"raw": stripped})
    return json.dumps(entries, indent=2)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the log subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("log", help="Tail, filter, grep log files")
    p.add_argument("--mode", "-m", default="tail", choices=["tail", "grep", "level", "stats", "parse"], help="Operation mode (default: tail)")
    p.add_argument("--lines", "-n", type=int, default=10, help="Number of lines for tail (default: 10)")
    p.add_argument("--pattern", "-p", default=None, help="Regex pattern for grep mode")
    p.add_argument("--level", "-l", default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Minimum log level for level mode")
    p.add_argument("input", help="Log file path")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the log subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "tail":
                lines = _tail_lines(args.input, args.lines)
                sys.stdout.writelines(lines)
            case "grep":
                if not args.pattern:
                    print("error: --pattern required for grep mode", file=sys.stderr)
                    return 1
                lines = _grep_lines(args.input, args.pattern)
                sys.stdout.writelines(lines)
            case "level":
                if not args.level:
                    print("error: --level required for level mode", file=sys.stderr)
                    return 1
                lines = _filter_by_level(args.input, args.level)
                sys.stdout.writelines(lines)
            case "stats":
                print(_compute_stats(args.input))
            case "parse":
                print(_parse_log(args.input))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except re.error as e:
        print(f"error: invalid regex: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
