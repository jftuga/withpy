"""Profile a Python script using cProfile and display statistics.

Runs a Python script under cProfile, collects performance statistics,
and displays the top functions sorted by the specified criteria.
Supports saving raw stats files for later analysis.
"""

import argparse
import cProfile
import io
import linecache
import pstats
import sys


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the profile subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("profile", help="Profile a Python script and show stats")
    p.add_argument("--sort", "-s", default="cumulative", choices=["cumulative", "tottime", "calls", "name"], help="Sort key (default: cumulative)")
    p.add_argument("--lines", "-n", type=int, default=20, help="Number of lines to show (default: 20)")
    p.add_argument("--output", "-o", default=None, help="Save raw stats to file")
    p.add_argument("--callers", action="store_true", help="Show caller information")
    p.add_argument("--source", action="store_true", help="Show source lines for top functions")
    p.add_argument("script", help="Python script to profile")
    p.add_argument("script_args", nargs="*", help="Arguments for the script")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the profile subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        with open(args.script, "r") as f:
            code = f.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        compiled = compile(code, args.script, "exec")
    except SyntaxError as e:
        print(f"error: syntax error in {args.script}: {e}", file=sys.stderr)
        return 1
    profiler = cProfile.Profile()
    old_argv = sys.argv[:]
    sys.argv = [args.script] + args.script_args
    try:
        profiler.enable()
        exec(compiled, {"__name__": "__main__", "__file__": args.script})
        profiler.disable()
    except SystemExit:
        profiler.disable()
    except Exception as e:
        profiler.disable()
        print(f"error: script raised {type(e).__name__}: {e}", file=sys.stderr)
    finally:
        sys.argv = old_argv
    if args.output:
        profiler.dump_stats(args.output)
        print(f"stats saved to: {args.output}")
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats(args.sort)
    if args.callers:
        stats.print_callers(args.lines)
    else:
        stats.print_stats(args.lines)
    print(stream.getvalue())
    if args.source:
        _print_source_lines(stats, args.lines)
    return 0


def _print_source_lines(stats: pstats.Stats, limit: int) -> None:
    """Print source lines for the top profiled functions.

    Args:
        stats: Profile statistics.
        limit: Maximum number of functions to show.
    """
    print("\n--- Source lines for top functions ---\n")
    sorted_stats = sorted(stats.stats.items(), key=lambda x: x[1][3], reverse=True)
    for (filename, lineno, name), _ in sorted_stats[:limit]:
        if filename.startswith("<") or not lineno:
            continue
        line = linecache.getline(filename, lineno).rstrip()
        if line:
            print(f"  {filename}:{lineno} ({name})")
            print(f"    {line}")
    linecache.clearcache()
