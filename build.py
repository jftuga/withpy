"""Bundle withpy source modules into one executable while preserving namespaces.

The generated script loads the bundled Python source into in-memory modules.
Imports, helpers, constants, and the original CLI dispatcher retain their
module scope. Only the standard library is required at build and run time.
"""

import os
import stat
from pathlib import Path

_SRC_DIR = Path("withpy")
_CMD_DIR = _SRC_DIR / "commands"
_OUT_FILE = Path("dist/withpy")

_BOOTSTRAP = '''#!/usr/bin/env python3.14
"""withpy -- batteries-included Swiss-army CLI. Single-file build."""

import sys
import types


def _load_module(name: str, source: str, is_package: bool = False) -> None:
    """Execute bundled source in its own registered module namespace.

    Args:
        name: Fully qualified module name.
        source: Python source bundled at build time.
        is_package: Whether the module is a package.
    """
    module = types.ModuleType(name)
    parent, _, child = name.rpartition(".")
    module.__package__ = name if is_package else parent
    if is_package:
        module.__path__ = []
    sys.modules[name] = module
    if parent:
        setattr(sys.modules[parent], child, module)
    exec(compile(source, f"<bundled {name}>", "exec"), module.__dict__)
'''

_ENTRY_POINT = '''
def main() -> int:
    """Run the bundled CLI dispatcher.

    Returns:
        The command's exit code.
    """
    return sys.modules["withpy.cli"].main()


if __name__ == "__main__":
    sys.exit(main())
'''


def _bundle_module(path: Path, name: str, is_package: bool = False) -> str:
    """Serialize a module without rewriting its source or imports.

    Args:
        path: Source file to bundle.
        name: Fully qualified module name.
        is_package: Whether the module is a package.

    Returns:
        A loader call containing the source as adjacent string literals.
    """
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    lines = "\n".join(f"    {line!r}" for line in source.splitlines(keepends=True))
    if not lines:
        lines = "    ''"
    return f"# --- {name} ---\n_load_module({name!r}, (\n{lines}\n), is_package={is_package!r})"


def build() -> None:
    """Write the self-contained executable with modules in dependency order.

    Raises:
        RuntimeError: If the source directory is missing.
        OSError: If required source files cannot be read or output written.
        SyntaxError: If bundled source cannot be compiled.
    """
    if not _SRC_DIR.is_dir():
        raise RuntimeError(f"source directory not found: {_SRC_DIR}")
    sections = [
        _BOOTSTRAP,
        _bundle_module(_SRC_DIR / "__init__.py", "withpy", is_package=True),
        _bundle_module(_CMD_DIR / "__init__.py", "withpy.commands", is_package=True),
        _bundle_module(_CMD_DIR / "shared.py", "withpy.commands.shared"),
    ]
    for path in sorted(_CMD_DIR.glob("*.py")):
        if path.name not in {"__init__.py", "shared.py"}:
            sections.append(_bundle_module(path, f"withpy.commands.{path.stem}"))
    sections.append(_bundle_module(_SRC_DIR / "cli.py", "withpy.cli"))
    sections.append(_ENTRY_POINT)
    output = "\n\n".join(sections) + "\n"
    compile(output, str(_OUT_FILE), "exec")
    _OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _OUT_FILE.write_text(output, encoding="utf-8")
    if os.name != "nt":
        _OUT_FILE.chmod(_OUT_FILE.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"built {_OUT_FILE} ({_OUT_FILE.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
