"""Cross-command helper utilities for withpy.

Provides common I/O operations used by multiple subcommands: reading input
from files or stdin, formatting byte sizes, and writing output to files
or stdout.
"""

import os
import sys


def read_input(path: str | None) -> bytes:
    """Read binary data from a file path or stdin.

    Args:
        path: File path to read, or None/"-" to read from stdin.

    Returns:
        The raw bytes read from the source.

    Raises:
        OSError: If the file cannot be read.
    """
    if path is None or path == "-":
        return sys.stdin.buffer.read()
    with open(path, "rb") as f:
        return f.read()


def read_input_text(path: str | None) -> str:
    """Read text data from a file path or stdin.

    Args:
        path: File path to read, or None/"-" to read from stdin.

    Returns:
        The text content read from the source.

    Raises:
        OSError: If the file cannot be read.
    """
    if path is None or path == "-":
        return sys.stdin.read()
    with open(path, "r") as f:
        return f.read()


_SIZE_UNITS: list[tuple[int, str]] = [
    (1 << 40, "TB"),
    (1 << 30, "GB"),
    (1 << 20, "MB"),
    (1 << 10, "KB"),
]


def format_size(n: int) -> str:
    """Format a byte count as a human-readable string.

    Args:
        n: Number of bytes.

    Returns:
        A string like "1.5 MB" or "42 B".
    """
    for threshold, unit in _SIZE_UNITS:
        if n >= threshold:
            return f"{n / threshold:.1f} {unit}"
    return f"{n} B"


def write_output(data: str | bytes, path: str | None = None) -> None:
    """Write data to a file or stdout.

    Args:
        data: String or bytes to write.
        path: File path to write to, or None for stdout.

    Raises:
        OSError: If the file cannot be written.
    """
    if path is None:
        if isinstance(data, bytes):
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.write(data)
        return
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)


def get_file_label(path: str) -> str:
    """Return a display label for a file path.

    Args:
        path: File path, or "-" for stdin.

    Returns:
        The basename of the path, or "(stdin)" for stdin.
    """
    if path == "-":
        return "(stdin)"
    return os.path.basename(path)


def read_input_lines(path: str | None) -> list[str]:
    """Read text input and split into non-empty lines.

    Args:
        path: File path to read, or None/"-" to read from stdin.

    Returns:
        A list of non-empty stripped lines.
    """
    text = read_input_text(path)
    return [line for line in text.splitlines() if line.strip()]


def format_duration(seconds: float) -> str:
    """Format seconds as a human-readable duration string.

    Args:
        seconds: Duration in seconds.

    Returns:
        A string like "1.5ms", "3.21s", or "2m 10.3s".
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def error_exit(msg: str) -> int:
    """Print an error message to stderr and return exit code 1.

    Args:
        msg: The error message to display.

    Returns:
        Always returns 1.
    """
    print(f"error: {msg}", file=sys.stderr)
    return 1


def parse_dot_path(path: str) -> list[str | int]:
    """Parse a dot-path string into path components.

    Supports key.subkey[0].field notation. Brackets denote array indices.

    Args:
        path: Dot-separated path string with optional bracket indices.

    Returns:
        List of string keys and integer indices.
    """
    components: list[str | int] = []
    current = ""
    i = 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if current:
                components.append(current)
                current = ""
        elif ch == "[":
            if current:
                components.append(current)
                current = ""
            i += 1
            idx_str = ""
            while i < len(path) and path[i] != "]":
                idx_str += path[i]
                i += 1
            try:
                components.append(int(idx_str))
            except ValueError:
                components.append(idx_str)
        elif ch == "]":
            pass
        else:
            current += ch
        i += 1
    if current:
        components.append(current)
    return components


def query_dot_path(data: object, path: str) -> object:
    """Traverse a nested structure using a dot-path.

    Args:
        data: The parsed data structure.
        path: Dot-path string (e.g. 'key.subkey[0].field').

    Returns:
        The value at the specified path.

    Raises:
        KeyError: If a key is not found.
        IndexError: If an array index is out of range.
        TypeError: If traversal is invalid for the data type.
    """
    components = parse_dot_path(path)
    current = data
    for comp in components:
        if isinstance(comp, int):
            if not isinstance(current, list):
                raise TypeError(f"cannot index non-array with [{comp}]")
            current = current[comp]
        else:
            if not isinstance(current, dict):
                raise TypeError(f"cannot access key '{comp}' on non-object")
            if comp not in current:
                raise KeyError(f"key not found: '{comp}'")
            current = current[comp]
    return current
