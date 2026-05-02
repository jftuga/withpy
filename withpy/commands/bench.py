"""HTTP load testing with concurrency and statistical reporting.

Uses concurrent.futures to send multiple HTTP requests in parallel,
measuring latency and computing percentile statistics. Reports request
counts, success/failure rates, and latency distribution.
"""

import argparse
import concurrent.futures
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request


def _make_request(url: str, method: str, headers: list[str], data: str | None, timeout: float) -> tuple[int, float]:
    """Make a single HTTP request and return status and latency.

    Args:
        url: Target URL.
        method: HTTP method.
        headers: List of "Name: Value" header strings.
        data: Request body or None.
        timeout: Request timeout.

    Returns:
        Tuple of (HTTP status code or 0 for error, latency in seconds).
    """
    body = data.encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    for h in headers:
        if ":" in h:
            name, value = h.split(":", 1)
            req.add_header(name.strip(), value.strip())
    start = time.time()
    try:
        response = urllib.request.urlopen(req, timeout=timeout)
        response.read()
        elapsed = time.time() - start
        return (response.status, elapsed)
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        return (e.code, elapsed)
    except (urllib.error.URLError, OSError):
        elapsed = time.time() - start
        return (0, elapsed)


def _format_stats(latencies: list[float], status_codes: dict[int, int], total_time: float, total_requests: int) -> str:
    """Format benchmark results.

    Args:
        latencies: List of request latencies in seconds.
        status_codes: Count of each HTTP status code.
        total_time: Total benchmark duration.
        total_requests: Total number of requests made.

    Returns:
        Formatted statistics string.
    """
    lines: list[str] = ["", "Results:", ""]
    successes = sum(c for code, c in status_codes.items() if 200 <= code < 400)
    failures = total_requests - successes
    rps = total_requests / total_time if total_time > 0 else 0
    lines.append(f"  Requests:      {total_requests}")
    lines.append(f"  Successes:     {successes}")
    lines.append(f"  Failures:      {failures}")
    lines.append(f"  Total time:    {total_time:.2f}s")
    lines.append(f"  Requests/sec:  {rps:.1f}")
    lines.append("")
    if latencies:
        sorted_lat = sorted(latencies)
        lines.append("  Latency:")
        lines.append(f"    min:    {sorted_lat[0] * 1000:.0f}ms")
        lines.append(f"    mean:   {statistics.mean(latencies) * 1000:.0f}ms")
        lines.append(f"    p50:    {sorted_lat[len(sorted_lat) // 2] * 1000:.0f}ms")
        p90_idx = int(len(sorted_lat) * 0.9)
        lines.append(f"    p90:    {sorted_lat[p90_idx] * 1000:.0f}ms")
        p95_idx = int(len(sorted_lat) * 0.95)
        lines.append(f"    p95:    {sorted_lat[p95_idx] * 1000:.0f}ms")
        p99_idx = int(len(sorted_lat) * 0.99)
        lines.append(f"    p99:    {sorted_lat[min(p99_idx, len(sorted_lat) - 1)] * 1000:.0f}ms")
        lines.append(f"    max:    {sorted_lat[-1] * 1000:.0f}ms")
    if status_codes:
        lines.append("")
        lines.append("  Status codes:")
        for code in sorted(status_codes.keys()):
            label = "error" if code == 0 else str(code)
            lines.append(f"    {label}: {status_codes[code]}")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the bench subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("bench", help="HTTP load testing with concurrency and stats")
    p.add_argument("url", help="Target URL")
    p.add_argument("--requests", "-n", type=int, default=100, help="Total requests (default: 100)")
    p.add_argument("--concurrency", "-c", type=int, default=10, help="Concurrent workers (default: 10)")
    p.add_argument("--method", "-X", default="GET", help="HTTP method (default: GET)")
    p.add_argument("--header", "-H", action="append", default=[], help="Request header (Name: Value)")
    p.add_argument("--data", "-d", default=None, help="Request body")
    p.add_argument("--timeout", "-t", type=float, default=10.0, help="Per-request timeout (default: 10s)")
    p.add_argument("--duration", type=float, default=None, help="Run for N seconds instead of fixed count")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the bench subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    latencies: list[float] = []
    status_codes: dict[int, int] = {}
    lock = threading.Lock()
    completed = 0
    print(f"Benchmarking {args.url}...")
    print(f"  {args.requests} requests, {args.concurrency} concurrent")
    start_time = time.time()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            if args.duration:
                futures: list[concurrent.futures.Future] = []
                deadline = time.time() + args.duration
                while time.time() < deadline:
                    if len(futures) - completed < args.concurrency * 2:
                        f = executor.submit(_make_request, args.url, args.method, args.header, args.data, args.timeout)
                        futures.append(f)
                    done = [f for f in futures if f.done()]
                    for f in done:
                        futures.remove(f)
                        status, latency = f.result()
                        with lock:
                            latencies.append(latency)
                            status_codes[status] = status_codes.get(status, 0) + 1
                            completed += 1
                    time.sleep(0.01)
                for f in concurrent.futures.as_completed(futures):
                    status, latency = f.result()
                    with lock:
                        latencies.append(latency)
                        status_codes[status] = status_codes.get(status, 0) + 1
                        completed += 1
            else:
                futures = [executor.submit(_make_request, args.url, args.method, args.header, args.data, args.timeout) for _ in range(args.requests)]
                for f in concurrent.futures.as_completed(futures):
                    status, latency = f.result()
                    with lock:
                        latencies.append(latency)
                        status_codes[status] = status_codes.get(status, 0) + 1
                        completed += 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    total_time = time.time() - start_time
    total_requests = len(latencies)
    print(_format_stats(latencies, status_codes, total_time, total_requests))
    return 0
