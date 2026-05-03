"""Cron-like one-shot and recurring task runner.

Provides modes for running shell commands after a delay, at recurring
intervals, or at a specific time of day. Uses the sched module for
scheduling and subprocess for command execution.
"""

import argparse
import datetime
import sched
import subprocess
import sys
import threading
import time


def _run_command(command: list[str]) -> int:
    """Execute a shell command and return its exit code.

    Args:
        command: Command and arguments list.

    Returns:
        Process exit code.
    """
    try:
        result = subprocess.run(command, capture_output=False)
        return result.returncode
    except (OSError, subprocess.SubprocessError) as e:
        print(f"error running command: {e}", file=sys.stderr)
        return 1


def _parse_time(time_str: str) -> float:
    """Parse a HH:MM:SS time string to a target epoch.

    Args:
        time_str: Time in HH:MM:SS or HH:MM format.

    Returns:
        Target epoch time (today or tomorrow if past).

    Raises:
        ValueError: If format is invalid.
    """
    now = datetime.datetime.now()
    parts = time_str.split(":")
    if len(parts) == 2:
        hour, minute, second = int(parts[0]), int(parts[1]), 0
    elif len(parts) == 3:
        hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
    else:
        raise ValueError(f"invalid time format: {time_str} (expected HH:MM or HH:MM:SS)")
    target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target.timestamp()


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the sched subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("sched", help="Schedule one-shot or recurring commands")
    p.add_argument("--mode", "-m", default="once", choices=["once", "every", "at"], help="Schedule mode (default: once)")
    p.add_argument("--delay", type=float, default=0, help="Delay before first run in seconds (default: 0)")
    p.add_argument("--interval", type=float, default=None, help="Repeat interval in seconds (every mode)")
    p.add_argument("--count", "-n", type=int, default=None, help="Max repetitions (None=infinite for every mode)")
    p.add_argument("--at", default=None, help="Time to run (HH:MM or HH:MM:SS)")
    p.add_argument("command", nargs="+", help="Command to execute")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the sched subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "once":
                if args.delay > 0:
                    print(f"waiting {args.delay}s...", file=sys.stderr)
                    time.sleep(args.delay)
                return _run_command(args.command)
            case "every":
                if args.interval is None:
                    print("error: --interval required for every mode", file=sys.stderr)
                    return 1
                if args.delay > 0:
                    time.sleep(args.delay)
                count = 0
                try:
                    while args.count is None or count < args.count:
                        rc = _run_command(args.command)
                        count += 1
                        if args.count is not None and count >= args.count:
                            break
                        time.sleep(args.interval)
                except KeyboardInterrupt:
                    print(f"\nstopped after {count} runs", file=sys.stderr)
                return 0
            case "at":
                if not args.at:
                    print("error: --at required for at mode", file=sys.stderr)
                    return 1
                target = _parse_time(args.at)
                wait = target - time.time()
                if wait > 0:
                    target_str = datetime.datetime.fromtimestamp(target).strftime("%H:%M:%S")
                    print(f"waiting until {target_str} ({wait:.0f}s)...", file=sys.stderr)
                    time.sleep(wait)
                return _run_command(args.command)
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
