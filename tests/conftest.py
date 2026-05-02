"""Shared pytest fixtures for withpy tests.

Provides factory fixtures for temporary files and runner helpers that invoke
withpy via subprocess in both module and amalgamated modes.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tmp_file(tmp_path: Path):
    """Factory fixture that creates a temporary file with given content.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        A callable that takes content (str or bytes) and returns the file Path.
    """
    def _make(content: str | bytes, name: str = "input.txt") -> Path:
        """Create a temp file with the given content.

        Args:
            content: File content as str or bytes.
            name: Filename to use.

        Returns:
            Path to the created file.
        """
        p = tmp_path / name
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content)
        return p
    return _make


def _make_env() -> dict[str, str]:
    """Create subprocess environment with UTF-8 mode enabled.

    Returns:
        Copy of current environment with PYTHONUTF8=1.
    """
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return env


def _run_command(*args: str, input_data: str | bytes | None = None) -> subprocess.CompletedProcess:
    """Run withpy via python -m, or via PTOOL if set.

    Args:
        *args: Command-line arguments after 'withpy'.
        input_data: Optional data to pass to stdin.

    Returns:
        The completed subprocess result.
    """
    ptool = os.environ.get("PTOOL")
    if ptool:
        cmd = ptool.split() + list(args)
    else:
        cmd = [sys.executable, "-m", "withpy"] + list(args)
    stdin_data = None
    if input_data is not None:
        stdin_data = input_data if isinstance(input_data, bytes) else input_data.encode()
    return subprocess.run(cmd, capture_output=True, input=stdin_data, env=_make_env())


@pytest.fixture
def cli():
    """Fixture providing a callable to run withpy commands.

    Returns:
        The _run_command helper function.
    """
    return _run_command


_AMALGAMATED = Path("dist/withpy")


def _run_amalgamated(*args: str, input_data: str | bytes | None = None) -> subprocess.CompletedProcess:
    """Run the amalgamated dist/withpy artifact.

    Args:
        *args: Command-line arguments after 'withpy'.
        input_data: Optional data to pass to stdin.

    Returns:
        The completed subprocess result.
    """
    cmd = [sys.executable, str(_AMALGAMATED)] + list(args)
    stdin_data = None
    if input_data is not None:
        stdin_data = input_data if isinstance(input_data, bytes) else input_data.encode()
    return subprocess.run(cmd, capture_output=True, input=stdin_data, env=_make_env())


@pytest.fixture
def amalgamated():
    """Fixture providing a callable to run the amalgamated artifact.

    Returns:
        The _run_amalgamated helper function.

    Raises:
        pytest.skip: If the amalgamated artifact does not exist.
    """
    if not _AMALGAMATED.exists():
        pytest.skip("amalgamated artifact not built")
    return _run_amalgamated
