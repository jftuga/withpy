"""Unicode character lookup, normalization, and category analysis.

Provides modes for looking up characters by codepoint or name, searching
by name substring, displaying Unicode categories, normalizing text forms,
and computing character category statistics.
"""

import argparse
import sys
import unicodedata

from withpy.commands.shared import read_input_text


def _char_info(char: str) -> str:
    """Get detailed information about a Unicode character.

    Args:
        char: A single character.

    Returns:
        Formatted character information.
    """
    code = ord(char)
    try:
        name = unicodedata.name(char)
    except ValueError:
        name = "<unnamed>"
    category = unicodedata.category(char)
    utf8_hex = " ".join(f"{b:02x}" for b in char.encode("utf-8"))
    lines = [
        f"char:     {char}",
        f"code:     U+{code:04X}",
        f"name:     {name}",
        f"category: {category}",
        f"utf-8:    {utf8_hex}",
    ]
    bidi = unicodedata.bidirectional(char)
    if bidi:
        lines.append(f"bidi:     {bidi}")
    return "\n".join(lines)


def _lookup_codepoint(value: str) -> str:
    """Look up a character by codepoint (U+XXXX) or literal character.

    Args:
        value: Codepoint string like "U+0041" or a single character.

    Returns:
        Formatted character information.

    Raises:
        ValueError: If codepoint is invalid.
    """
    if value.upper().startswith("U+"):
        try:
            code = int(value[2:], 16)
            char = chr(code)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"invalid codepoint: {value}") from e
    elif len(value) == 1:
        char = value
    else:
        try:
            char = unicodedata.lookup(value)
        except KeyError:
            raise ValueError(f"character not found: {value}") from None
    return _char_info(char)


def _search_by_name(pattern: str) -> str:
    """Search Unicode characters by name substring.

    Args:
        pattern: Substring to search for in character names.

    Returns:
        Formatted list of matching characters (limited to 50).
    """
    pattern_upper = pattern.upper()
    matches: list[str] = []
    for code in range(0x10FFFF + 1):
        try:
            char = chr(code)
            name = unicodedata.name(char)
            if pattern_upper in name:
                matches.append(f"U+{code:04X}  {char}  {name}")
                if len(matches) >= 50:
                    break
        except (ValueError, OverflowError):
            continue
    if not matches:
        return f"no characters found matching: {pattern}"
    return "\n".join(matches)


def _category_stats(text: str) -> str:
    """Compute Unicode category statistics for text.

    Args:
        text: Input text to analyze.

    Returns:
        Formatted category statistics.
    """
    categories: dict[str, int] = {}
    for char in text:
        cat = unicodedata.category(char)
        categories[cat] = categories.get(cat, 0) + 1
    total = len(text)
    lines = [f"Total characters: {total}", ""]
    _CATEGORY_NAMES: dict[str, str] = {
        "Lu": "Uppercase Letter", "Ll": "Lowercase Letter",
        "Lt": "Titlecase Letter", "Lm": "Modifier Letter",
        "Lo": "Other Letter", "Mn": "Nonspacing Mark",
        "Nd": "Decimal Number", "Nl": "Letter Number",
        "Pc": "Connector Punctuation", "Pd": "Dash Punctuation",
        "Ps": "Open Punctuation", "Pe": "Close Punctuation",
        "Po": "Other Punctuation", "Sm": "Math Symbol",
        "Sc": "Currency Symbol", "Zs": "Space Separator",
        "Zl": "Line Separator", "Zp": "Paragraph Separator",
        "Cc": "Control", "Cf": "Format",
    }
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        name = _CATEGORY_NAMES.get(cat, cat)
        pct = count / total * 100
        lines.append(f"  {cat} ({name}): {count} ({pct:.1f}%)")
    return "\n".join(lines)


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the unicode subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("unicode", help="Unicode character lookup, normalization, stats")
    p.add_argument("--mode", "-m", default="lookup", choices=["lookup", "name", "category", "normalize", "stats"], help="Operation mode (default: lookup)")
    p.add_argument("--form", default="NFC", choices=["NFC", "NFD", "NFKC", "NFKD"], help="Normalization form (default: NFC)")
    p.add_argument("value", nargs="?", default=None, help="Character, codepoint (U+XXXX), or name to search")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the unicode subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "lookup":
                if not args.value:
                    print("error: value required for lookup mode", file=sys.stderr)
                    return 1
                print(_lookup_codepoint(args.value))
            case "name":
                if not args.value:
                    print("error: search pattern required for name mode", file=sys.stderr)
                    return 1
                print(_search_by_name(args.value))
            case "category":
                if not args.value:
                    text = read_input_text(None)
                else:
                    text = args.value
                print(_category_stats(text))
            case "normalize":
                if args.value:
                    text = args.value
                else:
                    text = read_input_text(None)
                result = unicodedata.normalize(args.form, text)
                sys.stdout.write(result)
            case "stats":
                if args.value:
                    text = args.value
                else:
                    text = read_input_text(None)
                print(_category_stats(text))
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
