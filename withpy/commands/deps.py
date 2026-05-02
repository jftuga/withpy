"""Topological sort of dependency graphs.

Accepts dependency graphs in JSON or pair-list format and provides
topological sorting, cycle detection, Graphviz DOT output, and
level-grouped display using graphlib.TopologicalSorter.
"""

import argparse
import graphlib
import json
import sys

from withpy.commands.shared import read_input_text


def _parse_json_graph(text: str) -> dict[str, list[str]]:
    """Parse a JSON dependency graph.

    Args:
        text: JSON string mapping nodes to their dependency lists.

    Returns:
        Dictionary of node -> dependencies.

    Raises:
        ValueError: If JSON format is invalid.
    """
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object mapping nodes to dependency arrays")
    graph: dict[str, list[str]] = {}
    for node, deps in data.items():
        if not isinstance(deps, list):
            raise ValueError(f"dependencies for '{node}' must be an array")
        graph[node] = [str(d) for d in deps]
    return graph


def _parse_pairs_graph(text: str) -> dict[str, list[str]]:
    """Parse a pair-list dependency graph (one 'A B' per line means A depends on B).

    Args:
        text: Text with one pair per line.

    Returns:
        Dictionary of node -> dependencies.
    """
    graph: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            node, dep = parts[0], parts[1]
            graph.setdefault(node, []).append(dep)
            graph.setdefault(dep, [])
        elif len(parts) == 1:
            graph.setdefault(parts[0], [])
    return graph


def _to_dot(graph: dict[str, list[str]]) -> str:
    """Convert a dependency graph to Graphviz DOT format.

    Args:
        graph: Node -> dependencies mapping.

    Returns:
        DOT format string.
    """
    lines = ["digraph dependencies {"]
    for node, deps in sorted(graph.items()):
        if not deps:
            lines.append(f'  "{node}";')
        for dep in deps:
            lines.append(f'  "{node}" -> "{dep}";')
    lines.append("}")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the deps subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("deps", help="Topological sort of dependency graphs")
    p.add_argument("--mode", "-m", default="sort", choices=["sort", "check", "dot", "levels"], help="Operation mode (default: sort)")
    p.add_argument("--format", "-f", default="json", choices=["json", "pairs"], help="Input format (default: json)")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the deps subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        text = read_input_text(args.input)
        match args.format:
            case "json":
                graph = _parse_json_graph(text)
            case "pairs":
                graph = _parse_pairs_graph(text)
            case _:
                print(f"error: unknown format: {args.format}", file=sys.stderr)
                return 1
        ts = graphlib.TopologicalSorter()
        for node, deps in graph.items():
            ts.add(node, *deps)
        match args.mode:
            case "sort":
                try:
                    order = list(ts.static_order())
                    for node in order:
                        print(node)
                except graphlib.CycleError as e:
                    print(f"error: {e}", file=sys.stderr)
                    return 1
            case "check":
                try:
                    list(ts.static_order())
                    print("no cycles detected")
                    return 0
                except graphlib.CycleError as e:
                    print(f"cycle detected: {e}", file=sys.stderr)
                    return 1
            case "dot":
                print(_to_dot(graph))
            case "levels":
                try:
                    ts2 = graphlib.TopologicalSorter()
                    for node, deps in graph.items():
                        ts2.add(node, *deps)
                    ts2.prepare()
                    level = 0
                    while ts2.is_active():
                        nodes = ts2.get_ready()
                        print(f"Level {level}: {' '.join(sorted(nodes))}")
                        ts2.done(*nodes)
                        level += 1
                except graphlib.CycleError as e:
                    print(f"error: {e}", file=sys.stderr)
                    return 1
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
