"""Tests for the hash subcommand.

Covers known-value digests, HMAC mode, checksum verification, stdin input,
multiple algorithm coverage, and error paths.
"""

import pytest


_SHA256_HELLO = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
_MD5_HELLO = "5d41402abc4b2a76b9719d911017c592"
_CRC32_HELLO = "3610a686"
_ADLER32_HELLO = "062c0215"


def test_sha256_known_value(cli, tmp_file):
    """SHA-256 of 'hello' matches the known digest."""
    f = tmp_file("hello")
    result = cli("hash", "--algo", "sha256", str(f))
    assert result.returncode == 0
    assert result.stdout.decode().startswith(_SHA256_HELLO)


def test_md5_known_value(cli, tmp_file):
    """MD5 of 'hello' matches the known digest."""
    f = tmp_file("hello")
    result = cli("hash", "--algo", "md5", str(f))
    assert result.returncode == 0
    assert result.stdout.decode().startswith(_MD5_HELLO)


def test_crc32_known_value(cli, tmp_file):
    """CRC32 of 'hello' matches the known checksum."""
    f = tmp_file("hello")
    result = cli("hash", "--algo", "crc32", str(f))
    assert result.returncode == 0
    assert result.stdout.decode().startswith(_CRC32_HELLO)


def test_adler32_known_value(cli, tmp_file):
    """Adler32 of 'hello' matches the known checksum."""
    f = tmp_file("hello")
    result = cli("hash", "--algo", "adler32", str(f))
    assert result.returncode == 0
    assert result.stdout.decode().startswith(_ADLER32_HELLO)


_ALL_ALGOS = [
    "md5", "sha1", "sha224", "sha256", "sha384", "sha512",
    "sha3_256", "sha3_512", "blake2b", "blake2s", "crc32", "adler32",
]


@pytest.mark.parametrize("algo", _ALL_ALGOS)
def test_all_algorithms_produce_output(cli, tmp_file, algo):
    """Every supported algorithm produces non-empty hex output."""
    f = tmp_file("test data")
    result = cli("hash", "--algo", algo, str(f))
    assert result.returncode == 0
    line = result.stdout.decode().strip()
    digest = line.split("  ")[0]
    assert len(digest) > 0
    assert all(c in "0123456789abcdef" for c in digest)


def test_stdin_input(cli):
    """Hashing stdin produces the correct digest."""
    result = cli("hash", "--algo", "sha256", input_data="hello")
    assert result.returncode == 0
    assert result.stdout.decode().startswith(_SHA256_HELLO)
    assert "(stdin)" in result.stdout.decode()


def test_hmac_differs_from_plain(cli, tmp_file):
    """HMAC digest differs from plain digest for the same input."""
    f = tmp_file("hello")
    plain = cli("hash", "--algo", "sha256", str(f))
    hmac_result = cli("hash", "--algo", "sha256", "--hmac", "secret", str(f))
    assert plain.returncode == 0
    assert hmac_result.returncode == 0
    plain_digest = plain.stdout.decode().split("  ")[0]
    hmac_digest = hmac_result.stdout.decode().split("  ")[0]
    assert plain_digest != hmac_digest


def test_hmac_deterministic(cli, tmp_file):
    """Same HMAC key and input produce the same digest."""
    f = tmp_file("hello")
    r1 = cli("hash", "--algo", "sha256", "--hmac", "key1", str(f))
    r2 = cli("hash", "--algo", "sha256", "--hmac", "key1", str(f))
    assert r1.stdout == r2.stdout


def test_hmac_different_keys(cli, tmp_file):
    """Different HMAC keys produce different digests."""
    f = tmp_file("hello")
    r1 = cli("hash", "--algo", "sha256", "--hmac", "key1", str(f))
    r2 = cli("hash", "--algo", "sha256", "--hmac", "key2", str(f))
    d1 = r1.stdout.decode().split("  ")[0]
    d2 = r2.stdout.decode().split("  ")[0]
    assert d1 != d2


def test_hmac_rejected_for_crc(cli, tmp_file):
    """HMAC with CRC32 produces an error."""
    f = tmp_file("hello")
    result = cli("hash", "--algo", "crc32", "--hmac", "key", str(f))
    assert result.returncode == 1
    assert b"not supported" in result.stderr.lower()


def test_check_mode(cli, tmp_file, tmp_path):
    """Check mode verifies hashes from a checksum file."""
    data_file = tmp_file("hello", name="data.txt")
    checksum_file = tmp_path / "checksums.txt"
    checksum_file.write_text(f"{_SHA256_HELLO}  {data_file}\n")
    result = cli("hash", "--algo", "sha256", "--check", str(checksum_file))
    assert result.returncode == 0
    assert "OK" in result.stdout.decode()


def test_check_mode_failure(cli, tmp_file, tmp_path):
    """Check mode reports FAILED for a wrong hash."""
    data_file = tmp_file("hello", name="data.txt")
    checksum_file = tmp_path / "checksums.txt"
    checksum_file.write_text(f"{'0' * 64}  {data_file}\n")
    result = cli("hash", "--algo", "sha256", "--check", str(checksum_file))
    assert result.returncode == 1
    assert "FAILED" in result.stdout.decode()


def test_missing_file(cli):
    """Nonexistent file path produces an error."""
    result = cli("hash", "/nonexistent/path/file.txt")
    assert result.returncode == 1
    assert result.stderr


def test_multiple_files(cli, tmp_file, tmp_path):
    """Hashing multiple files produces one line per file."""
    f1 = tmp_file("aaa", name="a.txt")
    f2 = tmp_file("bbb", name="b.txt")
    result = cli("hash", "--algo", "sha256", str(f1), str(f2))
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 2
