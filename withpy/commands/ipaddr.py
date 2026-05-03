"""IP address and CIDR network math operations.

Provides modes for inspecting networks, checking address containment,
detecting overlap between networks, splitting into subnets, summarizing
address ranges, and listing all hosts in a network.
"""

import argparse
import ipaddress
import sys


def _network_info(addr_str: str) -> str:
    """Display detailed information about an IP network.

    Args:
        addr_str: IP address or CIDR notation string.

    Returns:
        Formatted network information.
    """
    try:
        net = ipaddress.ip_network(addr_str, strict=False)
    except ValueError:
        addr = ipaddress.ip_address(addr_str)
        lines = [
            f"address:    {addr}",
            f"version:    IPv{addr.version}",
            f"binary:     {int(addr):0{addr.max_prefixlen}b}",
            f"is_private: {addr.is_private}",
            f"is_global:  {addr.is_global}",
        ]
        return "\n".join(lines)
    lines = [
        f"network:    {net.network_address}/{net.prefixlen}",
        f"netmask:    {net.netmask}",
        f"hostmask:   {net.hostmask}",
        f"broadcast:  {net.broadcast_address}",
        f"hosts:      {net.num_addresses - 2 if net.prefixlen < net.max_prefixlen else 1}",
        f"version:    IPv{net.version}",
        f"is_private: {net.is_private}",
        f"first_host: {list(net.hosts())[0] if net.num_addresses > 2 else net.network_address}",
        f"last_host:  {list(net.hosts())[-1] if net.num_addresses > 2 else net.network_address}",
    ]
    return "\n".join(lines)


def _check_contains(addresses: list[str]) -> str:
    """Check if an address is contained in a network.

    Args:
        addresses: List of [network, address] strings.

    Returns:
        Result string.

    Raises:
        ValueError: If fewer than 2 arguments provided.
    """
    if len(addresses) < 2:
        raise ValueError("contains requires a network and an address")
    net = ipaddress.ip_network(addresses[0], strict=False)
    addr = ipaddress.ip_address(addresses[1])
    if addr in net:
        return f"{addr} is in {net}"
    return f"{addr} is NOT in {net}"


def _check_overlap(addresses: list[str]) -> str:
    """Check if two networks overlap.

    Args:
        addresses: List of [network1, network2] strings.

    Returns:
        Result string.

    Raises:
        ValueError: If fewer than 2 arguments provided.
    """
    if len(addresses) < 2:
        raise ValueError("overlap requires two networks")
    net1 = ipaddress.ip_network(addresses[0], strict=False)
    net2 = ipaddress.ip_network(addresses[1], strict=False)
    if net1.overlaps(net2):
        return f"{net1} overlaps with {net2}"
    return f"{net1} does NOT overlap with {net2}"


def _split_network(addresses: list[str], new_prefix: int | None) -> str:
    """Split a network into smaller subnets.

    Args:
        addresses: List containing the network to split.
        new_prefix: New prefix length for subnets.

    Returns:
        One subnet per line.

    Raises:
        ValueError: If prefix is invalid.
    """
    if not addresses:
        raise ValueError("split requires a network")
    if new_prefix is None:
        raise ValueError("--prefix is required for split mode")
    net = ipaddress.ip_network(addresses[0], strict=False)
    subnets = list(net.subnets(new_prefix=new_prefix))
    return "\n".join(str(s) for s in subnets)


def _summarize_addresses(addresses: list[str]) -> str:
    """Collapse a list of addresses/networks into minimal CIDR set.

    Args:
        addresses: List of IP addresses or networks.

    Returns:
        Summarized networks, one per line.
    """
    nets: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for addr in addresses:
        try:
            nets.append(ipaddress.ip_network(addr, strict=False))
        except ValueError:
            ip = ipaddress.ip_address(addr)
            if ip.version == 4:
                nets.append(ipaddress.IPv4Network(f"{ip}/32"))
            else:
                nets.append(ipaddress.IPv6Network(f"{ip}/128"))
    collapsed = list(ipaddress.collapse_addresses(sorted(nets)))
    return "\n".join(str(n) for n in collapsed)


def _list_range(addresses: list[str]) -> str:
    """List all host addresses in a network.

    Args:
        addresses: List containing the network.

    Returns:
        One host per line.
    """
    if not addresses:
        raise ValueError("range requires a network")
    net = ipaddress.ip_network(addresses[0], strict=False)
    hosts = list(net.hosts())
    if len(hosts) > 1024:
        lines = [str(h) for h in hosts[:1024]]
        lines.append(f"... ({len(hosts) - 1024} more hosts)")
        return "\n".join(lines)
    return "\n".join(str(h) for h in hosts)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ipaddr subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("ipaddr", help="IP/CIDR math (contains, overlap, split, summarize)")
    p.add_argument("--mode", "-m", default="info", choices=["info", "contains", "overlap", "split", "summarize", "range"], help="Operation mode (default: info)")
    p.add_argument("--prefix", type=int, default=None, help="New prefix length for split mode")
    p.add_argument("addresses", nargs="+", help="IP addresses or CIDR networks")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the ipaddr subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "info":
                for addr in args.addresses:
                    print(_network_info(addr))
                    if len(args.addresses) > 1:
                        print()
            case "contains":
                print(_check_contains(args.addresses))
            case "overlap":
                print(_check_overlap(args.addresses))
            case "split":
                print(_split_network(args.addresses, args.prefix))
            case "summarize":
                print(_summarize_addresses(args.addresses))
            case "range":
                print(_list_range(args.addresses))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
