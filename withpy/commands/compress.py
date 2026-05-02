"""Compress and decompress data using gzip, zlib, bz2, and lzma formats.

Supports round-trip compression with configurable levels and automatic
format detection on decompression via magic byte signatures.
"""

import argparse
import bz2
import gzip
import lzma
import sys
import zlib

from withpy.commands.shared import read_input, write_output


_MAGIC_BYTES: dict[bytes, str] = {
    b"\x1f\x8b": "gzip",
    b"\x78\x01": "zlib",
    b"\x78\x5e": "zlib",
    b"\x78\x9c": "zlib",
    b"\x78\xda": "zlib",
    b"BZ": "bz2",
    b"\xfd7zXZ\x00": "lzma",
}


def _detect_format(data: bytes) -> str | None:
    """Detect compression format from magic bytes.

    Args:
        data: The compressed data.

    Returns:
        Format name or None if unrecognized.
    """
    for magic, fmt in _MAGIC_BYTES.items():
        if data.startswith(magic):
            return fmt
    return None


def _compress_data(data: bytes, fmt: str, level: int | None) -> bytes:
    """Compress data using the specified format.

    Args:
        data: Raw bytes to compress.
        fmt: Compression format name.
        level: Compression level, or None for default.

    Returns:
        Compressed bytes.

    Raises:
        ValueError: If the format is unknown or level is invalid.
    """
    match fmt:
        case "gzip":
            kwargs = {"compresslevel": level} if level is not None else {}
            return gzip.compress(data, **kwargs)
        case "zlib":
            if level is not None:
                return zlib.compress(data, level)
            return zlib.compress(data)
        case "bz2":
            kwargs = {"compresslevel": level} if level is not None else {}
            return bz2.compress(data, **kwargs)
        case "lzma":
            kwargs = {"preset": level} if level is not None else {}
            return lzma.compress(data, **kwargs)
        case _:
            raise ValueError(f"unknown compression format: {fmt}")


def _decompress_data(data: bytes, fmt: str) -> bytes:
    """Decompress data using the specified format.

    Args:
        data: Compressed bytes.
        fmt: Compression format name.

    Returns:
        Decompressed bytes.

    Raises:
        ValueError: If the format is unknown or data is corrupt.
    """
    match fmt:
        case "gzip":
            return gzip.decompress(data)
        case "zlib":
            return zlib.decompress(data)
        case "bz2":
            return bz2.decompress(data)
        case "lzma":
            return lzma.decompress(data)
        case _:
            raise ValueError(f"unknown compression format: {fmt}")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the compress subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("compress", help="Compress/decompress data (gzip, zlib, bz2, lzma)")
    p.add_argument("--mode", "-m", default="compress", choices=["compress", "decompress"], help="Operation mode (default: compress)")
    p.add_argument("--format", "-f", default="gzip", choices=["gzip", "zlib", "bz2", "lzma"], help="Compression format (default: gzip)")
    p.add_argument("--level", "-l", type=int, default=None, help="Compression level (format-dependent)")
    p.add_argument("--output", "-o", default=None, help="Output file (default: stdout)")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the compress subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        data = read_input(args.input)
        match args.mode:
            case "compress":
                result = _compress_data(data, args.format, args.level)
            case "decompress":
                fmt = args.format
                detected = _detect_format(data)
                if detected:
                    fmt = detected
                result = _decompress_data(data, fmt)
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        write_output(result, args.output)
        return 0
    except (ValueError, OSError, zlib.error, lzma.LZMAError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
