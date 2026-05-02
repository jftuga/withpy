"""Combinatoric and iterator operations on input lines.

Uses itertools to perform permutations, combinations, products,
grouping, and chunking on line-oriented input data.
"""

import argparse
import functools
import itertools
import operator
import sys

from withpy.commands.shared import read_input_text


def _chunk(items: list[str], size: int) -> list[list[str]]:
    """Split a list into chunks of the given size.

    Args:
        items: List to chunk.
        size: Chunk size.

    Returns:
        List of chunks.
    """
    return [items[i:i + size] for i in range(0, len(items), size)]


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the iter subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("iter", help="Combinatoric operations (permutations, combinations, product)")
    p.add_argument("--mode", "-m", default="product", choices=["permutations", "combinations", "product", "chunk", "unique", "repeat", "chain", "accumulate", "reduce"], help="Operation mode (default: product)")
    p.add_argument("--r", "-r", type=int, default=None, dest="r_val", help="r value for combinations/permutations")
    p.add_argument("--size", "-s", type=int, default=2, help="Chunk size (default: 2)")
    p.add_argument("--count", "-n", type=int, default=2, help="Repeat count (default: 2)")
    p.add_argument("--sep", default=",", help="Output separator (default: ,)")
    p.add_argument("input", nargs="*", default=None, help="Items (or read from stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the iter subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    if args.input:
        items = args.input
    else:
        text = read_input_text(None)
        items = [line for line in text.splitlines() if line.strip()]
    if not items:
        print("error: no input items", file=sys.stderr)
        return 1
    match args.mode:
        case "permutations":
            r = args.r_val or len(items)
            for perm in itertools.permutations(items, r):
                print(args.sep.join(perm))
        case "combinations":
            r = args.r_val or 2
            for combo in itertools.combinations(items, r):
                print(args.sep.join(combo))
        case "product":
            r = args.r_val or 2
            for prod in itertools.product(items, repeat=r):
                print(args.sep.join(prod))
        case "chunk":
            for chunk in _chunk(items, args.size):
                print(args.sep.join(chunk))
        case "unique":
            seen: set[str] = set()
            for item in items:
                if item not in seen:
                    seen.add(item)
                    print(item)
        case "repeat":
            for item in itertools.islice(itertools.cycle(items), len(items) * args.count):
                print(item)
        case "chain":
            for item in itertools.chain.from_iterable([items] * args.count):
                print(item)
        case "accumulate":
            try:
                nums = [int(x) for x in items]
                for val in itertools.accumulate(nums, operator.add):
                    print(val)
            except ValueError:
                prefix = ""
                for i, item in enumerate(items):
                    prefix = item if i == 0 else prefix + args.sep + item
                    print(prefix)
        case "reduce":
            try:
                nums = [int(x) for x in items]
                print(functools.reduce(operator.add, nums))
            except ValueError:
                print(functools.reduce(lambda a, b: a + args.sep + b, items))
    return 0
