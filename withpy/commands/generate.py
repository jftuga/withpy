"""Generate random UUIDs, tokens, passwords, and byte sequences.

Uses cryptographically secure random sources via the secrets module.
Supports UUID versions 1, 4, and 5 with configurable namespaces.
"""

import argparse
import secrets
import string
import sys
import uuid


_CHARSETS: dict[str, str] = {
    "mixed": string.ascii_letters + string.digits + string.punctuation,
    "alpha": string.ascii_letters,
    "digits": string.digits,
    "hex": string.hexdigits[:16],
    "alphanum": string.ascii_letters + string.digits,
    "symbols": string.punctuation,
}

_UUID_NAMESPACES: dict[str, uuid.UUID] = {
    "dns": uuid.NAMESPACE_DNS,
    "url": uuid.NAMESPACE_URL,
    "oid": uuid.NAMESPACE_OID,
    "x500": uuid.NAMESPACE_X500,
}


def _generate_uuid(version: int, namespace: str | None, name: str | None) -> str:
    """Generate a UUID of the specified version.

    Args:
        version: UUID version (1, 4, or 5).
        namespace: Namespace for UUID5 (dns, url, oid, x500, or raw UUID).
        name: Name string for UUID5.

    Returns:
        The UUID as a string.

    Raises:
        ValueError: If UUID5 is requested without namespace/name or version is invalid.
    """
    match version:
        case 1:
            return str(uuid.uuid1())
        case 4:
            return str(uuid.uuid4())
        case 5:
            if not namespace or not name:
                raise ValueError("UUID5 requires both --namespace and --name")
            if namespace in _UUID_NAMESPACES:
                ns = _UUID_NAMESPACES[namespace]
            else:
                ns = uuid.UUID(namespace)
            return str(uuid.uuid5(ns, name))
        case _:
            raise ValueError(f"unsupported UUID version: {version}")


def _generate_token(length: int, fmt: str) -> str:
    """Generate a random token in the specified format.

    Args:
        length: Desired token length in characters.
        fmt: Format - "hex" for hex characters, "url" for URL-safe base64.

    Returns:
        The generated token string.
    """
    if fmt == "hex":
        return secrets.token_hex(length // 2 + 1)[:length]
    return secrets.token_urlsafe(length)[:length]


def _generate_password(length: int, charset: str) -> str:
    """Generate a random password from the specified character set.

    Args:
        length: Desired password length.
        charset: Name of the character set to use.

    Returns:
        The generated password string.

    Raises:
        ValueError: If the charset name is unknown.
    """
    chars = _CHARSETS.get(charset)
    if chars is None:
        raise ValueError(f"unknown charset: {charset}")
    return "".join(secrets.choice(chars) for _ in range(length))


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the generate subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("generate", help="Generate UUIDs, tokens, and passwords")
    p.add_argument("--mode", "-m", default="uuid", choices=["uuid", "token", "password", "bytes"], help="Generation mode (default: uuid)")
    p.add_argument("--count", "-n", type=int, default=1, help="Number of items to generate (default: 1)")
    p.add_argument("--length", "-l", type=int, default=32, help="Length for tokens/passwords (default: 32)")
    p.add_argument("--charset", default="mixed", choices=list(_CHARSETS.keys()), help="Character set for passwords (default: mixed)")
    p.add_argument("--uuid-version", type=int, default=4, choices=[1, 4, 5], help="UUID version (default: 4)")
    p.add_argument("--namespace", default=None, help="Namespace for UUID5 (dns, url, oid, x500, or UUID string)")
    p.add_argument("--name", default=None, help="Name for UUID5")
    p.add_argument("--format", "-f", default="url", choices=["hex", "url"], help="Token format (default: url)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the generate subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        for _ in range(args.count):
            match args.mode:
                case "uuid":
                    print(_generate_uuid(args.uuid_version, args.namespace, args.name))
                case "token":
                    print(_generate_token(args.length, args.format))
                case "password":
                    print(_generate_password(args.length, args.charset))
                case "bytes":
                    print(secrets.token_hex(args.length))
                case _:
                    print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                    return 1
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
