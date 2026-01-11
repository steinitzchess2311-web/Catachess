"""
PGN game splitting utilities.

Splits multi-game PGN content into individual games.
"""

import re
from dataclasses import dataclass

from .errors import EmptyPGNError, InvalidPGNFormatError


@dataclass
class PGNGame:
    """
    Represents a single PGN game.

    Attributes:
        headers: Dict of PGN headers (Event, Site, Date, etc.)
        moves: Move text including variations and comments
        raw_content: Original PGN text for this game
        game_number: Sequential game number (1-based)
    """

    headers: dict[str, str]
    moves: str
    raw_content: str
    game_number: int

    @property
    def event(self) -> str:
        """Get Event header."""
        return self.headers.get("Event", "Unknown")

    @property
    def white(self) -> str:
        """Get White player."""
        return self.headers.get("White", "?")

    @property
    def black(self) -> str:
        """Get Black player."""
        return self.headers.get("Black", "?")

    @property
    def date(self) -> str:
        """Get game date."""
        return self.headers.get("Date", "????.??.??")

    @property
    def result(self) -> str:
        """Get game result."""
        return self.headers.get("Result", "*")


def split_games(pgn_content: str) -> list[PGNGame]:
    """
    Split multi-game PGN content into individual games.

    PGN format structure:
    [Event "Title"]
    [Site "Location"]
    ...other headers...

    1. e4 e5 2. Nf3 ... *

    [Event "Title 2"]
    ...

    Args:
        pgn_content: Normalized PGN content

    Returns:
        List of PGNGame objects

    Raises:
        EmptyPGNError: If no games found
        InvalidPGNFormatError: If PGN format is invalid
    """
    if not pgn_content or not pgn_content.strip():
        raise EmptyPGNError("PGN content is empty")

    games = []
    lines = pgn_content.split("\n")

    current_headers: dict[str, str] = {}
    current_moves: list[str] = []
    current_raw: list[str] = []
    in_headers = False
    game_count = 0

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Detect header line: [TagName "Value"]
        if stripped.startswith("[") and stripped.endswith("]"):
            # If we were collecting moves, this is a new game
            if current_moves and not in_headers:
                # Save previous game
                _save_game(
                    games,
                    current_headers,
                    current_moves,
                    current_raw,
                    game_count,
                )
                game_count += 1

                # Reset for new game
                current_headers = {}
                current_moves = []
                current_raw = []

            # Parse header
            in_headers = True
            current_raw.append(line)

            header_match = re.match(r'\[(\w+)\s+"(.*)"\]', stripped)
            if header_match:
                tag, value = header_match.groups()
                current_headers[tag] = value
            else:
                # Malformed header - try to be lenient
                tag_match = re.match(r"\[(\w+)\s+", stripped)
                if tag_match:
                    tag = tag_match.group(1)
                    # Extract value between quotes
                    value_match = re.search(r'"(.*)"', stripped)
                    if value_match:
                        current_headers[tag] = value_match.group(1)

        # Empty line or whitespace
        elif not stripped:
            if in_headers and current_headers:
                # End of headers section
                in_headers = False
            current_raw.append(line)

        # Move text
        else:
            if not current_headers:
                # Moves without headers - this might be a continuation
                # or a malformed PGN
                if not games:
                    raise InvalidPGNFormatError(
                        "PGN starts with moves but has no headers",
                        line_number=line_num,
                        context=stripped[:50],
                    )

            in_headers = False
            current_moves.append(line)
            current_raw.append(line)

    # Save last game if exists
    if current_headers or current_moves:
        _save_game(
            games,
            current_headers,
            current_moves,
            current_raw,
            game_count,
        )

    if not games:
        raise EmptyPGNError("No games found in PGN content")

    return games


def _save_game(
    games: list[PGNGame],
    headers: dict[str, str],
    moves: list[str],
    raw: list[str],
    game_count: int,
) -> None:
    """
    Save current game to games list.

    Args:
        games: List to append to
        headers: Game headers
        moves: Game moves
        raw: Raw content lines
        game_count: Current game number
    """
    if not headers and not moves:
        return

    # Join moves, normalize spacing
    moves_text = "\n".join(moves).strip()

    # Join raw content
    raw_content = "\n".join(raw).strip()

    game = PGNGame(
        headers=headers.copy(),
        moves=moves_text,
        raw_content=raw_content,
        game_number=game_count + 1,
    )

    games.append(game)


def count_games(pgn_content: str) -> int:
    """
    Quickly count number of games in PGN without full parsing.

    Counts occurrences of [Event "..."] headers.

    Args:
        pgn_content: PGN content

    Returns:
        Number of games
    """
    # Count [Event headers as proxy for game count
    # This is faster than full parsing
    count = 0
    for line in pgn_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith('[Event "') or stripped.startswith("[Event '"):
            count += 1

    return count
