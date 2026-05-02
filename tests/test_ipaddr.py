"""Tests for the ipaddr subcommand."""

import pytest


def test_info_ipv4(cli):
    """Info mode shows network details for /24."""
    result = cli("ipaddr", "--mode", "info", "192.168.1.0/24")
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "254" in output
    assert "192.168.1.255" in output


def test_contains_true(cli):
    """Contains mode detects address in network."""
    result = cli("ipaddr", "--mode", "contains", "10.0.0.0/8", "10.1.2.3")
    assert result.returncode == 0
    assert "is in" in result.stdout.decode()


def test_contains_false(cli):
    """Contains mode detects address not in network."""
    result = cli("ipaddr", "--mode", "contains", "192.168.0.0/24", "10.0.0.1")
    assert result.returncode == 0
    assert "NOT in" in result.stdout.decode()


def test_overlap_true(cli):
    """Overlap mode detects overlapping networks."""
    result = cli("ipaddr", "--mode", "overlap", "192.168.0.0/16", "192.168.1.0/24")
    assert result.returncode == 0
    assert "overlaps" in result.stdout.decode()


def test_overlap_false(cli):
    """Overlap mode detects non-overlapping networks."""
    result = cli("ipaddr", "--mode", "overlap", "10.0.0.0/8", "192.168.0.0/16")
    assert result.returncode == 0
    assert "NOT overlap" in result.stdout.decode()


def test_split(cli):
    """Split /24 into /26 produces 4 subnets."""
    result = cli("ipaddr", "--mode", "split", "--prefix", "26", "192.168.1.0/24")
    assert result.returncode == 0
    lines = result.stdout.decode().strip().splitlines()
    assert len(lines) == 4


def test_summarize(cli):
    """Summarize collapses contiguous addresses."""
    result = cli("ipaddr", "--mode", "summarize", "192.168.0.0/24", "192.168.1.0/24")
    assert result.returncode == 0
    output = result.stdout.decode().strip()
    assert "192.168.0.0/23" in output


def test_invalid_address(cli):
    """Invalid CIDR notation produces error."""
    result = cli("ipaddr", "--mode", "info", "not.an.ip/address")
    assert result.returncode == 1
