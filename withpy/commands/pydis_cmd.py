"""Disassemble Python source or .pyc files into bytecode.

Uses the dis module to disassemble Python code into bytecode
instructions, showing opcodes, arguments, and code object details.
"""

import argparse
import dis
import io
import sys
import traceback


def _disassemble_source(source: str) -> str:
    """Disassemble Python source code to bytecode.

    Args:
        source: Python source code string.

    Returns:
        Disassembly output string.

    Raises:
        SyntaxError: If the source has syntax errors.
    """
    code = compile(source, "<input>", "exec")
    output = io.StringIO()
    dis.dis(code, file=output)
    return output.getvalue()


def _show_code_info(source: str) -> str:
    """Show code object info for Python source.

    Args:
        source: Python source code string.

    Returns:
        Code info output string.

    Raises:
        SyntaxError: If the source has syntax errors.
    """
    code = compile(source, "<input>", "exec")
    output = io.StringIO()
    dis.show_code(code, file=output)
    return output.getvalue()


def _instruction_count(source: str) -> dict[str, int]:
    """Count bytecode instructions by opname.

    Args:
        source: Python source code string.

    Returns:
        Dictionary mapping opname to count.
    """
    code = compile(source, "<input>", "exec")
    counts: dict[str, int] = {}
    for instr in dis.get_instructions(code):
        counts[instr.opname] = counts.get(instr.opname, 0) + 1
    return counts


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the pydis subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("pydis", help="Disassemble Python source to bytecode")
    p.add_argument("--mode", "-m", default="dis", choices=["dis", "info", "stats"], help="Operation mode (default: dis)")
    p.add_argument("file", nargs="?", default=None, help="Python file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the pydis subcommand.

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
        match args.mode:
            case "dis":
                print(_disassemble_source(source))
            case "info":
                print(_show_code_info(source))
            case "stats":
                counts = _instruction_count(source)
                total = sum(counts.values())
                print(f"Total instructions: {total}\n")
                for opname, count in sorted(counts.items(), key=lambda x: -x[1]):
                    pct = count / total * 100
                    print(f"  {opname:<25} {count:>4} ({pct:.1f}%)")
        return 0
    except SyntaxError as e:
        print("error: syntax error:", file=sys.stderr)
        traceback.print_exception(e, file=sys.stderr)
        return 1
