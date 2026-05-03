"""Pack and unpack binary data using struct format strings.

Provides modes for packing values into binary data, unpacking binary data
into values, and computing struct sizes. Supports endianness selection
and multiple output formats.
"""

import argparse
import struct
import sys

from withpy.commands.shared import read_input


_ENDIAN_PREFIXES: dict[str, str] = {
    "native": "@",
    "little": "<",
    "big": ">",
    "network": "!",
}


def _build_format(fmt: str, endian: str) -> str:
    """Prepend endianness prefix to format string if needed.

    Args:
        fmt: The struct format string.
        endian: Endianness name.

    Returns:
        Format string with prefix.
    """
    if fmt and fmt[0] in "@=<>!":
        return fmt
    prefix = _ENDIAN_PREFIXES.get(endian, "@")
    return prefix + fmt


def _parse_value(val_str: str) -> int | float:
    """Parse a string value for packing.

    Args:
        val_str: String representation of a number.

    Returns:
        Parsed numeric value.
    """
    val_str = val_str.strip()
    if val_str.startswith("0x") or val_str.startswith("0X"):
        return int(val_str, 16)
    if val_str.startswith("0b") or val_str.startswith("0B"):
        return int(val_str, 2)
    if val_str.startswith("0o") or val_str.startswith("0O"):
        return int(val_str, 8)
    if "." in val_str or "e" in val_str.lower():
        return float(val_str)
    return int(val_str)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the struct subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("struct", help="Pack/unpack binary data with format strings")
    p.add_argument("--mode", "-m", default="unpack", choices=["pack", "unpack", "size"], help="Operation mode (default: unpack)")
    p.add_argument("--format", "-f", required=True, help="Struct format string (e.g. '>3I')")
    p.add_argument("--endian", "-e", default="native", choices=["native", "little", "big", "network"], help="Endianness (default: native)")
    p.add_argument("--output-format", default="hex", choices=["hex", "decimal", "raw"], help="Output format for pack (default: hex)")
    p.add_argument("values", nargs="*", help="Values to pack, or hex string to unpack")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the struct subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        fmt = _build_format(args.format, args.endian)
        match args.mode:
            case "pack":
                if not args.values:
                    print("error: values required for pack mode", file=sys.stderr)
                    return 1
                values = [_parse_value(v) for v in args.values]
                packed = struct.pack(fmt, *values)
                match args.output_format:
                    case "hex":
                        print(packed.hex())
                    case "decimal":
                        print(" ".join(str(b) for b in packed))
                    case "raw":
                        sys.stdout.buffer.write(packed)
            case "unpack":
                if args.values:
                    hex_str = "".join(args.values).replace(" ", "")
                    data = bytes.fromhex(hex_str)
                else:
                    data = read_input(None)
                values = struct.unpack(fmt, data)
                print(" ".join(str(v) for v in values))
            case "size":
                size = struct.calcsize(fmt)
                print(size)
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (struct.error, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
