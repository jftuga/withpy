"""Canonical hex and ASCII dump of binary data.

Produces output similar to xxd: offset column, hex byte values grouped
in pairs, and an ASCII representation with non-printable characters
replaced by dots. Supports reverse mode to convert hex dump back to binary.
"""

import argparse
import sys

from withpy.commands.shared import read_input


def _format_line(offset: int, chunk: bytes, width: int, show_ascii: bool) -> str:
    """Format a single line of hex dump output.

    Args:
        offset: Byte offset of this line.
        chunk: The bytes for this line.
        width: Expected bytes per line (for padding).
        show_ascii: Whether to include the ASCII column.

    Returns:
        Formatted hex dump line.
    """
    hex_parts = " ".join(f"{b:02x}" for b in chunk)
    padding = width * 3 - 1
    line = f"{offset:08x}  {hex_parts:<{padding}}"
    if show_ascii:
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        line += f"  |{ascii_part}|"
    return line


def _hexdump(data: bytes, width: int, offset: int, length: int | None, show_ascii: bool) -> str:
    """Generate a hex dump of binary data.

    Args:
        data: Binary data to dump.
        width: Number of bytes per line.
        offset: Starting byte offset to display.
        length: Maximum number of bytes to dump, or None for all.
        show_ascii: Whether to include ASCII column.

    Returns:
        The complete hex dump as a string.
    """
    if length is not None:
        data = data[offset:offset + length]
    else:
        data = data[offset:]
    lines: list[str] = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        lines.append(_format_line(offset + i, chunk, width, show_ascii))
    return "\n".join(lines)


def _reverse_hexdump(text: str) -> bytes:
    """Convert a hex dump back to binary data.

    Args:
        text: Hex dump text (one line per row, offset + hex bytes).

    Returns:
        The reconstructed binary data.

    Raises:
        ValueError: If the hex dump format is invalid.
    """
    result = bytearray()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")[0]
        if "  " in parts:
            parts = parts.split("  ", 1)[1]
        hex_str = parts.strip()
        try:
            chunk_bytes = bytes.fromhex(hex_str.replace(" ", ""))
            result.extend(chunk_bytes)
        except ValueError as e:
            raise ValueError(f"invalid hex data in line: {e}") from e
    return bytes(result)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the hexdump subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("hexdump", help="Hex + ASCII dump of binary data")
    p.add_argument("--width", "-w", type=int, default=16, help="Bytes per line (default: 16)")
    p.add_argument("--offset", type=int, default=0, help="Start offset in bytes (default: 0)")
    p.add_argument("--length", "-n", type=int, default=None, help="Maximum bytes to dump")
    p.add_argument("--no-ascii", action="store_true", help="Suppress ASCII column")
    p.add_argument("--reverse", "-r", action="store_true", help="Reverse: convert hex dump back to binary")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the hexdump subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        if args.reverse:
            data = read_input(args.input)
            result = _reverse_hexdump(data.decode(errors="replace"))
            sys.stdout.buffer.write(result)
            return 0
        data = read_input(args.input)
        output = _hexdump(data, args.width, args.offset, args.length, not args.no_ascii)
        if output:
            print(output)
        return 0
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
