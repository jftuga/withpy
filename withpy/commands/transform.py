"""Text transformations: regex, case conversion, wrapping, normalization.

Provides multiple text transformation modes including regex substitution,
case conversions (upper, lower, title, camel, snake), text wrapping,
Unicode normalization, pattern counting, and character frequency analysis.
"""

import argparse
import collections
import re
import sys
import textwrap
import unicodedata

from withpy.commands.shared import read_input_text


def _to_camel_case(text: str) -> str:
    """Convert text to camelCase.

    Args:
        text: Input text (assumed space/underscore/hyphen separated).

    Returns:
        camelCase version of the text.
    """
    words = re.split(r'[\s_\-]+', text)
    if not words:
        return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def _to_snake_case(text: str) -> str:
    """Convert text to snake_case.

    Args:
        text: Input text (assumed camelCase or PascalCase or separated).

    Returns:
        snake_case version of the text.
    """
    text = re.sub(r'[\s\-]+', '_', text)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', text)
    text = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', text)
    return text.lower()


def _char_freq(text: str) -> str:
    """Compute character frequency analysis.

    Args:
        text: Input text.

    Returns:
        Formatted frequency report.
    """
    counter = collections.Counter(text)
    total = len(text)
    lines: list[str] = [f"Total characters: {total}", ""]
    for char, count in counter.most_common(30):
        pct = count / total * 100
        if char == "\n":
            display = "\\n"
        elif char == "\t":
            display = "\\t"
        elif char == " ":
            display = "SPACE"
        else:
            display = char
        lines.append(f"  {display:<6} {count:>6} ({pct:.1f}%)")
    return "\n".join(lines)


def _word_freq(text: str) -> str:
    """Compute word frequency analysis.

    Args:
        text: Input text.

    Returns:
        Formatted word frequency report.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    counter = collections.Counter(words)
    total = len(words)
    lines: list[str] = [f"Total words: {total}", ""]
    for word, count in counter.most_common(30):
        pct = count / total * 100
        lines.append(f"  {word:<20} {count:>6} ({pct:.1f}%)")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the transform subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("transform", help="Text transformations (regex, case, wrap, normalize)")
    p.add_argument("--mode", "-m", default="upper", choices=["replace", "upper", "lower", "title", "camel", "snake", "wrap", "dedent", "normalize", "count", "freq", "wordfreq"], help="Transform mode (default: upper)")
    p.add_argument("--pattern", "-p", default=None, help="Regex pattern (replace/count mode)")
    p.add_argument("--replacement", "-r", default="", help="Replacement string (replace mode)")
    p.add_argument("--width", "-w", type=int, default=80, help="Wrap width (default: 80)")
    p.add_argument("--form", default="NFC", choices=["NFC", "NFD", "NFKC", "NFKD"], help="Unicode normalization form (default: NFC)")
    p.add_argument("input", nargs="?", default=None, help="Input file (default: stdin)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the transform subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        text = read_input_text(args.input)
        match args.mode:
            case "replace":
                if not args.pattern:
                    print("error: --pattern required for replace mode", file=sys.stderr)
                    return 1
                result = re.sub(args.pattern, args.replacement, text)
                sys.stdout.write(result)
            case "upper":
                sys.stdout.write(text.upper())
            case "lower":
                sys.stdout.write(text.lower())
            case "title":
                sys.stdout.write(text.title())
            case "camel":
                for line in text.splitlines(keepends=True):
                    sys.stdout.write(_to_camel_case(line.rstrip()) + ("\n" if line.endswith("\n") else ""))
            case "snake":
                for line in text.splitlines(keepends=True):
                    sys.stdout.write(_to_snake_case(line.rstrip()) + ("\n" if line.endswith("\n") else ""))
            case "wrap":
                result = textwrap.fill(text, width=args.width)
                print(result)
            case "dedent":
                sys.stdout.write(textwrap.dedent(text))
            case "normalize":
                result = unicodedata.normalize(args.form, text)
                sys.stdout.write(result)
            case "count":
                if not args.pattern:
                    print("error: --pattern required for count mode", file=sys.stderr)
                    return 1
                matches = re.findall(args.pattern, text)
                print(len(matches))
            case "freq":
                print(_char_freq(text))
            case "wordfreq":
                print(_word_freq(text))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except re.error as e:
        print(f"error: invalid regex: {e}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
