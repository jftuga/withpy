"""Compute cryptographic and checksum hashes of files or stdin.

Supports hashlib algorithms (MD5 through BLAKE2), HMAC mode, and CRC32/Adler32
via zlib. Output follows the sha256sum two-space-separator convention. A check
mode verifies previously generated checksum files.
"""

import argparse
import hashlib
import hmac
import sys
import zlib

from withpy.commands.shared import read_input

_HASHLIB_ALGOS: set[str] = {
    "md5", "sha1", "sha224", "sha256", "sha384", "sha512",
    "sha3_256", "sha3_512", "blake2b", "blake2s",
}

_CHECKSUM_ALGOS: set[str] = {"crc32", "adler32"}

_ALL_ALGOS: list[str] = sorted(_HASHLIB_ALGOS | _CHECKSUM_ALGOS)

_BUF_SIZE: int = 8192


def _hash_stream_hashlib(stream: object, algo: str, hmac_key: str | None) -> str:
    """Hash a readable binary stream using a hashlib algorithm.

    Args:
        stream: A file-like object with a read() method.
        algo: The hashlib algorithm name.
        hmac_key: Optional HMAC key string, or None for plain hashing.

    Returns:
        The hex digest string.
    """
    if hmac_key is not None:
        h = hmac.new(hmac_key.encode(), digestmod=algo)
    else:
        h = hashlib.new(algo)
    while True:
        chunk = stream.read(_BUF_SIZE)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def _hash_stream_checksum(stream: object, algo: str) -> str:
    """Hash a readable binary stream using zlib CRC32 or Adler32.

    Args:
        stream: A file-like object with a read() method.
        algo: Either "crc32" or "adler32".

    Returns:
        The checksum as an 8-character zero-padded hex string.
    """
    func = zlib.crc32 if algo == "crc32" else zlib.adler32
    value = 1 if algo == "adler32" else 0
    while True:
        chunk = stream.read(_BUF_SIZE)
        if not chunk:
            break
        value = func(chunk, value)
    return f"{value & 0xFFFFFFFF:08x}"


def _hash_file(path: str, algo: str, hmac_key: str | None) -> str:
    """Compute the hash of a file or stdin.

    Args:
        path: File path, or "-" for stdin.
        algo: Algorithm name.
        hmac_key: Optional HMAC key, or None.

    Returns:
        The hex digest string.

    Raises:
        ValueError: If HMAC is requested with a checksum algorithm.
        OSError: If the file cannot be opened.
    """
    if hmac_key is not None and algo in _CHECKSUM_ALGOS:
        raise ValueError(f"HMAC is not supported with {algo}")
    if path == "-":
        stream = sys.stdin.buffer
    else:
        stream = open(path, "rb")
    try:
        if algo in _CHECKSUM_ALGOS:
            return _hash_stream_checksum(stream, algo)
        return _hash_stream_hashlib(stream, algo, hmac_key)
    finally:
        if path != "-":
            stream.close()


def _check_file(check_path: str, algo: str) -> int:
    """Verify hashes from a checksum file.

    Args:
        check_path: Path to the checksum file.
        algo: Algorithm to use for verification.

    Returns:
        0 if all hashes match, 1 if any fail.
    """
    failures = 0
    with open(check_path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2:
                print(f"malformed line: {line}", file=sys.stderr)
                failures += 1
                continue
            expected_hash, file_path = parts
            try:
                actual_hash = _hash_file(file_path, algo, None)
            except OSError as e:
                print(f"{file_path}: FAILED ({e})", file=sys.stderr)
                failures += 1
                continue
            if actual_hash == expected_hash:
                print(f"{file_path}: OK")
            else:
                print(f"{file_path}: FAILED")
                failures += 1
    return 1 if failures else 0


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the hash subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("hash", help="Compute file hashes (MD5, SHA, CRC32, ...)")
    p.add_argument("--algo", "-a", default="sha256", choices=_ALL_ALGOS, help="Hash algorithm (default: sha256)")
    p.add_argument("--hmac", metavar="KEY", default=None, help="Use HMAC with the given key")
    p.add_argument("--check", "-c", metavar="FILE", default=None, help="Verify hashes from a checksum file")
    p.add_argument("files", nargs="*", default=["-"], help="Files to hash (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the hash subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    if args.check:
        return _check_file(args.check, args.algo)
    for path in args.files:
        try:
            digest = _hash_file(path, args.algo, args.hmac)
        except (OSError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        label = "(stdin)" if path == "-" else path
        print(f"{digest}  {label}")
    return 0
