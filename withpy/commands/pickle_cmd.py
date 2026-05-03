"""Pickle file inspection and disassembly without executing pickled objects.

Provides safe inspection of pickle files using pickletools to display
opcodes and metadata without deserializing the data. Useful for auditing
pickle files for safety before loading them.
"""

import argparse
import io
import pickle
import pickletools
import sys


def _disassemble(data: bytes) -> str:
    """Disassemble pickle bytes into human-readable opcodes.

    Args:
        data: Raw pickle bytes.

    Returns:
        Disassembly output string.
    """
    output = io.StringIO()
    pickletools.dis(io.BytesIO(data), output)
    return output.getvalue()


def _get_info(data: bytes) -> dict[str, str | int]:
    """Extract basic information from pickle data.

    Args:
        data: Raw pickle bytes.

    Returns:
        Dictionary of pickle metadata.
    """
    info: dict[str, str | int] = {}
    info["size_bytes"] = len(data)
    if len(data) >= 2:
        proto = data[1] if data[0] == 0x80 else 0
        info["protocol"] = proto
    else:
        info["protocol"] = 0
    opcodes = list(pickletools.genops(io.BytesIO(data)))
    info["opcode_count"] = len(opcodes)
    opnames = set(op[0].name for op in opcodes)
    dangerous = {"GLOBAL", "INST", "OBJ", "REDUCE", "BUILD", "STACK_GLOBAL"}
    found_dangerous = opnames & dangerous
    info["potentially_dangerous"] = ", ".join(sorted(found_dangerous)) if found_dangerous else "none"
    return info


def _optimize(data: bytes) -> bytes:
    """Optimize pickle data by removing unused PUT opcodes.

    Args:
        data: Raw pickle bytes.

    Returns:
        Optimized pickle bytes.
    """
    return pickletools.optimize(data)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the pickle subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("pickle", help="Inspect/disassemble pickle files safely")
    p.add_argument("--mode", "-m", default="info", choices=["info", "dis", "optimize"], help="Operation mode (default: info)")
    p.add_argument("--output", "-o", default=None, help="Output file for optimize mode")
    p.add_argument("file", nargs="?", default=None, help="Pickle file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the pickle subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        if args.file is None or args.file == "-":
            data = sys.stdin.buffer.read()
        else:
            with open(args.file, "rb") as f:
                data = f.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        match args.mode:
            case "info":
                info = _get_info(data)
                for key, val in info.items():
                    print(f"{key}: {val}")
            case "dis":
                print(_disassemble(data))
            case "optimize":
                optimized = _optimize(data)
                if args.output:
                    with open(args.output, "wb") as f:
                        f.write(optimized)
                    saved = len(data) - len(optimized)
                    print(f"optimized: {len(data)} -> {len(optimized)} bytes (saved {saved})")
                else:
                    sys.stdout.buffer.write(optimized)
        return 0
    except Exception as e:
        print(f"error: invalid pickle data: {e}", file=sys.stderr)
        return 1
