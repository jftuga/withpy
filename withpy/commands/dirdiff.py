"""Recursive directory comparison using filecmp.

Compares two directory trees and reports files that are common, differ,
or exist only in one side. Supports shallow comparison mode and pattern
exclusion.
"""

import argparse
import difflib
import filecmp
import os
import sys


def _compare_dirs(dir1: str, dir2: str, shallow: bool, ignore: list[str]) -> filecmp.dircmp:
    """Create a directory comparison object.

    Args:
        dir1: First directory path.
        dir2: Second directory path.
        shallow: If True, compare only stat info, not content.
        ignore: List of filename patterns to ignore.

    Returns:
        A dircmp object.
    """
    return filecmp.dircmp(dir1, dir2, ignore=ignore or filecmp.DEFAULT_IGNORES)


def _collect_diffs(dcmp: filecmp.dircmp, prefix: str, result: dict[str, list[str]], shallow: bool) -> None:
    """Recursively collect differences from a dircmp object.

    Args:
        dcmp: The directory comparison object.
        prefix: Current relative path prefix.
        result: Dictionary to accumulate results into.
        shallow: Whether to use shallow comparison.
    """
    for name in dcmp.left_only:
        result["left_only"].append(os.path.join(prefix, name))
    for name in dcmp.right_only:
        result["right_only"].append(os.path.join(prefix, name))
    common = dcmp.common_files
    if common:
        _, mismatch, errors = filecmp.cmpfiles(dcmp.left, dcmp.right, common, shallow=shallow)
        matched = [f for f in common if f not in mismatch and f not in errors]
        for name in mismatch:
            result["diff_files"].append(os.path.join(prefix, name))
        for name in matched:
            result["same_files"].append(os.path.join(prefix, name))
    for sub_dir, sub_dcmp in dcmp.subdirs.items():
        _collect_diffs(sub_dcmp, os.path.join(prefix, sub_dir), result, shallow)


def _format_report(result: dict[str, list[str]]) -> str:
    """Format a full comparison report.

    Args:
        result: Dictionary of categorized file paths.

    Returns:
        Formatted report string.
    """
    lines: list[str] = []
    if result["same_files"]:
        lines.append(f"Identical files ({len(result['same_files'])}):")
        for f in sorted(result["same_files"]):
            lines.append(f"  {f}")
        lines.append("")
    if result["diff_files"]:
        lines.append(f"Differing files ({len(result['diff_files'])}):")
        for f in sorted(result["diff_files"]):
            lines.append(f"  {f}")
        lines.append("")
    if result["left_only"]:
        lines.append(f"Only in left ({len(result['left_only'])}):")
        for f in sorted(result["left_only"]):
            lines.append(f"  {f}")
        lines.append("")
    if result["right_only"]:
        lines.append(f"Only in right ({len(result['right_only'])}):")
        for f in sorted(result["right_only"]):
            lines.append(f"  {f}")
    if not any(result.values()):
        lines.append("Directories are identical.")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the dirdiff subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("dirdiff", help="Recursive directory comparison")
    p.add_argument("--mode", "-m", default="report", choices=["report", "left-only", "right-only", "common", "diff"], help="Output mode (default: report)")
    p.add_argument("--shallow", action="store_true", help="Compare only file metadata, not content")
    p.add_argument("--ignore", nargs="*", default=[], help="Patterns to ignore")
    p.add_argument("dir1", help="First directory")
    p.add_argument("dir2", help="Second directory")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the dirdiff subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    if not os.path.isdir(args.dir1):
        print(f"error: not a directory: {args.dir1}", file=sys.stderr)
        return 1
    if not os.path.isdir(args.dir2):
        print(f"error: not a directory: {args.dir2}", file=sys.stderr)
        return 1
    try:
        dcmp = _compare_dirs(args.dir1, args.dir2, args.shallow, args.ignore)
        result: dict[str, list[str]] = {
            "left_only": [],
            "right_only": [],
            "diff_files": [],
            "same_files": [],
        }
        _collect_diffs(dcmp, "", result, args.shallow)
        match args.mode:
            case "report":
                print(_format_report(result))
            case "left-only":
                for f in sorted(result["left_only"]):
                    print(f)
            case "right-only":
                for f in sorted(result["right_only"]):
                    print(f)
            case "common":
                for f in sorted(result["same_files"]):
                    print(f)
            case "diff":
                for f in sorted(result["diff_files"]):
                    path1 = os.path.join(args.dir1, f)
                    path2 = os.path.join(args.dir2, f)
                    try:
                        with open(path1) as f1, open(path2) as f2:
                            diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=path1, tofile=path2)
                            sys.stdout.writelines(diff)
                    except (OSError, UnicodeDecodeError):
                        print(f"  (binary or unreadable: {f})")
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
