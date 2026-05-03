"""Time and date utilities: current time, epoch conversions, timezone math, calendars.

Provides multiple modes for working with dates and times: display the current
time in several formats, convert between epoch timestamps and human-readable
dates, convert across timezones, and print ASCII calendars.
"""

import argparse
import calendar
import datetime
import sys
import time
import zoneinfo

type DateFormats = list[str]

_PARSE_FORMATS: DateFormats = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%b %d, %Y %H:%M:%S",
    "%b %d, %Y",
    "%B %d, %Y",
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S",
]

_DISPLAY_FORMAT: str = "%Y-%m-%d %H:%M:%S %Z"


def _parse_flexible(s: str) -> datetime.datetime:
    """Parse a date/time string trying multiple common formats.

    Args:
        s: A date/time string, or an integer epoch timestamp as a string.

    Returns:
        A datetime object. If no timezone info is present, assumes local time.

    Raises:
        ValueError: If the string cannot be parsed in any known format.
    """
    stripped = s.strip()
    try:
        epoch = int(stripped)
        return datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc)
    except ValueError:
        pass
    try:
        epoch_f = float(stripped)
        return datetime.datetime.fromtimestamp(epoch_f, tz=datetime.timezone.utc)
    except ValueError:
        pass
    for fmt in _PARSE_FORMATS:
        try:
            return datetime.datetime.strptime(stripped, fmt)
        except ValueError:
            continue
    raise ValueError(f"cannot parse date/time: {s!r}")


def _format_multi(dt: datetime.datetime) -> str:
    """Format a datetime in multiple representations.

    Args:
        dt: The datetime to format.

    Returns:
        A multi-line string with Local, UTC, ISO8601, and Epoch representations.
    """
    if dt.tzinfo is None:
        local_dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        local_dt = dt.astimezone()
    utc_dt = local_dt.astimezone(datetime.timezone.utc)
    lines = [
        f"Local:   {local_dt.strftime(_DISPLAY_FORMAT)}",
        f"UTC:     {utc_dt.strftime(_DISPLAY_FORMAT)}",
        f"ISO8601: {local_dt.isoformat()}",
        f"Epoch:   {int(utc_dt.timestamp())}",
    ]
    return "\n".join(lines)


def _run_now(args: argparse.Namespace) -> int:
    """Display the current time in multiple formats.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if args.zone:
        try:
            tz = zoneinfo.ZoneInfo(args.zone)
        except (KeyError, zoneinfo.ZoneInfoNotFoundError):
            print(f"error: unknown timezone: {args.zone}", file=sys.stderr)
            return 1
        now = now.astimezone(tz)
    if args.format:
        print(now.strftime(args.format))
    else:
        print(_format_multi(now))
    return 0


def _run_toepoch(args: argparse.Namespace) -> int:
    """Convert a date string to a Unix epoch timestamp.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on parse failure.
    """
    if not args.value:
        print("error: value required for toepoch mode", file=sys.stderr)
        return 1
    try:
        dt = _parse_flexible(args.value)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    print(int(dt.timestamp()))
    return 0


def _run_fromepoch(args: argparse.Namespace) -> int:
    """Convert a Unix epoch timestamp to human-readable formats.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on parse failure.
    """
    if not args.value:
        print("error: value required for fromepoch mode", file=sys.stderr)
        return 1
    try:
        epoch = int(args.value)
    except ValueError:
        print(f"error: not a valid epoch: {args.value!r}", file=sys.stderr)
        return 1
    dt = datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc)
    if args.zone:
        try:
            tz = zoneinfo.ZoneInfo(args.zone)
        except (KeyError, zoneinfo.ZoneInfoNotFoundError):
            print(f"error: unknown timezone: {args.zone}", file=sys.stderr)
            return 1
        dt = dt.astimezone(tz)
    if args.format:
        print(dt.strftime(args.format))
    else:
        print(_format_multi(dt))
    return 0


def _run_convert(args: argparse.Namespace) -> int:
    """Convert a date string to a different timezone.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    if not args.zone:
        print("error: --zone is required for convert mode", file=sys.stderr)
        return 1
    if not args.value:
        print("error: value required for convert mode", file=sys.stderr)
        return 1
    try:
        dt = _parse_flexible(args.value)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        tz = zoneinfo.ZoneInfo(args.zone)
    except (KeyError, zoneinfo.ZoneInfoNotFoundError):
        print(f"error: unknown timezone: {args.zone}", file=sys.stderr)
        return 1
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    converted = dt.astimezone(tz)
    if args.format:
        print(converted.strftime(args.format))
    else:
        print(_format_multi(converted))
    return 0


def _run_calendar(args: argparse.Namespace) -> int:
    """Print an ASCII calendar for a month or year.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on parse failure.
    """
    if not args.value:
        now = datetime.datetime.now()
        year, month = now.year, now.month
    else:
        val = args.value.strip()
        if "-" in val:
            parts = val.split("-", 1)
            try:
                year = int(parts[0])
                month = int(parts[1])
            except ValueError:
                print(f"error: invalid calendar value: {val!r} (use YYYY or YYYY-MM)", file=sys.stderr)
                return 1
            print(calendar.TextCalendar().formatmonth(year, month), end="")
            return 0
        else:
            try:
                year = int(val)
            except ValueError:
                print(f"error: invalid year: {val!r}", file=sys.stderr)
                return 1
            print(calendar.TextCalendar().formatyear(year))
            return 0
    print(calendar.TextCalendar().formatmonth(year, month), end="")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the time subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("time", help="Time/date utilities: now, epoch conversions, calendars")
    p.add_argument("--mode", "-m", default="now", choices=["now", "toepoch", "fromepoch", "convert", "calendar"], help="Operation mode (default: now)")
    p.add_argument("--format", "-f", default=None, metavar="FMT", help="strftime format string for output")
    p.add_argument("--zone", "-z", default=None, metavar="ZONE", help="IANA timezone name (e.g. America/New_York)")
    p.add_argument("value", nargs="?", default=None, help="Input value (epoch, date string, or YYYY[-MM])")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the time subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    match args.mode:
        case "now":
            return _run_now(args)
        case "toepoch":
            return _run_toepoch(args)
        case "fromepoch":
            return _run_fromepoch(args)
        case "convert":
            return _run_convert(args)
        case "calendar":
            return _run_calendar(args)
        case _:
            print(f"error: unknown mode: {args.mode}", file=sys.stderr)
            return 1
