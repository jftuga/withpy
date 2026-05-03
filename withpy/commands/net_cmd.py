"""TCP networking utilities: port check, scan, echo server, wait-for-port.

Provides modes for checking if a TCP port is open, scanning port ranges
with concurrent connections, running a simple echo server, waiting for
a port to become available, and DNS resolution.
"""

import argparse
import concurrent.futures
import selectors
import socket
import sys
import time


def _check_port(host: str, port: int, timeout: float) -> bool:
    """Check if a TCP port is open.

    Args:
        host: Target hostname.
        port: Target port.
        timeout: Connection timeout in seconds.

    Returns:
        True if port is open, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (OSError, socket.timeout):
        return False


def _scan_ports(host: str, start: int, end: int, timeout: float, concurrency: int) -> list[int]:
    """Scan a range of TCP ports concurrently.

    Args:
        host: Target hostname.
        start: Start port (inclusive).
        end: End port (inclusive).
        timeout: Per-connection timeout.
        concurrency: Maximum concurrent connections.

    Returns:
        Sorted list of open ports.
    """
    open_ports: list[int] = []

    def check(port: int) -> tuple[int, bool]:
        return (port, _check_port(host, port, timeout))

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(check, p) for p in range(start, end + 1)]
        for future in concurrent.futures.as_completed(futures):
            port, is_open = future.result()
            if is_open:
                open_ports.append(port)
    return sorted(open_ports)


def _echo_server(host: str, port: int) -> None:
    """Run a TCP echo server using selectors for non-blocking I/O.

    Args:
        host: Bind address.
        port: Bind port.
    """
    sel = selectors.DefaultSelector()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    server.setblocking(False)
    sel.register(server, selectors.EVENT_READ)
    actual_port = server.getsockname()[1]
    print(f"echo server listening on {host}:{actual_port}", flush=True)

    def _accept(sock: socket.socket) -> None:
        conn, addr = sock.accept()
        conn.setblocking(False)
        sel.register(conn, selectors.EVENT_READ)

    def _echo(conn: socket.socket) -> None:
        try:
            data = conn.recv(4096)
            if data:
                conn.sendall(data)
            else:
                sel.unregister(conn)
                conn.close()
        except (OSError, ConnectionError):
            sel.unregister(conn)
            conn.close()

    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                if key.fileobj is server:
                    _accept(key.fileobj)
                else:
                    _echo(key.fileobj)
    except KeyboardInterrupt:
        pass
    finally:
        sel.unregister(server)
        server.close()
        sel.close()
        print("\necho server stopped")


def _wait_for_port(host: str, port: int, timeout: float, poll_interval: float) -> bool:
    """Wait for a TCP port to become available.

    Args:
        host: Target hostname.
        port: Target port.
        timeout: Maximum wait time in seconds.
        poll_interval: Seconds between attempts.

    Returns:
        True if port became available, False if timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _check_port(host, port, min(poll_interval, 1.0)):
            return True
        time.sleep(poll_interval)
    return False


def _resolve_host(host: str) -> str:
    """Resolve a hostname to IP addresses.

    Args:
        host: Hostname to resolve.

    Returns:
        Formatted resolution results.
    """
    results: list[str] = []
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        seen: set[str] = set()
        for family, stype, proto, canonname, sockaddr in infos:
            addr = sockaddr[0]
            if addr not in seen:
                seen.add(addr)
                family_name = "IPv4" if family == socket.AF_INET else "IPv6"
                results.append(f"  {family_name}: {addr}")
    except socket.gaierror as e:
        return f"error resolving {host}: {e}"
    if not results:
        return f"no results for {host}"
    return f"{host}:\n" + "\n".join(results)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the net subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("net", help="TCP port check, scan, echo server, wait-for-port")
    p.add_argument("--mode", "-m", default="check", choices=["check", "scan", "echo", "wait", "resolve"], help="Operation mode (default: check)")
    p.add_argument("--host", "-H", default="localhost", help="Target host (default: localhost)")
    p.add_argument("--port", "-p", type=int, default=None, help="Target port")
    p.add_argument("--ports", default=None, help="Port range for scan (e.g. 80-443)")
    p.add_argument("--timeout", "-t", type=float, default=2.0, help="Connection timeout (default: 2.0s)")
    p.add_argument("--concurrency", "-c", type=int, default=50, help="Max concurrent connections (default: 50)")
    p.add_argument("--wait-timeout", type=float, default=30.0, help="Total wait time for wait mode (default: 30s)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the net subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "check":
                if args.port is None:
                    print("error: --port required for check mode", file=sys.stderr)
                    return 1
                is_open = _check_port(args.host, args.port, args.timeout)
                status = "open" if is_open else "closed"
                print(f"{args.host}:{args.port} is {status}")
                return 0 if is_open else 1
            case "scan":
                if not args.ports:
                    print("error: --ports required for scan mode (e.g. 80-443)", file=sys.stderr)
                    return 1
                parts = args.ports.split("-")
                if len(parts) != 2:
                    print("error: --ports must be in format START-END", file=sys.stderr)
                    return 1
                start, end = int(parts[0]), int(parts[1])
                open_ports = _scan_ports(args.host, start, end, args.timeout, args.concurrency)
                if open_ports:
                    print(f"Open ports on {args.host}:")
                    for p in open_ports:
                        print(f"  {p}")
                else:
                    print(f"No open ports found on {args.host} ({start}-{end})")
                return 0
            case "echo":
                port = args.port or 0
                _echo_server(args.host, port)
                return 0
            case "wait":
                if args.port is None:
                    print("error: --port required for wait mode", file=sys.stderr)
                    return 1
                success = _wait_for_port(args.host, args.port, args.wait_timeout, 0.5)
                if success:
                    print(f"{args.host}:{args.port} is available")
                    return 0
                print(f"timeout: {args.host}:{args.port} not available after {args.wait_timeout}s", file=sys.stderr)
                return 1
            case "resolve":
                print(_resolve_host(args.host))
                return 0
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
