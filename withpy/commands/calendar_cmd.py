"""Calendar display, weekday math, Easter date calculation.

Provides ASCII calendar rendering for months and years, day-of-week
lookup, ISO week number computation, date arithmetic, and Easter date
calculation using the anonymous Gregorian algorithm.
"""

import argparse
import calendar
import datetime
import sys


def _easter(year: int) -> datetime.date:
    """Compute Easter Sunday for a given year using the Anonymous Gregorian algorithm.

    Args:
        year: The year to compute Easter for.

    Returns:
        The date of Easter Sunday.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)


def _parse_date(value: str) -> datetime.date:
    """Parse a date string in YYYY-MM-DD format.

    Args:
        value: Date string.

    Returns:
        Parsed date object.

    Raises:
        ValueError: If format is invalid.
    """
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid date format: {value} (expected YYYY-MM-DD)") from None


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the calendar subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("calendar", help="Calendars, weekday math, Easter dates")
    p.add_argument("--mode", "-m", default="month", choices=["month", "year", "weekday", "easter", "weeks", "add"], help="Operation mode (default: month)")
    p.add_argument("--year", "-y", type=int, default=None, help="Year")
    p.add_argument("--month", type=int, default=None, help="Month (1-12)")
    p.add_argument("--days", type=int, default=0, help="Days to add (add mode)")
    p.add_argument("--weeks", type=int, default=0, help="Weeks to add (add mode)")
    p.add_argument("date", nargs="?", default=None, help="Date (YYYY-MM-DD)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the calendar subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        today = datetime.date.today()
        match args.mode:
            case "month":
                year = args.year or today.year
                month = args.month or today.month
                cal = calendar.TextCalendar()
                output = cal.formatmonth(year, month)
                sys.stdout.write(output)
            case "year":
                year = args.year or today.year
                cal = calendar.TextCalendar()
                output = cal.formatyear(year)
                sys.stdout.write(output)
                sys.stdout.write("\n")
            case "weekday":
                if args.date:
                    d = _parse_date(args.date)
                else:
                    d = today
                day_name = calendar.day_name[d.weekday()]
                print(f"{d.isoformat()} is {day_name}")
            case "easter":
                year = args.year or today.year
                e = _easter(year)
                print(f"Easter {year}: {e.isoformat()} ({calendar.day_name[e.weekday()]})")
            case "weeks":
                if args.date:
                    d = _parse_date(args.date)
                else:
                    d = today
                iso_year, iso_week, iso_day = d.isocalendar()
                print(f"{d.isoformat()}: ISO week {iso_week} of {iso_year}, day {iso_day}")
            case "add":
                if args.date:
                    d = _parse_date(args.date)
                else:
                    d = today
                delta = datetime.timedelta(days=args.days, weeks=args.weeks)
                result = d + delta
                print(f"{d.isoformat()} + {args.days}d {args.weeks}w = {result.isoformat()} ({calendar.day_name[result.weekday()]})")
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, OverflowError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
