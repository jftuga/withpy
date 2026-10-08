"""Regression tests for module isolation in the single-file builder."""

import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def test_module_isolation(tmp_path: Path) -> None:
    """Preserve helpers, constants, import aliases, dataclasses, and CLI logic."""
    root = Path(__file__).resolve().parents[1]
    shutil.copy2(root / "build.py", tmp_path / "build.py")
    sources = {
        "withpy/__init__.py": '__version__ = "test"\n',
        "withpy/commands/__init__.py": '',
        "withpy/commands/shared.py": '''
            """Shared helper with a deliberately duplicated constant."""
            _VALUE = "shared"

            def value() -> str:
                """Return the shared module's own constant."""
                return _VALUE
        ''',
        "withpy/commands/alpha.py": '''
            """First command with helpers and aliases duplicated by beta."""
            import math as dependency
            from dataclasses import dataclass
            from withpy.commands.shared import value

            _VALUE = "alpha"

            @dataclass
            class Record:
                """A record whose module must be registered before execution."""
                label: str

            def _helper() -> str:
                """Resolve this module's constant and import alias."""
                return f"{_VALUE}:{dependency.sqrt(9)}:{value()}:{Record('ok').label}"
        ''',
        "withpy/commands/beta.py": '''
            """Second command whose globals must not replace alpha's."""
            import statistics as dependency
            _VALUE = "beta"

            def _helper() -> str:
                """Resolve this module's constant and import alias."""
                return f"{_VALUE}:{dependency.mean([2, 4])}"
        ''',
        "withpy/cli.py": '''
            """Dispatcher that must be bundled unchanged."""
            import withpy
            from withpy.commands import alpha, beta

            def main() -> int:
                """Print independently resolved module values."""
                print(withpy.__version__, alpha._helper(), beta._helper())
                return 0
        ''',
    }
    for name, source in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(source), encoding="utf-8")
    subprocess.run([sys.executable, "build.py"], cwd=tmp_path, check=True, capture_output=True)
    artifact = tmp_path / "dist" / "withpy"
    original = artifact.read_bytes()
    subprocess.run([sys.executable, "build.py"], cwd=tmp_path, check=True, capture_output=True)
    assert artifact.read_bytes() == original
    shutil.rmtree(tmp_path / "withpy")
    result = subprocess.run([sys.executable, "-I", str(artifact)], cwd=tmp_path, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.strip() == b"test alpha:3.0:shared:ok beta:3"
