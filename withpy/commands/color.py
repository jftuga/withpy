"""Color space conversions between RGB, HSL, HSV, and HEX formats.

Provides conversion between color representations, palette generation
with evenly-spaced hues, and color blending/interpolation using the
colorsys standard library module.
"""

import argparse
import colorsys
import sys


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB tuple.

    Args:
        hex_str: Hex color like "#FF0000" or "FF0000".

    Returns:
        Tuple of (R, G, B) integers 0-255.

    Raises:
        ValueError: If the hex string is invalid.
    """
    h = hex_str.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"invalid hex color: {hex_str} (expected 6 hex digits)")
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        raise ValueError(f"invalid hex color: {hex_str}") from None


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers to hex string.

    Args:
        r: Red component 0-255.
        g: Green component 0-255.
        b: Blue component 0-255.

    Returns:
        Hex color string like "#ff0000".
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def _parse_rgb(value: str) -> tuple[int, int, int]:
    """Parse an RGB string like "255,0,0".

    Args:
        value: Comma-separated RGB values.

    Returns:
        Tuple of (R, G, B) integers.

    Raises:
        ValueError: If format is invalid or values out of range.
    """
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError(f"invalid RGB format: {value} (expected R,G,B)")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
        raise ValueError(f"RGB values must be 0-255, got: {r},{g},{b}")
    return (r, g, b)


def _parse_hsl(value: str) -> tuple[float, float, float]:
    """Parse an HSL string like "360,100,50".

    Args:
        value: Comma-separated H,S,L values (H: 0-360, S/L: 0-100).

    Returns:
        Tuple of (H, S, L) as normalized floats (0-1).

    Raises:
        ValueError: If format is invalid.
    """
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError(f"invalid HSL format: {value} (expected H,S,L)")
    h, s, l = float(parts[0]), float(parts[1]), float(parts[2])
    return (h / 360.0, s / 100.0, l / 100.0)


def _parse_hsv(value: str) -> tuple[float, float, float]:
    """Parse an HSV string like "360,100,100".

    Args:
        value: Comma-separated H,S,V values (H: 0-360, S/V: 0-100).

    Returns:
        Tuple of (H, S, V) as normalized floats (0-1).

    Raises:
        ValueError: If format is invalid.
    """
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError(f"invalid HSV format: {value} (expected H,S,V)")
    h, s, v = float(parts[0]), float(parts[1]), float(parts[2])
    return (h / 360.0, s / 100.0, v / 100.0)


def _to_rgb(value: str, from_space: str) -> tuple[int, int, int]:
    """Convert a color value from any space to RGB.

    Args:
        value: Color value string.
        from_space: Source color space.

    Returns:
        RGB tuple (0-255 each).

    Raises:
        ValueError: If color space or value is invalid.
    """
    match from_space:
        case "hex":
            return _hex_to_rgb(value)
        case "rgb":
            return _parse_rgb(value)
        case "hsl":
            h, s, l = _parse_hsl(value)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return (round(r * 255), round(g * 255), round(b * 255))
        case "hsv":
            h, s, v = _parse_hsv(value)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return (round(r * 255), round(g * 255), round(b * 255))
        case _:
            raise ValueError(f"unknown color space: {from_space}")


def _from_rgb(r: int, g: int, b: int, to_space: str) -> str:
    """Convert RGB to the target color space string.

    Args:
        r: Red 0-255.
        g: Green 0-255.
        b: Blue 0-255.
        to_space: Target color space.

    Returns:
        Formatted color string.
    """
    match to_space:
        case "hex":
            return _rgb_to_hex(r, g, b)
        case "rgb":
            return f"{r},{g},{b}"
        case "hsl":
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            return f"{h * 360:.0f},{s * 100:.0f},{l * 100:.0f}"
        case "hsv":
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            return f"{h * 360:.0f},{s * 100:.0f},{v * 100:.0f}"
        case "all":
            lines = [
                f"hex: {_rgb_to_hex(r, g, b)}",
                f"rgb: {r},{g},{b}",
            ]
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            lines.append(f"hsl: {h * 360:.0f},{s * 100:.0f},{l * 100:.0f}")
            h2, s2, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            lines.append(f"hsv: {h2 * 360:.0f},{s2 * 100:.0f},{v * 100:.0f}")
            return "\n".join(lines)
        case _:
            return _rgb_to_hex(r, g, b)


def _generate_palette(steps: int, saturation: float, lightness: float) -> list[str]:
    """Generate a palette of evenly-spaced hues.

    Args:
        steps: Number of colors to generate.
        saturation: HSL saturation (0-1).
        lightness: HSL lightness (0-1).

    Returns:
        List of hex color strings.
    """
    colors: list[str] = []
    for i in range(steps):
        h = i / steps
        r, g, b = colorsys.hls_to_rgb(h, lightness, saturation)
        colors.append(_rgb_to_hex(round(r * 255), round(g * 255), round(b * 255)))
    return colors


def _blend_colors(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int], steps: int) -> list[str]:
    """Interpolate between two colors in RGB space.

    Args:
        rgb1: Start color as RGB tuple.
        rgb2: End color as RGB tuple.
        steps: Number of interpolation steps.

    Returns:
        List of hex color strings.
    """
    colors: list[str] = []
    for i in range(steps):
        t = i / max(steps - 1, 1)
        r = round(rgb1[0] + (rgb2[0] - rgb1[0]) * t)
        g = round(rgb1[1] + (rgb2[1] - rgb1[1]) * t)
        b = round(rgb1[2] + (rgb2[2] - rgb1[2]) * t)
        colors.append(_rgb_to_hex(r, g, b))
    return colors


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the color subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("color", help="Color space conversions (RGB/HSL/HSV/HEX)")
    p.add_argument("--mode", "-m", default="convert", choices=["convert", "palette", "blend"], help="Operation mode (default: convert)")
    p.add_argument("--from", dest="from_space", default="hex", choices=["hex", "rgb", "hsl", "hsv"], help="Source color space (default: hex)")
    p.add_argument("--to", dest="to_space", default="hex", choices=["hex", "rgb", "hsl", "hsv", "all"], help="Target color space (default: hex)")
    p.add_argument("--steps", type=int, default=5, help="Steps for palette/blend (default: 5)")
    p.add_argument("--saturation", type=float, default=100.0, help="Saturation for palette (0-100, default: 100)")
    p.add_argument("--lightness", type=float, default=50.0, help="Lightness for palette (0-100, default: 50)")
    p.add_argument("colors", nargs="*", help="Color values")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the color subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "convert":
                if not args.colors:
                    print("error: at least one color value required", file=sys.stderr)
                    return 1
                for color in args.colors:
                    rgb = _to_rgb(color, args.from_space)
                    print(_from_rgb(*rgb, args.to_space))
            case "palette":
                colors = _generate_palette(args.steps, args.saturation / 100.0, args.lightness / 100.0)
                for c in colors:
                    print(c)
            case "blend":
                if len(args.colors) < 2:
                    print("error: blend requires exactly 2 colors", file=sys.stderr)
                    return 1
                rgb1 = _to_rgb(args.colors[0], args.from_space)
                rgb2 = _to_rgb(args.colors[1], args.from_space)
                colors = _blend_colors(rgb1, rgb2, args.steps)
                for c in colors:
                    print(c)
            case _:
                print(f"error: unknown mode: {args.mode}", file=sys.stderr)
                return 1
        return 0
    except (ValueError, IndexError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
