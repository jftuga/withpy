"""Run command tests against source modules and a freshly built executable."""

import os
import subprocess
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Protocol

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_AMALGAMATED = _ROOT / "dist" / "withpy"


class CliRunner(Protocol):
    """Callable interface for binary subprocess results."""

    def __call__(self, *args: str, input_data: str | bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        """Run a command with optional standard input."""
        ...


def _make_file(root: Path, content: str | bytes, name: str = "input.txt") -> Path:
    """Create a test input file.

    Args:
        root: Temporary directory.
        content: Text or binary file content.
        name: File name within the directory.

    Returns:
        Path to the created file.
    """
    path = root / name
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def tmp_file(tmp_path: Path) -> Callable[..., Path]:
    """Provide a factory for temporary input files."""
    return partial(_make_file, tmp_path)


@pytest.fixture(scope="session")
def built_artifact() -> Path:
    """Build the executable once, failing the session if the build fails."""
    subprocess.run([sys.executable, str(_ROOT / "build.py")], cwd=_ROOT, check=True)
    return _AMALGAMATED


@pytest.fixture(params=("source", "amalgamated"))
def cli_command(request: pytest.FixtureRequest, built_artifact: Path) -> list[str]:
    """Provide both invocation forms to commands and server fixtures."""
    if request.param == "amalgamated":
        return [sys.executable, str(built_artifact)]
    ptool = os.environ.get("PTOOL")
    if ptool:
        return ptool.split()
    return [sys.executable, "-m", "withpy"]


def _run_command(command: list[str], *args: str, input_data: str | bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    """Run a CLI invocation with UTF-8 input and output.

    Args:
        command: Interpreter and script or module arguments.
        *args: Arguments following the executable.
        input_data: Optional data to pass to standard input.

    Returns:
        Completed process with captured binary output.
    """
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    stdin_data = input_data.encode() if isinstance(input_data, str) else input_data
    return subprocess.run(command + list(args), capture_output=True, input=stdin_data, env=env, cwd=_ROOT)


@pytest.fixture
def cli(cli_command: list[str]) -> CliRunner:
    """Provide a runner for each CLI execution form."""
    return partial(_run_command, cli_command)


@pytest.fixture
def amalgamated(built_artifact: Path) -> CliRunner:
    """Provide a runner for the freshly built standalone artifact."""
    return partial(_run_command, [sys.executable, str(built_artifact)])
