"""
PGN input normalization utilities.
"""


def normalize_pgn(pgn_text: str) -> str:
    """
    Normalize PGN input for consistent parsing.

    - Converts CRLF and CR line endings to LF.
    - Trims trailing whitespace from each line.
    - Preserves content and structure.

    Args:
        pgn_text: Raw PGN input string.

    Returns:
        Normalized PGN string with LF line endings.
    """
    if not pgn_text:
        return ""

    # Normalize line endings: CRLF -> LF, CR -> LF
    text = pgn_text.replace('\r\n', '\n').replace('\r', '\n')

    # Trim trailing whitespace from each line while preserving content
    lines = text.split('\n')
    normalized_lines = [line.rstrip() for line in lines]

    return '\n'.join(normalized_lines)
