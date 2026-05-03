"""HTTP/HTTPS static file server with optional TLS, gzip, CORS, and auth.

Serves files from a directory using http.server with configurable TLS
support via ssl, gzip compression, CORS headers, basic authentication,
and file upload via POST.
"""

import argparse
import base64
import gzip
import html
import http.server
import mimetypes
import os
import signal
import socketserver
import ssl
import sys
from dataclasses import dataclass


@dataclass
class _ServerConfig:
    """Configuration for the file server handler."""

    auth_credentials: str | None = None
    enable_gzip: bool = False
    enable_cors: bool = False
    enable_upload: bool = False
    quiet: bool = False


def _make_handler(config: _ServerConfig) -> type[http.server.SimpleHTTPRequestHandler]:
    """Create a handler class bound to the given config.

    Args:
        config: Server configuration dataclass.

    Returns:
        A handler class that uses the provided config.
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        """Custom HTTP request handler with gzip, CORS, auth, and upload support."""

        def log_message(self, format: str, *args) -> None:
            """Log an HTTP request message.

            Args:
                format: Printf-style format string.
                *args: Format arguments.
            """
            if not config.quiet:
                super().log_message(format, *args)

        def do_GET(self) -> None:
            """Handle GET requests with optional auth and CORS."""
            if not self._check_auth():
                return
            self._add_cors_headers()
            super().do_GET()

        def do_HEAD(self) -> None:
            """Handle HEAD requests."""
            if not self._check_auth():
                return
            self._add_cors_headers()
            super().do_HEAD()

        def do_POST(self) -> None:
            """Handle POST requests for file upload."""
            if not self._check_auth():
                return
            if not config.enable_upload:
                self.send_error(405, "Upload not enabled")
                return
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            path = self.translate_path(self.path)
            filename = os.path.basename(self.path) or "upload"
            target = os.path.join(os.path.dirname(path), filename)
            with open(target, "wb") as f:
                f.write(body)
            self.send_response(201)
            self._add_cors_headers()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"saved: {filename} ({len(body)} bytes)\n".encode())

        def do_OPTIONS(self) -> None:
            """Handle OPTIONS requests for CORS preflight."""
            self.send_response(200)
            self._add_cors_headers()
            self.end_headers()

        def end_headers(self) -> None:
            """Add gzip encoding and finish headers."""
            if config.enable_gzip:
                accept = self.headers.get("Accept-Encoding", "")
                if "gzip" in accept:
                    self.send_header("Content-Encoding", "gzip")
            super().end_headers()

        def _check_auth(self) -> bool:
            """Verify basic authentication if configured.

            Returns:
                True if auth passes or not configured.
            """
            if config.auth_credentials is None:
                return True
            auth_header = self.headers.get("Authorization", "")
            if not auth_header.startswith("Basic "):
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="withpy"')
                self.end_headers()
                return False
            try:
                decoded = base64.b64decode(auth_header[6:]).decode()
                if decoded == config.auth_credentials:
                    return True
            except (ValueError, UnicodeDecodeError):
                pass
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="withpy"')
            self.end_headers()
            return False

        def _add_cors_headers(self) -> None:
            """Add CORS headers if enabled."""
            if config.enable_cors:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "*")

    return Handler


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the serve subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("serve", help="HTTP/HTTPS static file server")
    p.add_argument("--addr", "-a", default="", help="Bind address (default: all interfaces)")
    p.add_argument("--port", "-p", type=int, default=8000, help="Listen port (default: 8000)")
    p.add_argument("--dir", "-d", default=".", help="Directory to serve (default: .)")
    p.add_argument("--tls-cert", default=None, help="TLS certificate file")
    p.add_argument("--tls-key", default=None, help="TLS private key file")
    p.add_argument("--gzip", action="store_true", help="Enable gzip compression")
    p.add_argument("--cors", action="store_true", help="Enable CORS headers")
    p.add_argument("--auth", default=None, help="Basic auth credentials (user:pass)")
    p.add_argument("--upload", action="store_true", help="Enable file upload via POST")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress access log")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the serve subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    config = _ServerConfig(
        auth_credentials=args.auth,
        enable_gzip=args.gzip,
        enable_cors=args.cors,
        enable_upload=args.upload,
        quiet=args.quiet,
    )
    serve_dir = os.path.abspath(args.dir)
    if not os.path.isdir(serve_dir):
        print(f"error: directory not found: {args.dir}", file=sys.stderr)
        return 1
    os.chdir(serve_dir)
    handler_class = _make_handler(config)
    try:
        server = socketserver.TCPServer((args.addr, args.port), handler_class)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if args.tls_cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            context.load_cert_chain(args.tls_cert, args.tls_key)
        except (ssl.SSLError, OSError) as e:
            print(f"error: TLS setup failed: {e}", file=sys.stderr)
            return 1
        server.socket = context.wrap_socket(server.socket, server_side=True)
    protocol = "https" if args.tls_cert else "http"
    addr_display = args.addr or "0.0.0.0"
    actual_port = server.server_address[1]
    print(f"serving {serve_dir} at {protocol}://{addr_display}:{actual_port}/")
    print("press Ctrl+C to stop")
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.server_close()
    return 0
