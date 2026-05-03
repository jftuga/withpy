"""Thin dispatcher for the withpy CLI.

Routes subcommands to their respective handler modules via argparse subparsers.
Contains no per-command business logic. Each command module registers itself
by exporting a register() function.
"""

import argparse
import sys

import withpy
from withpy.commands import (
    archive,
    bench,
    calc,
    calendar_cmd,
    codec,
    color,
    compress,
    config_cmd,
    csv_cmd,
    db,
    deps,
    diff,
    dirdiff,
    fetch,
    find_cmd,
    generate,
    glob_cmd,
    hash_cmd,
    hexdump,
    info,
    inspect_cmd,
    ipaddr,
    iter_cmd,
    json_cmd,
    jwt,
    keyword_cmd,
    log_cmd,
    mail,
    net_cmd,
    netrc_cmd,
    pickle_cmd,
    plist,
    profile_cmd,
    pydis_cmd,
    random_cmd,
    repr_cmd,
    sched_cmd,
    serve,
    shlex_cmd,
    sort_cmd,
    struct_cmd,
    template,
    time_cmd,
    token_cmd,
    toml_cmd,
    transform,
    unicode_cmd,
    url,
    wave_cmd,
    zipapp_cmd,
)

_COMMAND_MODULES: tuple = (
    archive,
    bench,
    calc,
    calendar_cmd,
    codec,
    color,
    compress,
    config_cmd,
    csv_cmd,
    db,
    deps,
    diff,
    dirdiff,
    fetch,
    find_cmd,
    generate,
    glob_cmd,
    hash_cmd,
    hexdump,
    info,
    inspect_cmd,
    ipaddr,
    iter_cmd,
    json_cmd,
    jwt,
    keyword_cmd,
    log_cmd,
    mail,
    net_cmd,
    netrc_cmd,
    pickle_cmd,
    plist,
    profile_cmd,
    pydis_cmd,
    random_cmd,
    repr_cmd,
    sched_cmd,
    serve,
    shlex_cmd,
    sort_cmd,
    struct_cmd,
    template,
    time_cmd,
    token_cmd,
    toml_cmd,
    transform,
    unicode_cmd,
    url,
    wave_cmd,
    zipapp_cmd,
)


def main() -> int:
    """Parse arguments and dispatch to the appropriate subcommand.

    Returns:
        Exit code: 0 on success, nonzero on failure.
    """
    parser = argparse.ArgumentParser(prog="withpy", description="Batteries-included Swiss-army CLI -- stdlib only, no pip required")
    parser.add_argument("--version", "-V", action="version", version=f"withpy {withpy.__version__}")
    subparsers = parser.add_subparsers(dest="command")
    for mod in _COMMAND_MODULES:
        mod.register(subparsers)
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)
