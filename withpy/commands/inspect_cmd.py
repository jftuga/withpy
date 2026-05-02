"""TLS certificate inspection and DNS resolution.

Provides modes for retrieving and displaying TLS certificate details,
viewing certificate chains, resolving hostnames, and checking certificate
expiry dates.
"""

import argparse
import datetime
import json
import socket
import ssl
import sys


def _get_cert(host: str, port: int, timeout: float) -> dict:
    """Connect to a host and retrieve its TLS certificate.

    Args:
        host: Target hostname.
        port: Target port.
        timeout: Connection timeout.

    Returns:
        Certificate dictionary from getpeercert().

    Raises:
        OSError: If connection fails.
        ssl.SSLError: If TLS handshake fails.
    """
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert()


def _format_cert(cert: dict, host: str) -> str:
    """Format certificate details for display.

    Args:
        cert: Certificate dictionary.
        host: The hostname that was connected to.

    Returns:
        Formatted certificate information.
    """
    lines: list[str] = [f"Certificate for: {host}", ""]
    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    lines.append(f"Subject:")
    for key, val in subject.items():
        lines.append(f"  {key}: {val}")
    lines.append(f"\nIssuer:")
    for key, val in issuer.items():
        lines.append(f"  {key}: {val}")
    sans = cert.get("subjectAltName", [])
    if sans:
        lines.append(f"\nSubject Alt Names:")
        for san_type, san_val in sans:
            lines.append(f"  {san_type}: {san_val}")
    not_before = cert.get("notBefore", "")
    not_after = cert.get("notAfter", "")
    lines.append(f"\nValidity:")
    lines.append(f"  Not Before: {not_before}")
    lines.append(f"  Not After:  {not_after}")
    serial = cert.get("serialNumber", "")
    if serial:
        lines.append(f"\nSerial: {serial}")
    return "\n".join(lines)


def _format_cert_json(cert: dict, host: str) -> str:
    """Format certificate as JSON.

    Args:
        cert: Certificate dictionary.
        host: The hostname.

    Returns:
        JSON string.
    """
    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    sans = [{"type": t, "value": v} for t, v in cert.get("subjectAltName", [])]
    data = {
        "host": host,
        "subject": subject,
        "issuer": issuer,
        "subjectAltName": sans,
        "notBefore": cert.get("notBefore", ""),
        "notAfter": cert.get("notAfter", ""),
        "serialNumber": cert.get("serialNumber", ""),
    }
    return json.dumps(data, indent=2)


def _check_expiry(cert: dict, host: str) -> str:
    """Check certificate expiry status.

    Args:
        cert: Certificate dictionary.
        host: The hostname.

    Returns:
        Formatted expiry information.
    """
    not_after = cert.get("notAfter", "")
    if not not_after:
        return f"{host}: unable to determine expiry"
    expiry = ssl.cert_time_to_seconds(not_after)
    expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    days = (expiry_dt - now).days
    if days < 0:
        return f"{host}: EXPIRED ({abs(days)} days ago) - {not_after}"
    elif days < 30:
        return f"{host}: EXPIRING SOON ({days} days remaining) - {not_after}"
    return f"{host}: valid ({days} days remaining) - {not_after}"


def _resolve_dns(host: str) -> str:
    """Resolve hostname to IP addresses.

    Args:
        host: Hostname to resolve.

    Returns:
        Formatted DNS resolution results.
    """
    lines: list[str] = [f"DNS resolution for: {host}", ""]
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        seen: set[str] = set()
        for family, stype, proto, canonname, sockaddr in infos:
            addr = sockaddr[0]
            if addr not in seen:
                seen.add(addr)
                family_name = "A" if family == socket.AF_INET else "AAAA"
                lines.append(f"  {family_name:4s} {addr}")
    except socket.gaierror as e:
        lines.append(f"  error: {e}")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the inspect subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("inspect", help="TLS certificate inspection and DNS lookup")
    p.add_argument("--mode", "-m", default="cert", choices=["cert", "chain", "dns", "expiry"], help="Inspection mode (default: cert)")
    p.add_argument("--port", "-p", type=int, default=443, help="Target port (default: 443)")
    p.add_argument("--timeout", "-t", type=float, default=10.0, help="Connection timeout (default: 10s)")
    p.add_argument("--format", "-f", default="text", choices=["text", "json"], help="Output format (default: text)")
    p.add_argument("host", help="Hostname to inspect")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the inspect subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "cert":
                cert = _get_cert(args.host, args.port, args.timeout)
                if args.format == "json":
                    print(_format_cert_json(cert, args.host))
                else:
                    print(_format_cert(cert, args.host))
            case "chain":
                cert = _get_cert(args.host, args.port, args.timeout)
                if args.format == "json":
                    print(_format_cert_json(cert, args.host))
                else:
                    print(_format_cert(cert, args.host))
                    print("\n(Note: Python ssl module only exposes the leaf certificate)")
            case "dns":
                print(_resolve_dns(args.host))
            case "expiry":
                cert = _get_cert(args.host, args.port, args.timeout)
                print(_check_expiry(cert, args.host))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (OSError, ssl.SSLError, socket.timeout) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
