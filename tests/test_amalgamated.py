"""Subprocess integration tests against the amalgamated dist/withpy artifact.

Each test spawns dist/withpy as a subprocess and verifies a representative
path from each implemented subcommand. All tests are skipped if the artifact
has not been built.
"""

import pytest


def test_version(amalgamated):
    """Amalgamated artifact reports its version."""
    result = amalgamated("--version")
    assert result.returncode == 0
    assert b"withpy" in result.stdout


def test_hash(amalgamated):
    """Amalgamated artifact hashes stdin correctly."""
    result = amalgamated("hash", "--algo", "sha256", input_data=b"hello")
    assert result.returncode == 0
    assert b"2cf24dba5fb0a30e26e83b2ac5b9e29e" in result.stdout


def test_encode_decode_roundtrip(amalgamated):
    """Amalgamated artifact round-trips base64 encoding."""
    enc = amalgamated("encode", "--format", "base64", input_data=b"roundtrip test")
    assert enc.returncode == 0
    dec = amalgamated("decode", "--format", "base64", input_data=enc.stdout.strip())
    assert dec.returncode == 0
    assert dec.stdout.strip() == b"roundtrip test"


def test_time_now(amalgamated):
    """Amalgamated artifact shows current time with expected labels."""
    result = amalgamated("time", "--mode", "now")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "Local:" in output
    assert "UTC:" in output
    assert "Epoch:" in output


def test_time_fromepoch(amalgamated):
    """Amalgamated artifact converts epoch 0 correctly."""
    result = amalgamated("time", "--mode", "fromepoch", "0")
    assert result.returncode == 0
    assert b"1970-01-01" in result.stdout


def test_help(amalgamated):
    """Amalgamated artifact shows help text with all commands."""
    result = amalgamated("--help")
    assert result.returncode == 0
    assert b"hash" in result.stdout
    assert b"encode" in result.stdout
    assert b"time" in result.stdout
    assert b"generate" in result.stdout
    assert b"json" in result.stdout
    assert b"compress" in result.stdout


def test_generate_uuid(amalgamated):
    """Amalgamated artifact generates a UUID."""
    result = amalgamated("generate", "--mode", "uuid")
    assert result.returncode == 0
    uuid = result.stdout.decode().strip()
    assert len(uuid) == 36
    assert uuid.count("-") == 4


def test_jwt_decode(amalgamated):
    """Amalgamated artifact decodes a JWT."""
    token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.fake"
    result = amalgamated("jwt", token)
    assert result.returncode == 0
    assert b"test" in result.stdout


def test_json_pretty(amalgamated):
    """Amalgamated artifact pretty-prints JSON."""
    result = amalgamated("json", "--mode", "pretty", input_data=b'{"a":1}')
    assert result.returncode == 0
    assert b'"a": 1' in result.stdout


def test_compress_roundtrip(amalgamated):
    """Amalgamated artifact round-trips gzip compression."""
    enc = amalgamated("compress", "--format", "gzip", input_data=b"hello world")
    assert enc.returncode == 0
    dec = amalgamated("compress", "--mode", "decompress", "--format", "gzip", input_data=enc.stdout)
    assert dec.returncode == 0
    assert dec.stdout == b"hello world"


def test_hexdump(amalgamated):
    """Amalgamated artifact produces hex dump."""
    result = amalgamated("hexdump", input_data=b"Hello")
    assert result.returncode == 0
    assert b"48 65 6c 6c 6f" in result.stdout


def test_url_parse(amalgamated):
    """Amalgamated artifact parses URLs."""
    result = amalgamated("url", "--mode", "parse", "https://example.com/path?q=1")
    assert result.returncode == 0
    assert b"example.com" in result.stdout


def test_calc_expr(amalgamated):
    """Amalgamated artifact evaluates expressions."""
    result = amalgamated("calc", "2+2")
    assert result.returncode == 0
    assert b"4" in result.stdout


def test_color_convert(amalgamated):
    """Amalgamated artifact converts colors."""
    result = amalgamated("color", "--from", "hex", "--to", "rgb", "#FF0000")
    assert result.returncode == 0
    assert b"255,0,0" in result.stdout


def test_toml_tojson(amalgamated):
    """Amalgamated artifact converts TOML to JSON."""
    result = amalgamated("toml", input_data=b'[section]\nkey = "value"\n')
    assert result.returncode == 0
    assert b"section" in result.stdout


def test_transform_upper(amalgamated):
    """Amalgamated artifact transforms text to upper."""
    result = amalgamated("transform", "--mode", "upper", input_data=b"hello")
    assert result.returncode == 0
    assert result.stdout.strip() == b"HELLO"


def test_ipaddr_info(amalgamated):
    """Amalgamated artifact shows IP info."""
    result = amalgamated("ipaddr", "--mode", "info", "192.168.1.0/24")
    assert result.returncode == 0
    assert b"254" in result.stdout


def test_csv_tojson(amalgamated):
    """Amalgamated artifact converts CSV to JSON."""
    result = amalgamated("csv", "--mode", "tojson", input_data=b"name,age\nalice,30\n")
    assert result.returncode == 0
    assert b"alice" in result.stdout


def test_deps_sort(amalgamated):
    """Amalgamated artifact sorts dependencies."""
    graph = b'{"a": ["b"], "b": ["c"], "c": []}'
    result = amalgamated("deps", "--mode", "sort", input_data=graph)
    assert result.returncode == 0
    assert b"c" in result.stdout


def test_info_os(amalgamated):
    """Amalgamated artifact shows OS info."""
    result = amalgamated("info", "--mode", "os")
    assert result.returncode == 0
    assert len(result.stdout) > 0


def test_calendar_weekday(amalgamated):
    """Amalgamated artifact computes weekday."""
    result = amalgamated("calendar", "--mode", "weekday", "2024-01-01")
    assert result.returncode == 0
    assert b"Monday" in result.stdout


def test_net_resolve(amalgamated):
    """Amalgamated artifact resolves DNS."""
    result = amalgamated("net", "--mode", "resolve", "--host", "localhost")
    assert result.returncode == 0
    assert b"127.0.0.1" in result.stdout or b"::1" in result.stdout


def test_config_sections(amalgamated):
    """Amalgamated artifact lists INI sections."""
    result = amalgamated("config", "--mode", "sections", input_data=b"[sec1]\nkey=val\n[sec2]\na=b\n")
    assert result.returncode == 0
    assert b"sec1" in result.stdout
    assert b"sec2" in result.stdout


def test_shlex_split(amalgamated):
    """Amalgamated artifact splits shell commands."""
    result = amalgamated("shlex", "--mode", "split", "echo", "hello world")
    assert result.returncode == 0
    assert b"echo" in result.stdout


def test_random_int(amalgamated):
    """Amalgamated artifact generates random integers."""
    result = amalgamated("random", "--mode", "int", "--min", "5", "--max", "5", "--seed", "1")
    assert result.returncode == 0
    assert b"5" in result.stdout


def test_tokenize_source(amalgamated):
    """Amalgamated artifact tokenizes Python source."""
    result = amalgamated("tokenize", "--mode", "stats", input_data=b"x = 1\n")
    assert result.returncode == 0
    assert b"NAME" in result.stdout


def test_transform_dedent(amalgamated):
    """Amalgamated artifact dedents text."""
    result = amalgamated("transform", "--mode", "dedent", input_data=b"    hello\n    world\n")
    assert result.returncode == 0
    assert result.stdout.replace(b"\r\n", b"\n").strip() == b"hello\nworld"


def test_info_disk(amalgamated):
    """Amalgamated artifact shows disk info."""
    result = amalgamated("info", "--mode", "disk")
    assert result.returncode == 0
    assert b"root_total" in result.stdout
