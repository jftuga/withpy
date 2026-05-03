"""Create, extract, and list tar and zip archives.

Supports zip, tar, tar.gz, tar.bz2, and tar.xz formats with automatic
format detection from file extensions or magic bytes. Includes path
traversal protection on extraction.
"""

import argparse
import os
import sys
import tarfile
import zipfile


_FORMAT_EXTENSIONS: dict[str, str] = {
    ".zip": "zip",
    ".tar": "tar",
    ".tar.gz": "tar.gz",
    ".tgz": "tar.gz",
    ".tar.bz2": "tar.bz2",
    ".tbz2": "tar.bz2",
    ".tar.xz": "tar.xz",
    ".txz": "tar.xz",
}

_TAR_MODES: dict[str, str] = {
    "tar": "w",
    "tar.gz": "w:gz",
    "tar.bz2": "w:bz2",
    "tar.xz": "w:xz",
}

_TAR_READ_MODES: dict[str, str] = {
    "tar": "r:",
    "tar.gz": "r:gz",
    "tar.bz2": "r:bz2",
    "tar.xz": "r:xz",
}


def _detect_format(path: str) -> str:
    """Detect archive format from file extension.

    Args:
        path: Archive file path.

    Returns:
        Format string.

    Raises:
        ValueError: If format cannot be determined.
    """
    lower = path.lower()
    for ext, fmt in _FORMAT_EXTENSIONS.items():
        if lower.endswith(ext):
            return fmt
    raise ValueError(f"cannot determine archive format from: {path}")


def _is_safe_path(path: str, base: str) -> bool:
    """Check if an archive member path is safe to extract.

    Args:
        path: The member path from the archive.
        base: The target extraction directory.

    Returns:
        True if the path is safe (no traversal).
    """
    resolved = os.path.realpath(os.path.join(base, path))
    return resolved.startswith(os.path.realpath(base))


def _strip_components(path: str, strip: int) -> str:
    """Strip leading path components.

    Args:
        path: Original path.
        strip: Number of components to strip.

    Returns:
        Path with leading components removed.
    """
    parts = path.split("/")
    if len(parts) <= strip:
        return ""
    return "/".join(parts[strip:])


def _create_archive(files: list[str], output: str, fmt: str) -> None:
    """Create an archive from the given files.

    Args:
        files: List of file/directory paths to archive.
        output: Output archive path.
        fmt: Archive format.

    Raises:
        ValueError: If format is invalid or no files given.
        OSError: If files cannot be read.
    """
    if not files:
        raise ValueError("no files specified for archiving")
    if fmt == "zip":
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in files:
                if os.path.isdir(path):
                    for root, dirs, filenames in os.walk(path):
                        for fname in filenames:
                            full = os.path.join(root, fname)
                            arcname = os.path.relpath(full, os.path.dirname(path))
                            zf.write(full, arcname)
                else:
                    zf.write(path, os.path.basename(path))
    else:
        mode = _TAR_MODES.get(fmt)
        if mode is None:
            raise ValueError(f"unsupported tar format: {fmt}")
        with tarfile.open(output, mode) as tf:
            for path in files:
                tf.add(path, arcname=os.path.basename(path))


def _extract_archive(archive: str, output: str, fmt: str, strip: int) -> None:
    """Extract an archive to the given directory.

    Args:
        archive: Archive file path.
        output: Target directory.
        fmt: Archive format.
        strip: Number of leading path components to strip.

    Raises:
        ValueError: If format is unsupported or paths are unsafe.
        OSError: If archive cannot be read.
    """
    os.makedirs(output, exist_ok=True)
    if fmt == "zip":
        with zipfile.ZipFile(archive, "r") as zf:
            for info in zf.infolist():
                member_path = _strip_components(info.filename, strip) if strip else info.filename
                if not member_path:
                    continue
                if not _is_safe_path(member_path, output):
                    raise ValueError(f"unsafe path in archive: {info.filename}")
                target = os.path.join(output, member_path)
                if info.is_dir():
                    os.makedirs(target, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with zf.open(info) as src, open(target, "wb") as dst:
                        dst.write(src.read())
    else:
        mode = _TAR_READ_MODES.get(fmt, "r:*")
        with tarfile.open(archive, mode) as tf:
            for member in tf.getmembers():
                member_path = _strip_components(member.name, strip) if strip else member.name
                if not member_path:
                    continue
                if not _is_safe_path(member_path, output):
                    raise ValueError(f"unsafe path in archive: {member.name}")
                member.name = member_path
                tf.extract(member, output, filter="data")


def _list_archive(archive: str, fmt: str) -> list[str]:
    """List archive contents.

    Args:
        archive: Archive file path.
        fmt: Archive format.

    Returns:
        List of formatted entries (name and size).
    """
    entries: list[str] = []
    if fmt == "zip":
        with zipfile.ZipFile(archive, "r") as zf:
            for info in zf.infolist():
                size = info.file_size
                entries.append(f"{size:>10}  {info.filename}")
    else:
        mode = _TAR_READ_MODES.get(fmt, "r:*")
        with tarfile.open(archive, mode) as tf:
            for member in tf.getmembers():
                entries.append(f"{member.size:>10}  {member.name}")
    return entries


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the archive subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("archive", help="Create/extract/list tar and zip archives")
    p.add_argument("--mode", "-m", default="create", choices=["create", "extract", "list"], help="Operation mode (default: create)")
    p.add_argument("--format", "-f", default="auto", choices=["auto", "zip", "tar", "tar.gz", "tar.bz2", "tar.xz"], help="Archive format (default: auto-detect)")
    p.add_argument("--output", "-o", default=None, help="Output path (archive for create, directory for extract)")
    p.add_argument("--strip", type=int, default=0, help="Strip N leading path components on extract")
    p.add_argument("archive", nargs="?", default=None, help="Archive file path")
    p.add_argument("files", nargs="*", help="Files/directories to archive (create mode)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the archive subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "create":
                output = args.output or args.archive
                if not output:
                    print("error: output path required (--output or positional archive)", file=sys.stderr)
                    return 1
                fmt = args.format
                if fmt == "auto":
                    fmt = _detect_format(output)
                files = args.files
                if not files and args.archive and args.archive != output:
                    files = [args.archive]
                _create_archive(files, output, fmt)
                return 0
            case "extract":
                if not args.archive:
                    print("error: archive path required", file=sys.stderr)
                    return 1
                fmt = args.format
                if fmt == "auto":
                    fmt = _detect_format(args.archive)
                output = args.output or "."
                _extract_archive(args.archive, output, fmt, args.strip)
                return 0
            case "list":
                if not args.archive:
                    print("error: archive path required", file=sys.stderr)
                    return 1
                fmt = args.format
                if fmt == "auto":
                    fmt = _detect_format(args.archive)
                entries = _list_archive(args.archive, fmt)
                for entry in entries:
                    print(entry)
                return 0
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
    except (ValueError, OSError, tarfile.TarError, zipfile.BadZipFile) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
