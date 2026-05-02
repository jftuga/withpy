"""Create and inspect Python ZIP application archives (.pyz files).

Uses the zipapp module to create executable Python archives from
directories, inspect existing archives, and extract their contents.
"""

import argparse
import os
import sys
import zipapp
import zipfile


def _create_archive(source: str, output: str, interpreter: str | None, main: str | None, compressed: bool) -> None:
    """Create a .pyz archive from a source directory.

    Args:
        source: Source directory path.
        output: Output .pyz file path.
        interpreter: Python interpreter for shebang line.
        main: Main function specification (e.g. 'pkg.mod:func').
        compressed: Whether to compress the archive.
    """
    zipapp.create_archive(source, target=output, interpreter=interpreter, main=main, compressed=compressed)


def _info(path: str) -> dict[str, str]:
    """Get information about a .pyz archive.

    Args:
        path: Path to the .pyz archive.

    Returns:
        Dictionary of archive metadata.
    """
    info: dict[str, str] = {}
    with open(path, "rb") as f:
        first_line = f.readline()
        if first_line.startswith(b"#!"):
            info["interpreter"] = first_line.decode().strip()[2:]
        else:
            info["interpreter"] = "none"
    info["size_bytes"] = str(os.path.getsize(path))
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        info["entries"] = str(len(names))
        if "__main__.py" in names:
            info["has_main"] = "yes"
            content = zf.read("__main__.py").decode(errors="replace")
            first_lines = content.splitlines()[:5]
            info["main_preview"] = "; ".join(first_lines)
        else:
            info["has_main"] = "no"
    return info


def _list_contents(path: str) -> list[str]:
    """List contents of a .pyz archive.

    Args:
        path: Path to the .pyz archive.

    Returns:
        List of file names in the archive.
    """
    with zipfile.ZipFile(path, "r") as zf:
        return zf.namelist()


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the zipapp subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("zipapp", help="Create/inspect Python ZIP application archives")
    p.add_argument("--mode", "-m", default="create", choices=["create", "info", "list"], help="Operation mode (default: create)")
    p.add_argument("--output", "-o", default=None, help="Output file for create mode")
    p.add_argument("--interpreter", "-i", default=None, help="Python interpreter for shebang")
    p.add_argument("--main", default=None, help="Main function (pkg.mod:func)")
    p.add_argument("--compressed", "-c", action="store_true", help="Compress the archive")
    p.add_argument("source", help="Source directory (create) or .pyz file (info/list)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the zipapp subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "create":
                if not os.path.isdir(args.source):
                    print(f"error: not a directory: {args.source}", file=sys.stderr)
                    return 1
                output = args.output or (args.source.rstrip("/") + ".pyz")
                _create_archive(args.source, output, args.interpreter, args.main, args.compressed)
                print(f"created: {output} ({os.path.getsize(output)} bytes)")
            case "info":
                if not os.path.isfile(args.source):
                    print(f"error: file not found: {args.source}", file=sys.stderr)
                    return 1
                info = _info(args.source)
                for key, val in info.items():
                    print(f"{key}: {val}")
            case "list":
                if not os.path.isfile(args.source):
                    print(f"error: file not found: {args.source}", file=sys.stderr)
                    return 1
                for name in _list_contents(args.source):
                    print(name)
        return 0
    except (zipfile.BadZipFile, zipapp.ZipAppError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
