"""Regression tests for readable amalgamation and global-name collisions."""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from build import _validate_global_names


@pytest.fixture
def build_tree(tmp_path: Path) -> Path:
    """Copy build inputs to an isolated directory for integration tests."""
    root = Path(__file__).resolve().parents[1]
    shutil.copy2(root / "build.py", tmp_path / "build.py")
    shutil.copytree(root / "withpy", tmp_path / "withpy", ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path


@pytest.mark.parametrize("first,second", [
    ('def _duplicate() -> int:\n    """Return one."""\n    return 1\n', 'def _duplicate() -> int:\n    """Return two."""\n    return 2\n'),
    ('_duplicate: int = 1\n', '_duplicate = 2\n'),
    ('import math as _duplicate\n', 'import statistics as _duplicate\n'),
    ('class _duplicate:\n    """First class."""\n', 'class _duplicate:\n    """Second class."""\n'),
])
def test_build_rejects_collisions(build_tree: Path, first: str, second: str) -> None:
    """Reject conflicting module globals before producing an executable."""
    for filename, extra in [('archive.py', first), ('compress.py', second)]:
        path = build_tree / "withpy" / "commands" / filename
        path.write_text(path.read_text(encoding="utf-8") + "\n" + extra, encoding="utf-8")
    result = subprocess.run([sys.executable, "build.py"], cwd=build_tree, capture_output=True)
    assert result.returncode != 0
    assert b"global name collision for '_duplicate'" in result.stderr
    assert not (build_tree / "dist" / "withpy").exists()


@pytest.mark.parametrize("source", [
    'import math\nmath = 1\n',
    'import math as dependency\nfrom statistics import mean as dependency\n',
    'a, b = 1, 2\nb = 3\n',
    'type Value = int\ntype Value = str\n',
])
def test_other_global_collisions(source: str) -> None:
    """Catch import shadowing, destructured assignments, and type aliases."""
    with pytest.raises(ValueError, match="global name collision"):
        _validate_global_names(source)


def test_compatible_imports_and_local_names() -> None:
    """Allow compatible dotted imports and independent function locals."""
    _validate_global_names('''import urllib.request
import urllib.parse
import math
import math

def first() -> int:
    """Use a local name."""
    value = 1
    return value


def second() -> int:
    """Reuse the local name in a separate scope."""
    value = 2
    return value
''')


def test_wildcard_import_rejected() -> None:
    """Require explicit imports so global bindings can be checked."""
    with pytest.raises(ValueError, match="wildcard imports"):
        _validate_global_names('from math import *\n')


def test_readable_deterministic_build(build_tree: Path) -> None:
    """Keep imports at the top, ordinary definitions, and standalone execution."""
    subprocess.run([sys.executable, "build.py"], cwd=build_tree, check=True, capture_output=True)
    artifact = build_tree / "dist" / "withpy"
    original = artifact.read_bytes()
    subprocess.run([sys.executable, "build.py"], cwd=build_tree, check=True, capture_output=True)
    assert artifact.read_bytes() == original
    tree = ast.parse(original)
    imports_finished = False
    imports: set[str] = set()
    definitions: set[str] = set()
    for node in tree.body[1:]:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            assert not imports_finished, "imports should appear before definitions"
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
        else:
            imports_finished = True
        if isinstance(node, ast.FunctionDef):
            definitions.add(node.name)
    assert {"argparse", "csv", "json", "statistics", "tarfile", "zipfile"} <= imports
    assert {"_archive_create", "_calc_compute_stats", "_db_format_csv_output", "main"} <= definitions
    assert b"_load_module" not in original
    shutil.rmtree(build_tree / "withpy")
    result = subprocess.run([sys.executable, "-I", str(artifact), "calc", "--mode", "stats", "1", "2", "3"], cwd=build_tree, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert b"mean:   2.0" in result.stdout
