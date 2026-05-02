"""Tests for the mail subcommand."""

import pytest


_SAMPLE_EML = b"""From: sender@example.com
To: recipient@example.com
CC: cc@example.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 +0000
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

This is the email body.
"""


def test_headers(cli, tmp_file):
    """Headers mode shows email headers."""
    path = tmp_file(_SAMPLE_EML, name="test.eml")
    result = cli("mail", "--mode", "headers", str(path))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "From:" in output
    assert "sender@example.com" in output
    assert "Subject:" in output


def test_specific_header(cli, tmp_file):
    """Extracting a specific header."""
    path = tmp_file(_SAMPLE_EML, name="test.eml")
    result = cli("mail", "--mode", "headers", "--header", "Subject", str(path))
    assert result.returncode == 0
    assert "Test Email" in result.stdout.decode()


def test_body(cli, tmp_file):
    """Body mode shows email body text."""
    path = tmp_file(_SAMPLE_EML, name="test.eml")
    result = cli("mail", "--mode", "body", str(path))
    assert result.returncode == 0
    assert "email body" in result.stdout.decode()


def test_addresses(cli, tmp_file):
    """Addresses mode extracts email addresses."""
    path = tmp_file(_SAMPLE_EML, name="test.eml")
    result = cli("mail", "--mode", "addresses", str(path))
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "sender@example.com" in output
    assert "recipient@example.com" in output
    assert "cc@example.com" in output


def test_nonexistent_file(cli):
    """Non-existent file produces error."""
    result = cli("mail", "--mode", "headers", "/nonexistent/file.eml")
    assert result.returncode == 1
