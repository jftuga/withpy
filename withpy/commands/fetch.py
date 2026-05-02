"""HTTP client with headers, timing, cookies, and redirect following.

Uses urllib.request to make HTTP/HTTPS requests with support for custom
headers, request bodies, cookie jars, redirect following, and response
timing breakdowns.
"""

import argparse
import http.cookiejar
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def _build_request(url: str, method: str, headers: list[str], data: str | None) -> urllib.request.Request:
    """Build an HTTP request object.

    Args:
        url: Target URL.
        method: HTTP method.
        headers: List of "Name: Value" header strings.
        data: Request body or None.

    Returns:
        Configured Request object.
    """
    body = None
    if data:
        if data.startswith("@"):
            with open(data[1:], "rb") as f:
                body = f.read()
        else:
            body = data.encode()
    req = urllib.request.Request(url, data=body, method=method)
    for h in headers:
        if ":" in h:
            name, value = h.split(":", 1)
            req.add_header(name.strip(), value.strip())
    return req


def _format_timing(elapsed: float) -> str:
    """Format request timing information.

    Args:
        elapsed: Total elapsed time in seconds.

    Returns:
        Formatted timing string.
    """
    if elapsed < 1:
        return f"Total: {elapsed * 1000:.0f}ms"
    return f"Total: {elapsed:.2f}s"


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the fetch subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("fetch", help="HTTP client with headers, timing, cookies")
    p.add_argument("url", help="URL to fetch")
    p.add_argument("--method", "-X", default="GET", choices=["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"], help="HTTP method (default: GET)")
    p.add_argument("--header", "-H", action="append", default=[], help="Request header (Name: Value)")
    p.add_argument("--data", "-d", default=None, help="Request body (or @file)")
    p.add_argument("--output", "-o", default=None, help="Save response body to file")
    p.add_argument("--include", "-i", action="store_true", help="Include response headers in output")
    p.add_argument("--follow", "-L", action="store_true", help="Follow redirects")
    p.add_argument("--max-redirects", type=int, default=10, help="Maximum redirects to follow (default: 10)")
    p.add_argument("--timeout", "-t", type=float, default=30.0, help="Request timeout (default: 30s)")
    p.add_argument("--cookie-jar", default=None, help="Cookie file path (Netscape format)")
    p.add_argument("--timing", action="store_true", help="Show timing information")
    p.add_argument("--verbose", "-v", action="store_true", help="Show request details")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the fetch subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        handlers: list[urllib.request.BaseHandler] = []
        if args.cookie_jar:
            cj = http.cookiejar.MozillaCookieJar(args.cookie_jar)
            try:
                cj.load(ignore_discard=True)
            except (OSError, http.cookiejar.LoadError):
                pass
            handlers.append(urllib.request.HTTPCookieProcessor(cj))
        if not args.follow:
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None
            handlers.append(NoRedirect())
        opener = urllib.request.build_opener(*handlers)
        req = _build_request(args.url, args.method, args.header, args.data)
        if args.verbose:
            print(f"> {args.method} {args.url}", file=sys.stderr)
            for key, val in req.header_items():
                print(f"> {key}: {val}", file=sys.stderr)
            print(file=sys.stderr)
        start = time.time()
        response = opener.open(req, timeout=args.timeout)
        elapsed = time.time() - start
        body = response.read()
        if args.include:
            print(f"HTTP/{response.status} {response.reason}")
            for key, val in response.headers.items():
                print(f"{key}: {val}")
            print()
        if args.output:
            with open(args.output, "wb") as f:
                f.write(body)
            print(f"saved to: {args.output} ({len(body)} bytes)", file=sys.stderr)
        else:
            try:
                sys.stdout.write(body.decode())
            except UnicodeDecodeError:
                sys.stdout.buffer.write(body)
        if args.timing:
            print(f"\n{_format_timing(elapsed)}", file=sys.stderr)
        if args.cookie_jar:
            cj.save(ignore_discard=True)
        return 0
    except urllib.error.HTTPError as e:
        if args.include:
            print(f"HTTP/{e.code} {e.reason}")
            for key, val in e.headers.items():
                print(f"{key}: {val}")
            print()
        body = e.read()
        try:
            sys.stdout.write(body.decode())
        except UnicodeDecodeError:
            sys.stdout.buffer.write(body)
        return 1
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
