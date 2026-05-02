"""Amalgamator for withpy: combines multi-file source into a single executable script.

Scans withpy/cli.py and withpy/commands/*.py, deduplicates imports, inlines
shared.py first then command modules with renamed register/run functions,
and emits a self-contained dist/withpy script. Uses only the standard library.
"""

import ast
import os
import re
import stat
import sys
from pathlib import Path

_SRC_DIR = Path("withpy")
_CMD_DIR = _SRC_DIR / "commands"
_OUT_DIR = Path("dist")
_OUT_FILE = _OUT_DIR / "withpy"

_SHEBANG = "#!/usr/bin/env python3"

_INTERNAL_PREFIXES: tuple[str, ...] = ("withpy.", "withpy ", "commands.", "commands ")


def _is_internal_import(node: ast.stmt) -> bool:
    """Check if an AST import node refers to an internal withpy module.

    Args:
        node: An ast.Import or ast.ImportFrom node.

    Returns:
        True if the import is internal and should be stripped.
    """
    if isinstance(node, ast.ImportFrom):
        if node.module and any(node.module.startswith(p.rstrip()) for p in ("withpy", "commands")):
            return True
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith("withpy"):
                return True
    return False


def _extract_imports(source: str) -> list[str]:
    """Extract stdlib import lines from source code.

    Args:
        source: Python source code string.

    Returns:
        List of import statement strings, excluding internal imports.
    """
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if _is_internal_import(node):
                continue
            imports.append(ast.get_source_segment(source, node) or "")
    return [imp for imp in imports if imp]


def _strip_imports_and_docstring(source: str) -> str:
    """Remove import statements, module docstrings, and if-main blocks from source.

    Args:
        source: Python source code string.

    Returns:
        Source with imports, module docstring, and if-main removed.
    """
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    regions_to_remove: list[tuple[int, int]] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            regions_to_remove.append((node.lineno, node.end_lineno or node.lineno))
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name) and test.left.id == "__name__"):
                regions_to_remove.append((node.lineno, node.end_lineno or node.lineno))
    first_node = None
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            first_node = node
            break
    if first_node and isinstance(first_node, ast.Expr) and isinstance(first_node.value, ast.Constant):
        regions_to_remove.append((first_node.lineno, first_node.end_lineno or first_node.lineno))
    remove_set: set[int] = set()
    for start, end in regions_to_remove:
        for i in range(start, end + 1):
            remove_set.add(i)
    result_lines = [line for i, line in enumerate(lines, 1) if i not in remove_set]
    return "".join(result_lines)


def _rename_functions(source: str, mod_name: str) -> str:
    """Rename register() and run() functions to module-prefixed versions.

    Args:
        source: Source code of a command module.
        mod_name: The module name (e.g. "hash_cmd").

    Returns:
        Source with renamed functions and updated set_defaults references.
    """
    source = re.sub(r'\bdef register\(', f'def _register_{mod_name}(', source)
    source = re.sub(r'\bdef run\(', f'def _run_{mod_name}(', source)
    source = re.sub(r'func=run\b', f'func=_run_{mod_name}', source)
    return source


def _collect_command_modules() -> list[Path]:
    """Find all command module files, excluding __init__.py.

    Returns:
        Sorted list of Path objects for command modules.
    """
    modules: list[Path] = []
    for p in sorted(_CMD_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        modules.append(p)
    return modules


def _build_dispatcher(cmd_modules: list[Path]) -> str:
    """Generate the amalgamated main() dispatcher function.

    Args:
        cmd_modules: List of command module paths (excluding shared.py).

    Returns:
        Source code for the main() function.
    """
    register_calls: list[str] = []
    for p in cmd_modules:
        if p.name == "shared.py":
            continue
        mod_name = p.stem
        register_calls.append(f"    _register_{mod_name}(subparsers)")
    calls = "\n".join(register_calls)
    return f'''
def main() -> int:
    """Parse arguments and dispatch to the appropriate subcommand."""
    parser = argparse.ArgumentParser(prog="withpy", description="Batteries-included Swiss-army CLI -- stdlib only, no pip required")
    parser.add_argument("--version", "-V", action="version", version=f"withpy {{__version__}}")
    subparsers = parser.add_subparsers(dest="command")
{calls}
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
'''


def build() -> None:
    """Run the amalgamation build process.

    Raises:
        RuntimeError: If required source files are missing.
    """
    if not _SRC_DIR.is_dir():
        raise RuntimeError(f"source directory not found: {_SRC_DIR}")
    all_imports: set[str] = set()
    init_source = (_SRC_DIR / "__init__.py").read_text()
    all_imports.update(_extract_imports(init_source))
    version_line = ""
    for line in init_source.splitlines():
        if line.startswith("__version__"):
            version_line = line
            break
    cmd_modules = _collect_command_modules()
    shared_path = _CMD_DIR / "shared.py"
    if not shared_path.exists():
        raise RuntimeError("shared.py not found")
    cli_source = (_SRC_DIR / "cli.py").read_text()
    all_imports.update(_extract_imports(cli_source))
    all_imports.update(_extract_imports(shared_path.read_text()))
    for p in cmd_modules:
        if p.name == "shared.py":
            continue
        all_imports.update(_extract_imports(p.read_text()))
    all_imports.discard("")
    sorted_imports = sorted(all_imports)
    sections: list[str] = []
    sections.append(_SHEBANG)
    sections.append('"""withpy -- batteries-included Swiss-army CLI. Amalgamated single-file build."""\n')
    sections.append("\n".join(sorted_imports))
    sections.append("")
    sections.append(version_line)
    sections.append("")
    shared_body = _strip_imports_and_docstring(shared_path.read_text())
    sections.append(f"# --- shared ---\n{shared_body.strip()}")
    non_shared = [p for p in cmd_modules if p.name != "shared.py"]
    for p in non_shared:
        mod_name = p.stem
        source = p.read_text()
        body = _strip_imports_and_docstring(source)
        body = _rename_functions(body, mod_name)
        sections.append(f"\n# --- {mod_name} ---\n{body.strip()}")
    sections.append(_build_dispatcher(cmd_modules))
    output = "\n\n".join(sections) + "\n"
    output = re.sub(r'\n{3,}', '\n\n\n', output)
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    _OUT_FILE.write_text(output)
    if os.name != "nt":
        _OUT_FILE.chmod(_OUT_FILE.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"built {_OUT_FILE} ({_OUT_FILE.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
