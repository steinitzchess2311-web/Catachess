"""
PGN normalization utilities.

Standardizes PGN format for consistent parsing.
"""

import re
from typing import BinaryIO

from .errors import EncodingError


def normalize_pgn(content: str) -> str:
    """
    Normalize PGN content for consistent parsing.

    Operations:
    - Converts all line endings to \n
    - Removes excessive blank lines (max 2 consecutive)
    - Strips trailing whitespace from lines
    - Ensures file ends with single newline
    - Normalizes spaces around brackets and tags

    Args:
        content: Raw PGN content

    Returns:
        Normalized PGN content
    """
    # Normalize line endings (CRLF, CR -> LF)
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Split into lines
    lines = content.split("\n")

    # Process each line
    normalized_lines = []
    blank_count = 0

    for line in lines:
        # Strip trailing whitespace
        line = line.rstrip()

        # Track blank lines (max 2 consecutive)
        if not line:
            blank_count += 1
            if blank_count <= 2:
                normalized_lines.append(line)
        else:
            blank_count = 0
            normalized_lines.append(line)

    # Join lines
    result = "\n".join(normalized_lines)

    # Remove leading blank lines
    result = result.lstrip("\n")

    # Ensure single trailing newline
    result = result.rstrip("\n") + "\n"

    # Normalize spaces in headers: [Event  "Title"] -> [Event "Title"]
    result = re.sub(r'\[(\w+)\s+"', r'[\1 "', result)

    return result


def detect_encoding(data: bytes) -> str:
    """
    Detect PGN file encoding.

    Tries UTF-8, then Latin-1, then other common encodings.

    Args:
        data: Raw file bytes

    Returns:
        Detected encoding name

    Raises:
        EncodingError: If encoding cannot be detected
    """
    # Try UTF-8 first (most common)
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # Try Latin-1 (ISO-8859-1) - common for older PGN files
    try:
        data.decode("latin-1")
        return "latin-1"
    except UnicodeDecodeError:
        pass

    # Try Windows-1252 (common in ChessBase)
    try:
        data.decode("windows-1252")
        return "windows-1252"
    except UnicodeDecodeError:
        pass

    raise EncodingError("Unable to detect PGN encoding")


def decode_pgn(data: bytes, encoding: str | None = None) -> str:
    """
    Decode PGN bytes to string.

    Args:
        data: Raw PGN bytes
        encoding: Optional encoding hint

    Returns:
        Decoded PGN string

    Raises:
        EncodingError: If decoding fails
    """
    if encoding:
        # Try specified encoding
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError) as e:
            raise EncodingError(
                f"Failed to decode PGN with encoding {encoding}"
            ) from e

    # Auto-detect encoding
    detected = detect_encoding(data)
    try:
        return data.decode(detected)
    except UnicodeDecodeError as e:
        raise EncodingError(f"Failed to decode PGN with encoding {detected}") from e


def normalize_pgn_file(file: BinaryIO, encoding: str | None = None) -> str:
    """
    Read and normalize PGN from file.

    Args:
        file: Binary file object
        encoding: Optional encoding hint

    Returns:
        Normalized PGN content
    """
    data = file.read()
    content = decode_pgn(data, encoding)
    return normalize_pgn(content)
