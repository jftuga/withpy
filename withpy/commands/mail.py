"""Parse .eml files: extract headers, body, MIME parts, and attachments.

Uses the email.parser module with the modern email.policy to parse
RFC 5322 email messages. Supports header extraction, body display,
MIME part listing, attachment enumeration, and address extraction.
"""

import argparse
import email.parser
import email.policy
import email.utils
import os
import sys


def _parse_message(path: str) -> email.message.EmailMessage:
    """Parse an email message from a file.

    Args:
        path: Path to the .eml file.

    Returns:
        Parsed EmailMessage object.

    Raises:
        OSError: If file cannot be read.
    """
    with open(path, "rb") as f:
        return email.parser.BytesParser(policy=email.policy.default).parse(f)


def _format_headers(msg: email.message.EmailMessage, specific: str | None) -> str:
    """Format message headers for display.

    Args:
        msg: Parsed email message.
        specific: If set, only show this header.

    Returns:
        Formatted header string.
    """
    if specific:
        values = msg.get_all(specific, [])
        return "\n".join(str(v) for v in values) if values else f"(header '{specific}' not found)"
    lines: list[str] = []
    for key in msg.keys():
        lines.append(f"{key}: {msg[key]}")
    return "\n".join(lines)


def _get_body(msg: email.message.EmailMessage) -> str:
    """Extract the text body from an email message.

    Args:
        msg: Parsed email message.

    Returns:
        The plain text body, or HTML body if no plain text available.
    """
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is None:
        return "(no text body found)"
    content = body.get_content()
    if isinstance(content, bytes):
        return content.decode(errors="replace")
    return content


def _list_parts(msg: email.message.EmailMessage) -> str:
    """List all MIME parts in the message.

    Args:
        msg: Parsed email message.

    Returns:
        Formatted parts listing.
    """
    lines: list[str] = []
    for i, part in enumerate(msg.walk()):
        content_type = part.get_content_type()
        size = len(part.get_content() if hasattr(part.get_content(), '__len__') else b"") if not part.is_multipart() else 0
        filename = part.get_filename() or ""
        lines.append(f"{i:3d}  {content_type:<30}  {size:>8} bytes  {filename}")
    return "\n".join(lines)


def _list_attachments(msg: email.message.EmailMessage) -> str:
    """List attachments in the message.

    Args:
        msg: Parsed email message.

    Returns:
        Formatted attachment listing.
    """
    attachments: list[str] = []
    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename() or "(unnamed)"
            try:
                content = part.get_content()
                size = len(content) if isinstance(content, (bytes, str)) else 0
            except (KeyError, LookupError):
                size = 0
            attachments.append(f"  {filename} ({size} bytes)")
    if not attachments:
        return "(no attachments)"
    return "\n".join(attachments)


def _extract_addresses(msg: email.message.EmailMessage) -> str:
    """Extract all email addresses from From, To, CC, BCC headers.

    Args:
        msg: Parsed email message.

    Returns:
        Formatted address list.
    """
    lines: list[str] = []
    for header in ("From", "To", "CC", "BCC", "Reply-To"):
        values = msg.get_all(header, [])
        for val in values:
            addrs = email.utils.getaddresses([str(val)])
            for name, addr in addrs:
                if addr:
                    display = f"{name} <{addr}>" if name else addr
                    lines.append(f"  {header}: {display}")
    if not lines:
        return "(no addresses found)"
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the mail subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("mail", help="Parse .eml files (headers, body, parts, attachments)")
    p.add_argument("--mode", "-m", default="headers", choices=["headers", "body", "parts", "attachments", "addresses"], help="Display mode (default: headers)")
    p.add_argument("--header", default=None, help="Specific header to extract")
    p.add_argument("--save-dir", default=None, help="Directory to save attachments")
    p.add_argument("input", help="Path to .eml file")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the mail subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        msg = _parse_message(args.input)
        match args.mode:
            case "headers":
                print(_format_headers(msg, args.header))
            case "body":
                print(_get_body(msg))
            case "parts":
                print(_list_parts(msg))
            case "attachments":
                if args.save_dir:
                    os.makedirs(args.save_dir, exist_ok=True)
                    saved = 0
                    for part in msg.walk():
                        if part.get_content_disposition() == "attachment":
                            filename = part.get_filename() or f"attachment_{saved}"
                            content = part.get_content()
                            path = os.path.join(args.save_dir, filename)
                            mode = "wb" if isinstance(content, bytes) else "w"
                            with open(path, mode) as f:
                                f.write(content)
                            print(f"  saved: {path}")
                            saved += 1
                    if not saved:
                        print("(no attachments to save)")
                else:
                    print(_list_attachments(msg))
            case "addresses":
                print(_extract_addresses(msg))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
