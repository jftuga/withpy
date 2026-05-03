"""Check and list Python keywords and soft keywords.

Uses the keyword module to test whether identifiers are Python
keywords or soft keywords, and to list all keywords for the
current Python version.
"""

import argparse
import keyword
import sys

from withpy.commands.shared import read_input_text


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the keyword subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("keyword", help="Check/list Python keywords")
    p.add_argument("--mode", "-m", default="check", choices=["check", "list", "filter"], help="Operation mode (default: check)")
    p.add_argument("words", nargs="*", default=None, help="Words to check")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the keyword subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    match args.mode:
        case "list":
            print("Keywords:")
            for kw in keyword.kwlist:
                print(f"  {kw}")
            print(f"\nSoft keywords:")
            for skw in keyword.softkwlist:
                print(f"  {skw}")
            print(f"\nTotal: {len(keyword.kwlist)} keywords, {len(keyword.softkwlist)} soft keywords")
        case "check":
            if not args.words:
                words = read_input_text(None).split()
            else:
                words = args.words
            found_keyword = False
            for word in words:
                is_kw = keyword.iskeyword(word)
                is_soft = keyword.issoftkeyword(word)
                if is_kw:
                    print(f"{word}: keyword")
                    found_keyword = True
                elif is_soft:
                    print(f"{word}: soft keyword")
                    found_keyword = True
                else:
                    print(f"{word}: not a keyword")
            return 0 if found_keyword else 1
        case "filter":
            if not args.words:
                words = read_input_text(None).split()
            else:
                words = args.words
            for word in words:
                if keyword.iskeyword(word) or keyword.issoftkeyword(word):
                    print(word)
    return 0
