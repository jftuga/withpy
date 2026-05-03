"""WAV audio file metadata inspection and duration calculation.

Reads WAV file headers to display sample rate, channels, bit depth,
duration, and other metadata using the wave and array stdlib modules.
"""

import argparse
import array
import json
import sys
import wave


def _format_duration(seconds: float) -> str:
    """Format seconds as mm:ss.ms string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration string.
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:05.2f}"


def _get_metadata(path: str) -> dict[str, str | int | float]:
    """Extract metadata from a WAV file.

    Args:
        path: Path to the WAV file.

    Returns:
        Dictionary of metadata key-value pairs.

    Raises:
        wave.Error: If the file is not a valid WAV.
        OSError: If the file cannot be read.
    """
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frame_rate = wf.getframerate()
        n_frames = wf.getnframes()
        comp_type = wf.getcomptype()
        comp_name = wf.getcompname()
        duration = n_frames / frame_rate if frame_rate > 0 else 0.0
        return {
            "channels": n_channels,
            "sample_width_bytes": sample_width,
            "bit_depth": sample_width * 8,
            "sample_rate": frame_rate,
            "frames": n_frames,
            "duration_seconds": round(duration, 3),
            "duration": _format_duration(duration),
            "compression_type": comp_type,
            "compression_name": comp_name,
        }


def _get_peaks(path: str) -> dict[str, int | float]:
    """Calculate peak amplitude from a WAV file.

    Args:
        path: Path to the WAV file.

    Returns:
        Dictionary with peak values.

    Raises:
        wave.Error: If the file is not a valid WAV.
    """
    with wave.open(path, "rb") as wf:
        n_frames = wf.getnframes()
        sample_width = wf.getsampwidth()
        raw = wf.readframes(n_frames)
    typecode_map = {1: "b", 2: "h", 4: "i"}
    typecode = typecode_map.get(sample_width)
    if typecode is None:
        return {"error": f"unsupported sample width: {sample_width}"}
    samples = array.array(typecode)
    samples.frombytes(raw)
    if len(samples) == 0:
        return {"peak": 0, "peak_normalized": 0.0}
    peak = max(abs(s) for s in samples)
    max_val = (1 << (sample_width * 8 - 1)) - 1
    return {
        "peak": peak,
        "peak_normalized": round(peak / max_val, 6) if max_val > 0 else 0.0,
        "sample_count": len(samples),
    }


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the wave subcommand with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    p = subparsers.add_parser("wave", help="WAV audio file metadata and duration")
    p.add_argument("--mode", "-m", default="info", choices=["info", "peaks", "json"], help="Operation mode (default: info)")
    p.add_argument("file", help="WAV file to inspect")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the wave subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        match args.mode:
            case "info":
                meta = _get_metadata(args.file)
                for key, val in meta.items():
                    print(f"{key}: {val}")
            case "peaks":
                peaks = _get_peaks(args.file)
                for key, val in peaks.items():
                    print(f"{key}: {val}")
            case "json":
                meta = _get_metadata(args.file)
                print(json.dumps(meta, indent=2))
        return 0
    except wave.Error as e:
        print(f"error: invalid WAV file: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
