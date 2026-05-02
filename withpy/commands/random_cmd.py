"""Non-cryptographic random operations: shuffle, sample, choice, dice.

Uses the random module for operations where cryptographic security
is not required: shuffling lines, sampling from lists, weighted
choices, and dice/coin simulation.
"""

import argparse
import json
import random
import sys

from withpy.commands.shared import read_input_text


def _shuffle_lines(text: str, seed: int | None) -> str:
    """Shuffle lines of text.

    Args:
        text: Input text.
        seed: Optional random seed for reproducibility.

    Returns:
        Text with lines shuffled.
    """
    if seed is not None:
        random.seed(seed)
    lines = text.splitlines()
    random.shuffle(lines)
    return "\n".join(lines)


def _sample_lines(text: str, count: int, seed: int | None) -> str:
    """Sample N lines from text without replacement.

    Args:
        text: Input text.
        count: Number of lines to sample.
        seed: Optional random seed.

    Returns:
        Sampled lines joined by newlines.
    """
    if seed is not None:
        random.seed(seed)
    lines = text.splitlines()
    count = min(count, len(lines))
    chosen = random.sample(lines, count)
    return "\n".join(chosen)


def _dice(spec: str, count: int, seed: int | None) -> list[int]:
    """Roll dice according to NdS notation.

    Args:
        spec: Dice spec like '2d6' or 'd20'.
        count: Number of times to roll.
        seed: Optional random seed.

    Returns:
        List of roll results.
    """
    if seed is not None:
        random.seed(seed)
    spec = spec.lower()
    if "d" not in spec:
        raise ValueError(f"invalid dice spec: {spec} (use NdS format, e.g. 2d6)")
    parts = spec.split("d")
    num = int(parts[0]) if parts[0] else 1
    sides = int(parts[1])
    if sides < 1 or num < 1:
        raise ValueError(f"invalid dice spec: {spec}")
    results: list[int] = []
    for _ in range(count):
        total = sum(random.randint(1, sides) for _ in range(num))
        results.append(total)
    return results


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the random subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("random", help="Shuffle, sample, dice, weighted choice")
    p.add_argument("--mode", "-m", default="shuffle", choices=["shuffle", "sample", "choice", "dice", "float", "int"], help="Operation mode (default: shuffle)")
    p.add_argument("--count", "-n", type=int, default=1, help="Number of results (default: 1)")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    p.add_argument("--min", type=int, default=1, dest="range_min", help="Minimum for int mode (default: 1)")
    p.add_argument("--max", type=int, default=100, dest="range_max", help="Maximum for int mode (default: 100)")
    p.add_argument("args", nargs="*", default=None, help="Items for choice, dice spec, or input file")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the random subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    if args.seed is not None:
        random.seed(args.seed)
    match args.mode:
        case "shuffle":
            if args.args:
                text = read_input_text(args.args[0])
            else:
                text = read_input_text(None)
            print(_shuffle_lines(text, args.seed))
        case "sample":
            if args.args:
                text = read_input_text(args.args[0])
            else:
                text = read_input_text(None)
            print(_sample_lines(text, args.count, args.seed))
        case "choice":
            if not args.args:
                items = read_input_text(None).splitlines()
            else:
                items = args.args
            items = [i for i in items if i.strip()]
            if not items:
                print("error: no items to choose from", file=sys.stderr)
                return 1
            for _ in range(args.count):
                print(random.choice(items))
        case "dice":
            spec = args.args[0] if args.args else "1d6"
            try:
                results = _dice(spec, args.count, args.seed)
                for r in results:
                    print(r)
                if args.count > 1:
                    print(f"sum: {sum(results)}")
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
        case "float":
            for _ in range(args.count):
                print(f"{random.random():.6f}")
        case "int":
            for _ in range(args.count):
                print(random.randint(args.range_min, args.range_max))
    return 0
