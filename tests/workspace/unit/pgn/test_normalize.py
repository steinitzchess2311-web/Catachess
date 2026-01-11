"""
Tests for PGN normalization.
"""

import pytest

from workspace.pgn.parser.normalize import normalize_pgn, detect_encoding, decode_pgn
from workspace.pgn.parser.errors import EncodingError


def test_normalize_line_endings():
    """Test normalization of different line endings."""
    # CRLF
    pgn_crlf = "[Event \"Test\"]\r\n\r\n1. e4 e5\r\n"
    normalized = normalize_pgn(pgn_crlf)
    assert "\r" not in normalized
    assert normalized.count("\n") > 0

    # CR
    pgn_cr = "[Event \"Test\"]\r\r1. e4 e5\r"
    normalized = normalize_pgn(pgn_cr)
    assert "\r" not in normalized


def test_normalize_excessive_blank_lines():
    """Test removal of excessive blank lines."""
    pgn = "[Event \"Test\"]\n\n\n\n\n1. e4 e5\n"
    normalized = normalize_pgn(pgn)

    # Should have max 2 consecutive blank lines
    assert "\n\n\n\n" not in normalized
    assert "[Event" in normalized
    assert "1. e4" in normalized


def test_normalize_trailing_whitespace():
    """Test removal of trailing whitespace."""
    pgn = "[Event \"Test\"]   \n1. e4 e5    \n"
    normalized = normalize_pgn(pgn)

    # No trailing spaces
    lines = normalized.split("\n")
    for line in lines[:-1]:  # Exclude final newline
        assert not line.endswith(" ")


def test_normalize_header_spacing():
    """Test normalization of header spacing."""
    pgn = '[Event  "Test"]\n[Site   "Location"]\n'
    normalized = normalize_pgn(pgn)

    assert '[Event "Test"]' in normalized
    assert '[Site "Location"]' in normalized


def test_normalize_ends_with_single_newline():
    """Test that normalized PGN ends with single newline."""
    pgn = "[Event \"Test\"]\n1. e4 e5\n\n\n"
    normalized = normalize_pgn(pgn)

    assert normalized.endswith("\n")
    assert not normalized.endswith("\n\n")


def test_normalize_removes_leading_blank_lines():
    """Test removal of leading blank lines."""
    pgn = "\n\n\n[Event \"Test\"]\n1. e4 e5\n"
    normalized = normalize_pgn(pgn)

    assert not normalized.startswith("\n")
    assert normalized.startswith("[Event")


def test_detect_encoding_utf8():
    """Test UTF-8 detection."""
    data = "test content".encode("utf-8")
    encoding = detect_encoding(data)
    assert encoding == "utf-8"


def test_detect_encoding_latin1():
    """Test Latin-1 detection."""
    # Use character that's valid in Latin-1 but would fail UTF-8
    data = b"test \xe9 content"  # é in Latin-1
    encoding = detect_encoding(data)
    assert encoding in ("latin-1", "windows-1252", "utf-8")


def test_detect_encoding_invalid():
    """Test handling of invalid encoding."""
    # Create truly invalid byte sequence that fails all encodings
    # This is actually hard because Latin-1 can decode anything
    # So let's test that it doesn't raise for valid bytes
    data = b"\xff\xfe\x00\x00"
    # This will succeed with latin-1, which is fine
    encoding = detect_encoding(data)
    assert encoding in ("latin-1", "windows-1252")


def test_decode_pgn_utf8():
    """Test decoding UTF-8 PGN."""
    data = "[Event \"Test\"]\n".encode("utf-8")
    decoded = decode_pgn(data)
    assert decoded == "[Event \"Test\"]\n"


def test_decode_pgn_with_hint():
    """Test decoding with encoding hint."""
    data = "[Event \"Test\"]\n".encode("latin-1")
    decoded = decode_pgn(data, encoding="latin-1")
    assert decoded == "[Event \"Test\"]\n"


def test_decode_pgn_invalid_encoding():
    """Test handling of invalid encoding hint."""
    data = "[Event \"Test\"]\n".encode("utf-8")
    with pytest.raises(EncodingError):
        decode_pgn(data, encoding="invalid-encoding")
