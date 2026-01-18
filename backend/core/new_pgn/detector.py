"""
PGN detector: splits multi-game PGN into individual games.
"""
import re
from .types import PGNGame, PGNHeader

HEADER_PATTERN = re.compile(r'^\s*\[(\w+)\s+"([^"]*)"\]\s*$')


def _is_comment(s: str) -> bool:
    return s.startswith(';') or s.startswith('%')


def parse_headers(lines: list[str]) -> tuple[PGNHeader, int]:
    """Parse header lines, skipping blanks and comments. Returns (headers, end_idx)."""
    headers: PGNHeader = {}
    idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or _is_comment(stripped):
            continue
        match = HEADER_PATTERN.match(line)
        if match:
            headers[match.group(1)] = match.group(2)
            idx = i + 1
        else:
            break
    return headers, idx


def split_games(pgn_text: str) -> list[PGNGame]:
    """Split multi-game PGN into PGNGame objects. Empty list if no headers."""
    lines = pgn_text.split('\n')
    games: list[PGNGame] = []
    current_lines: list[str] = []
    in_headers = False
    seen_movetext = False
    game_index = 0

    for line in lines:
        stripped = line.strip()
        is_header = bool(HEADER_PATTERN.match(line))
        is_skip = not stripped or _is_comment(stripped)

        # New game: header after movetext
        if is_header and seen_movetext:
            if current_lines:
                game = _build_game(current_lines, game_index)
                if game:
                    games.append(game)
            current_lines = []
            in_headers, seen_movetext = True, False
            game_index += 1

        # First header starts first game
        if is_header and not in_headers and not seen_movetext:
            in_headers = True
            game_index += 1

        # Transition from headers to movetext
        if in_headers and not is_header and not is_skip:
            in_headers, seen_movetext = False, True

        current_lines.append(line)

    # Finalize last game
    if current_lines:
        game = _build_game(current_lines, game_index)
        if game:
            games.append(game)
    return games


def _build_game(lines: list[str], index: int) -> PGNGame | None:
    """Build a PGNGame from accumulated lines."""
    raw = '\n'.join(lines)
    headers, movetext_start = parse_headers(lines)
    if not headers:
        return None
    movetext = '\n'.join(lines[movetext_start:]).strip()
    return PGNGame(headers=headers, movetext=movetext, raw=raw.strip(), index=index)
