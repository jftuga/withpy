"""System information reporting: OS, Python, network, hardware, environment.

Collects and displays system information in multiple formats (text, JSON,
CSV, XML) using platform, socket, os, and related stdlib modules.
"""

import argparse
import csv
import getpass
import io
import json
import os
import platform
import shutil
import socket
import sys
import uuid
import xml.etree.ElementTree as ET


def _get_os_info() -> dict[str, str]:
    """Collect operating system information.

    Returns:
        Dictionary of OS-related key-value pairs.
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "architecture": platform.architecture()[0],
        "platform": platform.platform(),
    }


def _get_python_info() -> dict[str, str]:
    """Collect Python runtime information.

    Returns:
        Dictionary of Python-related key-value pairs.
    """
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
        "executable": sys.executable,
        "prefix": sys.prefix,
    }


def _get_network_info() -> dict[str, str]:
    """Collect network information.

    Returns:
        Dictionary of network-related key-value pairs.
    """
    info: dict[str, str] = {
        "hostname": socket.gethostname(),
    }
    try:
        info["fqdn"] = socket.getfqdn()
    except (OSError, socket.herror):
        info["fqdn"] = ""
    try:
        info["ip"] = socket.gethostbyname(socket.gethostname())
    except (OSError, socket.gaierror):
        info["ip"] = "unknown"
    return info


def _get_hardware_info() -> dict[str, str]:
    """Collect hardware information.

    Returns:
        Dictionary of hardware-related key-value pairs.
    """
    return {
        "cpu_count": str(os.cpu_count() or "unknown"),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
    }


def _get_disk_info() -> dict[str, str]:
    """Collect disk usage information for common mount points.

    Returns:
        Dictionary of disk usage key-value pairs.
    """
    info: dict[str, str] = {}
    try:
        usage = shutil.disk_usage("/")
        info["root_total"] = _format_bytes(usage.total)
        info["root_used"] = _format_bytes(usage.used)
        info["root_free"] = _format_bytes(usage.free)
        info["root_percent"] = f"{usage.used / usage.total * 100:.1f}%"
    except OSError:
        info["root"] = "unavailable"
    home = os.path.expanduser("~")
    if home != "/":
        try:
            usage = shutil.disk_usage(home)
            info["home_total"] = _format_bytes(usage.total)
            info["home_used"] = _format_bytes(usage.used)
            info["home_free"] = _format_bytes(usage.free)
            info["home_percent"] = f"{usage.used / usage.total * 100:.1f}%"
        except OSError:
            pass
    return info


def _format_bytes(n: int) -> str:
    """Format byte count as human-readable string.

    Args:
        n: Number of bytes.

    Returns:
        Formatted string like '1.5 GB'.
    """
    for threshold, unit in [(1 << 40, "TB"), (1 << 30, "GB"), (1 << 20, "MB"), (1 << 10, "KB")]:
        if n >= threshold:
            return f"{n / threshold:.1f} {unit}"
    return f"{n} B"


def _get_env_info() -> dict[str, str]:
    """Collect environment variable information (filtered).

    Returns:
        Dictionary of safe environment variables.
    """
    safe_keys = ["HOME", "USER", "SHELL", "LANG", "TERM", "PATH", "EDITOR", "VISUAL", "PWD", "HOSTNAME"]
    info: dict[str, str] = {}
    for key in safe_keys:
        val = os.environ.get(key)
        if val:
            info[key] = val
    info["username"] = getpass.getuser()
    return info


def _get_all_info() -> dict[str, dict[str, str]]:
    """Collect all system information categories.

    Returns:
        Nested dictionary with category keys.
    """
    return {
        "os": _get_os_info(),
        "python": _get_python_info(),
        "network": _get_network_info(),
        "hardware": _get_hardware_info(),
        "env": _get_env_info(),
        "disk": _get_disk_info(),
        "uuid": {"machine_id": str(uuid.uuid4())},
    }


def _format_text(data: dict[str, dict[str, str]]) -> str:
    """Format system info as plain text.

    Args:
        data: Nested info dictionary.

    Returns:
        Formatted text output.
    """
    lines: list[str] = []
    for section, values in data.items():
        lines.append(f"[{section}]")
        for key, val in values.items():
            lines.append(f"  {key}: {val}")
        lines.append("")
    return "\n".join(lines)


def _format_csv_output(data: dict[str, dict[str, str]]) -> str:
    """Format system info as CSV.

    Args:
        data: Nested info dictionary.

    Returns:
        CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "key", "value"])
    for section, values in data.items():
        for key, val in values.items():
            writer.writerow([section, key, val])
    return output.getvalue()


def _format_xml(data: dict[str, dict[str, str]]) -> str:
    """Format system info as XML.

    Args:
        data: Nested info dictionary.

    Returns:
        XML string.
    """
    root = ET.Element("system-info")
    for section, values in data.items():
        section_elem = ET.SubElement(root, section)
        for key, val in values.items():
            item = ET.SubElement(section_elem, key)
            item.text = val
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the info subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("info", help="System information (OS, CPU, network, env)")
    p.add_argument("--mode", "-m", default="all", choices=["all", "os", "python", "network", "env", "hardware", "disk"], help="Info category (default: all)")
    p.add_argument("--format", "-f", default="text", choices=["text", "json", "csv", "xml"], help="Output format (default: text)")
    p.add_argument("--key", "-k", default=None, help="Specific info key to retrieve")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the info subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    collectors = {
        "os": _get_os_info,
        "python": _get_python_info,
        "network": _get_network_info,
        "env": _get_env_info,
        "hardware": _get_hardware_info,
        "disk": _get_disk_info,
    }
    if args.mode == "all":
        data = _get_all_info()
    else:
        collector = collectors.get(args.mode)
        if not collector:
            print(f"error: unknown mode: {args.mode}", file=sys.stderr)
            return 1
        data = {args.mode: collector()}
    if args.key:
        for section_data in data.values():
            if args.key in section_data:
                print(section_data[args.key])
                return 0
        print(f"error: key not found: {args.key}", file=sys.stderr)
        return 1
    match args.format:
        case "text":
            print(_format_text(data))
        case "json":
            print(json.dumps(data, indent=2))
        case "csv":
            sys.stdout.write(_format_csv_output(data))
        case "xml":
            print(_format_xml(data))
    return 0
