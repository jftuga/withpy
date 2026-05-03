"""Decode JWT tokens without signature verification.

Splits a JWT on its dot separators, base64url-decodes the header and
payload segments, and pretty-prints the resulting JSON. Optionally
reports token expiry status from the exp claim.
"""

import argparse
import base64
import datetime
import json
import sys


def _b64url_decode(segment: str) -> bytes:
    """Decode a base64url-encoded segment with padding correction.

    Args:
        segment: The base64url-encoded string.

    Returns:
        The decoded bytes.

    Raises:
        ValueError: If the segment cannot be decoded.
    """
    padding = 4 - len(segment) % 4
    if padding != 4:
        segment += "=" * padding
    try:
        return base64.urlsafe_b64decode(segment)
    except Exception as e:
        raise ValueError(f"invalid base64url segment: {e}") from e


def _format_expiry(payload: dict) -> str | None:
    """Format the expiry status of a JWT payload.

    Args:
        payload: The decoded JWT payload dictionary.

    Returns:
        A human-readable expiry string, or None if no exp claim.
    """
    exp = payload.get("exp")
    if exp is None:
        return None
    try:
        exp_dt = datetime.datetime.fromtimestamp(int(exp), tz=datetime.timezone.utc)
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        diff = exp_dt - now
        if diff.total_seconds() < 0:
            elapsed = abs(diff)
            days = elapsed.days
            hours = elapsed.seconds // 3600
            if days > 0:
                return f"expired {days}d {hours}h ago"
            return f"expired {hours}h {elapsed.seconds % 3600 // 60}m ago"
        else:
            days = diff.days
            hours = diff.seconds // 3600
            if days > 0:
                return f"expires in {days}d {hours}h"
            return f"expires in {hours}h {diff.seconds % 3600 // 60}m"
    except (TypeError, ValueError, OSError):
        return None


def _decode_token(token: str, part: str, raw: bool) -> str:
    """Decode a JWT token and format the output.

    Args:
        token: The JWT string.
        part: Which part to display (header, payload, or all).
        raw: If True, output compact JSON without indentation.

    Returns:
        The formatted output string.

    Raises:
        ValueError: If the token is malformed.
    """
    segments = token.strip().split(".")
    if len(segments) < 2:
        raise ValueError("invalid JWT: expected at least 2 dot-separated segments")
    header_bytes = _b64url_decode(segments[0])
    payload_bytes = _b64url_decode(segments[1])
    try:
        header = json.loads(header_bytes)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JWT header JSON: {e}") from e
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JWT payload JSON: {e}") from e
    indent = None if raw else 2
    lines: list[str] = []
    if part in ("header", "all"):
        if part == "all":
            lines.append("--- Header ---")
        lines.append(json.dumps(header, indent=indent))
    if part in ("payload", "all"):
        if part == "all":
            lines.append("\n--- Payload ---")
        lines.append(json.dumps(payload, indent=indent))
        expiry = _format_expiry(payload)
        if expiry:
            lines.append(f"\n[{expiry}]")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the jwt subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("jwt", help="Decode JWT tokens (no signature verification)")
    p.add_argument("token", nargs="?", default=None, help="JWT string (default: stdin)")
    p.add_argument("--part", "-p", default="payload", choices=["header", "payload", "all"], help="Which part to display (default: payload)")
    p.add_argument("--raw", action="store_true", help="Output compact JSON without indentation")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the jwt subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    if args.token:
        token = args.token
    else:
        token = sys.stdin.read().strip()
    if not token:
        print("error: no JWT token provided", file=sys.stderr)
        return 1
    try:
        output = _decode_token(token, args.part, args.raw)
        print(output)
        return 0
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
