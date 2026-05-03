"""Compare two files and output unified, context, HTML, or ndiff format.

Uses Python's difflib module to compute and display differences between
two text files. Returns exit code 0 if files are identical, 1 if they
differ, matching Unix diff conventions.
"""

import argparse
import difflib
import sys


def _read_file_lines(path: str) -> list[str]:
    """Read a file into a list of lines with newlines preserved.

    Args:
        path: File path to read.

    Returns:
        List of lines including newline characters.

    Raises:
        OSError: If the file cannot be read.
    """
    with open(path, "r") as f:
        return f.readlines()


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the diff subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("diff", help="Compare two files (unified/context/HTML/ndiff)")
    p.add_argument("--format", "-f", default="unified", choices=["unified", "context", "html", "ndiff"], help="Diff format (default: unified)")
    p.add_argument("--context", "-c", type=int, default=3, help="Context lines (default: 3)")
    p.add_argument("file1", help="First file")
    p.add_argument("file2", help="Second file")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the diff subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 if files are identical, 1 if they differ.
    """
    try:
        lines1 = _read_file_lines(args.file1)
        lines2 = _read_file_lines(args.file2)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if lines1 == lines2:
        return 0
    match args.format:
        case "unified":
            result = difflib.unified_diff(lines1, lines2, fromfile=args.file1, tofile=args.file2, n=args.context)
        case "context":
            result = difflib.context_diff(lines1, lines2, fromfile=args.file1, tofile=args.file2, n=args.context)
        case "html":
            differ = difflib.HtmlDiff()
            html = differ.make_file(lines1, lines2, fromdesc=args.file1, todesc=args.file2, context=True, numlines=args.context)
            sys.stdout.write(html)
            return 1
        case "ndiff":
            result = difflib.ndiff(lines1, lines2)
        case _:
            print(f"error: unknown format: {args.format}", file=sys.stderr)
            return 2
    output = "".join(result)
    if output:
        sys.stdout.write(output)
    return 1
