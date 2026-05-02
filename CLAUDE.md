# withpy Development Guide

## Project Overview

`withpy` is a batteries-included Swiss-army CLI using only the Python 3.14+
standard library. It is the Python sibling of
[mtool](https://github.com/jftuga/mtool) (Go) and
[swiftswiss](https://github.com/jftuga/swiftswiss) (Swift).

## Python Version

**Target: Python 3.14 or newer.** This overrides any global setting. Use PEP 695
`type` aliases, `match` statements, built-in generics (`list[str]`), and
modern stdlib modules. Do not use deprecated APIs.

## Hard Constraints

- **Standard library only** for runtime code. `pytest` is allowed only inside `tests/`.
- **Every function and method is fully type-annotated.**
- **No nested function definitions.** Promote helpers to module scope.
- **No emojis** in code, docs, or output.
- **Google-style docstrings** on every module, class, and function.
- **Function signatures stay on a single line.** Never split a `def` across lines.
- **Fail fast.** Raise built-in exceptions at CLI boundaries.

## Subcommand Module Contract

Every file under `withpy/commands/` exports exactly two public functions:

```python
def register(subparsers: argparse._SubParsersAction) -> None:
    ...

def run(args: argparse.Namespace) -> int:
    ...
```

The dispatcher (`cli.py`) imports each module and calls `register`.
It contains no per-command logic.

## Naming Conventions

- Use a `_cmd` suffix when a module name shadows a stdlib/builtin:
  `time_cmd.py`, `json_cmd.py`, `hash_cmd.py`, etc.
- Private helpers use a `_` prefix and live at module scope.

## Amalgamation Rules

The build produces a single-file `dist/withpy` via `build.py`. To keep
amalgamation simple:

- **No relative imports** in command modules.
- **No `__file__`, `__package__`, or `importlib.resources`.**
- **No embedded assets.** Use string literals.
- **Command modules do not import each other.** Only stdlib + `commands.shared`.
- **Module-level constants are fine.**

## Build and Test

```
make build       # Compile-check all source files
make test        # pytest (builds amalgamated artifact first)
make amalgamate  # Produce dist/withpy
make dist        # Create tar.xz archive
make clean       # Remove build artifacts
make help        # Show all targets
```

## Testing Philosophy

- **Round-trip tests:** encode/decode, compress/decompress, archive create/extract.
- **Known-value tests:** hash digests and epoch conversions against fixed expected output.
- **Error-path tests:** invalid input, wrong parameters, unsupported formats.
- **No external network.** Network tests use local listeners only.
- `tests/test_amalgamated.py` runs `dist/withpy` as a subprocess.

## Adding a New Subcommand

1. Create `withpy/commands/<name>.py` (or `<name>_cmd.py` if it shadows stdlib).
2. Implement `register()` and `run()` per the contract above.
3. Import and register in `withpy/cli.py` (add to `_COMMAND_MODULES`).
4. Create `tests/test_<name>.py` with known-value, round-trip, and error tests.
5. Add a representative test to `tests/test_amalgamated.py`.
6. Run `make test` to verify both module and amalgamated forms.
7. Update README.md with the new subcommand and stdlib module count.
