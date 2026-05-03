"""Parse and query .netrc files for machine credentials.

Uses the netrc module to safely read .netrc files and extract
login, password, and account information for specific hosts.
"""

import argparse
import json
import netrc
import os
import sys


def _default_netrc_path() -> str:
    """Return the default .netrc file path.

    Returns:
        Path to ~/.netrc.
    """
    return os.path.join(os.path.expanduser("~"), ".netrc")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the netrc subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("netrc", help="Parse/query .netrc files")
    p.add_argument("--mode", "-m", default="lookup", choices=["lookup", "hosts", "dump"], help="Operation mode (default: lookup)")
    p.add_argument("--file", "-f", default=None, help="Path to .netrc file (default: ~/.netrc)")
    p.add_argument("--format", default="text", choices=["text", "json"], help="Output format (default: text)")
    p.add_argument("host", nargs="?", default=None, help="Hostname to look up")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the netrc subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    netrc_path = args.file or _default_netrc_path()
    try:
        nrc = netrc.netrc(netrc_path)
    except FileNotFoundError:
        print(f"error: file not found: {netrc_path}", file=sys.stderr)
        return 1
    except netrc.NetrcParseError as e:
        print(f"error: parse error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    match args.mode:
        case "lookup":
            if not args.host:
                print("error: host argument required for lookup mode", file=sys.stderr)
                return 1
            auth = nrc.authenticators(args.host)
            if auth is None:
                print(f"error: no entry for host: {args.host}", file=sys.stderr)
                return 1
            login, account, password = auth
            if args.format == "json":
                data = {"host": args.host, "login": login or "", "account": account or "", "password": password or ""}
                print(json.dumps(data, indent=2))
            else:
                print(f"host: {args.host}")
                print(f"login: {login or ''}")
                if account:
                    print(f"account: {account}")
                print(f"password: {password or ''}")
            return 0
        case "hosts":
            for host in nrc.hosts:
                print(host)
            return 0
        case "dump":
            data: dict[str, dict[str, str]] = {}
            for host, (login, account, password) in nrc.hosts.items():
                entry: dict[str, str] = {"login": login or ""}
                if account:
                    entry["account"] = account
                entry["password"] = password or ""
                data[host] = entry
            if args.format == "json":
                print(json.dumps(data, indent=2))
            else:
                for host, info in data.items():
                    print(f"machine {host}")
                    for key, val in info.items():
                        print(f"  {key} {val}")
            return 0
    return 0
