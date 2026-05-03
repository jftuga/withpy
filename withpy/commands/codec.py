"""Encode and decode data in various formats.

Combined module that registers both the 'encode' and 'decode' subcommands.
Supports base64, base32, hex, ascii85, URL percent-encoding, HTML entities,
quoted-printable, and UTF-16. Mirrors mtool's internal/codec package.
"""

import argparse
import base64
import binascii
import codecs
import html
import quopri
import sys
import urllib.parse

from withpy.commands.shared import read_input

_FORMATS: list[str] = [
    "base64", "base32", "hex", "ascii85", "url", "html", "quopri", "utf16",
]


def _encode(data: bytes, fmt: str) -> bytes:
    """Encode binary data in the specified format.

    Args:
        data: Raw bytes to encode.
        fmt: One of the supported format names.

    Returns:
        The encoded data as bytes.

    Raises:
        ValueError: If the format is unknown.
    """
    match fmt:
        case "base64":
            return base64.b64encode(data)
        case "base32":
            return base64.b32encode(data)
        case "hex":
            return binascii.hexlify(data)
        case "ascii85":
            return base64.a85encode(data)
        case "url":
            return urllib.parse.quote_plus(data.decode()).encode()
        case "html":
            return html.escape(data.decode()).encode()
        case "quopri":
            return quopri.encodestring(data)
        case "utf16":
            return codecs.encode(data.decode(), "utf-16")
        case _:
            raise ValueError(f"unknown format: {fmt}")


def _decode(data: bytes, fmt: str) -> bytes:
    """Decode data from the specified format back to raw bytes.

    Args:
        data: Encoded data.
        fmt: One of the supported format names.

    Returns:
        The decoded raw bytes.

    Raises:
        ValueError: If the format is unknown or the data is malformed.
    """
    match fmt:
        case "base64":
            return base64.b64decode(data)
        case "base32":
            return base64.b32decode(data)
        case "hex":
            return binascii.unhexlify(data.strip())
        case "ascii85":
            return base64.a85decode(data)
        case "url":
            return urllib.parse.unquote_plus(data.decode()).encode()
        case "html":
            return html.unescape(data.decode()).encode()
        case "quopri":
            return quopri.decodestring(data)
        case "utf16":
            return codecs.decode(data, "utf-16").encode()
        case _:
            raise ValueError(f"unknown format: {fmt}")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the encode and decode subcommands.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    for mode in ("encode", "decode"):
        verb = "Encode" if mode == "encode" else "Decode"
        p = subparsers.add_parser(mode, help=f"{verb} data (base64, hex, url, ...)")
        p.add_argument("--format", "-f", default="base64", choices=_FORMATS, help="Encoding format (default: base64)")
        p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
        p.set_defaults(func=run, _codec_mode=mode)


def run(args: argparse.Namespace) -> int:
    """Execute the encode or decode subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        data = read_input(args.input)
        match args._codec_mode:
            case "encode":
                result = _encode(data, args.format)
            case "decode":
                result = _decode(data, args.format)
            case _:
                print(f"error: unknown codec mode: {args._codec_mode}", file=sys.stderr)
                return 1
        sys.stdout.buffer.write(result)
        if not result.endswith(b"\n"):
            sys.stdout.buffer.write(b"\n")
        return 0
    except (ValueError, binascii.Error, UnicodeDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
