"""Tokenize Python source files into token streams.

Uses the tokenize and token stdlib modules to break Python source
code into tokens, display token types and values, and provide
statistics about the token distribution.
"""

import argparse
import io
import json
import sys
import token
import tokenize
from collections import Counter


def _tokenize_source(source: str) -> list[tuple[str, str, int, int]]:
    """Tokenize Python source into a list of token tuples.

    Args:
        source: Python source code string.

    Returns:
        List of (type_name, string, start_line, start_col) tuples.
    """
    tokens: list[tuple[str, str, int, int]] = []
    readline = io.BytesIO(source.encode()).readline
    for tok in tokenize.tokenize(readline):
        type_name = token.tok_name.get(tok.type, "UNKNOWN")
        tokens.append((type_name, tok.string, tok.start[0], tok.start[1]))
    return tokens


def _format_tokens(tokens: list[tuple[str, str, int, int]]) -> str:
    """Format tokens as a readable table.

    Args:
        tokens: List of token tuples.

    Returns:
        Formatted string.
    """
    lines: list[str] = []
    for type_name, string, line, col in tokens:
        display = repr(string) if string.strip() != string or not string else string
        lines.append(f"{line:>4}:{col:<3} {type_name:<10} {display}")
    return "\n".join(lines)


def _token_stats(tokens: list[tuple[str, str, int, int]]) -> str:
    """Generate statistics about token distribution.

    Args:
        tokens: List of token tuples.

    Returns:
        Formatted statistics string.
    """
    counter = Counter(t[0] for t in tokens)
    total = len(tokens)
    lines: list[str] = [f"Total tokens: {total}", ""]
    for name, count in counter.most_common():
        pct = count / total * 100
        lines.append(f"  {name:<15} {count:>6} ({pct:.1f}%)")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the tokenize subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("tokenize", help="Tokenize Python source files")
    p.add_argument("--mode", "-m", default="tokens", choices=["tokens", "stats", "json"], help="Operation mode (default: tokens)")
    p.add_argument("file", nargs="?", default=None, help="Python file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the tokenize subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        if args.file is None or args.file == "-":
            source = sys.stdin.read()
        else:
            with open(args.file, "r") as f:
                source = f.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        tokens = _tokenize_source(source)
    except tokenize.TokenError as e:
        print(f"error: tokenization failed: {e}", file=sys.stderr)
        return 1
    match args.mode:
        case "tokens":
            print(_format_tokens(tokens))
        case "stats":
            print(_token_stats(tokens))
        case "json":
            data = [{"type": t, "string": s, "line": l, "col": c} for t, s, l, c in tokens]
            print(json.dumps(data, indent=2))
    return 0
