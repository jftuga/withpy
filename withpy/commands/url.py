"""Parse, build, encode, and decode URLs and query strings.

Provides modes for decomposing URLs into components, constructing URLs
from parts, percent-encoding/decoding strings, and parsing query
parameters into key-value pairs.
"""

import argparse
import json
import sys
import urllib.parse

from withpy.commands.shared import read_input_text


def _parse_url(url_str: str, output_format: str) -> str:
    """Parse a URL into its components.

    Args:
        url_str: The URL string to parse.
        output_format: Output format ("text" or "json").

    Returns:
        Formatted string of URL components.
    """
    parsed = urllib.parse.urlparse(url_str)
    components = {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "port": parsed.port,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "username": parsed.username or "",
        "password": parsed.password or "",
    }
    if output_format == "json":
        return json.dumps(components, indent=2)
    lines: list[str] = []
    for key, value in components.items():
        if value:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _build_url(scheme: str | None, host: str | None, port: int | None, path: str | None, query: str | None, fragment: str | None) -> str:
    """Build a URL from individual components.

    Args:
        scheme: URL scheme (e.g. "https").
        host: Hostname.
        port: Port number or None.
        path: URL path.
        query: Query string.
        fragment: Fragment identifier.

    Returns:
        The constructed URL string.
    """
    netloc = host or ""
    if port:
        netloc = f"{netloc}:{port}"
    return urllib.parse.urlunparse((
        scheme or "",
        netloc,
        path or "",
        "",
        query or "",
        fragment or "",
    ))


def _parse_params(url_str: str) -> str:
    """Extract and format query parameters from a URL.

    Args:
        url_str: URL string or bare query string.

    Returns:
        Formatted key=value pairs, one per line.
    """
    if "?" in url_str:
        query = urllib.parse.urlparse(url_str).query
    else:
        query = url_str
    params = urllib.parse.parse_qs(query, keep_blank_values=True)
    lines: list[str] = []
    for key, values in params.items():
        for val in values:
            lines.append(f"{key}={val}")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the url subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("url", help="Parse, build, encode/decode URLs")
    p.add_argument("--mode", "-m", default="parse", choices=["parse", "build", "encode", "decode", "params"], help="Operation mode (default: parse)")
    p.add_argument("--scheme", default=None, help="URL scheme for build mode")
    p.add_argument("--host", default=None, help="Hostname for build mode")
    p.add_argument("--port", type=int, default=None, help="Port for build mode")
    p.add_argument("--path", default=None, help="Path for build mode")
    p.add_argument("--query", default=None, help="Query string for build mode")
    p.add_argument("--fragment", default=None, help="Fragment for build mode")
    p.add_argument("--format", "-f", default="text", choices=["text", "json"], help="Output format (default: text)")
    p.add_argument("value", nargs="?", default=None, help="URL string or value to encode/decode")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the url subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "parse":
                value = args.value or read_input_text(None).strip()
                if not value:
                    print("error: no URL provided", file=sys.stderr)
                    return 1
                print(_parse_url(value, args.format))
            case "build":
                url = _build_url(args.scheme, args.host, args.port, args.path, args.query, args.fragment)
                print(url)
            case "encode":
                value = args.value or read_input_text(None).strip()
                print(urllib.parse.quote_plus(value))
            case "decode":
                value = args.value or read_input_text(None).strip()
                print(urllib.parse.unquote_plus(value))
            case "params":
                value = args.value or read_input_text(None).strip()
                if not value:
                    print("error: no URL provided", file=sys.stderr)
                    return 1
                print(_parse_params(value))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
