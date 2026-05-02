"""Tests for the wave subcommand."""

import struct
import tempfile
import wave

import pytest


def _make_wav(tmp_path, channels=1, sampwidth=2, framerate=44100, nframes=100):
    """Create a minimal WAV file for testing."""
    path = str(tmp_path / "test.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        data = b"\x00" * (nframes * channels * sampwidth)
        wf.writeframes(data)
    return path


def test_info(cli, tmp_path):
    """Wave info shows metadata."""
    path = _make_wav(tmp_path)
    result = cli("wave", "--mode", "info", path)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "channels: 1" in output
    assert "sample_rate: 44100" in output


def test_json(cli, tmp_path):
    """Wave json mode outputs valid JSON."""
    path = _make_wav(tmp_path)
    result = cli("wave", "--mode", "json", path)
    assert result.returncode == 0
    assert b'"channels": 1' in result.stdout


def test_peaks(cli, tmp_path):
    """Wave peaks mode returns peak info."""
    path = _make_wav(tmp_path, nframes=50)
    result = cli("wave", "--mode", "peaks", path)
    assert result.returncode == 0
    assert b"peak:" in result.stdout


def test_invalid_file(cli, tmp_path):
    """Wave rejects non-WAV files."""
    path = str(tmp_path / "bad.wav")
    with open(path, "wb") as f:
        f.write(b"not a wav file")
    result = cli("wave", "--mode", "info", path)
    assert result.returncode == 1
