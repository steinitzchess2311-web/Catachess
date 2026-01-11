"""
Tests for PGN game splitting.
"""

import pytest

from workspace.pgn.parser.split_games import split_games, count_games, PGNGame
from workspace.pgn.parser.errors import EmptyPGNError, InvalidPGNFormatError


# Sample PGN data
SINGLE_GAME_PGN = '''[Event "Test Event"]
[Site "Test Site"]
[Date "2026.01.10"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
'''

MULTI_GAME_PGN = '''[Event "Game 1"]
[White "Alice"]
[Black "Bob"]
[Result "*"]

1. e4 e5 *

[Event "Game 2"]
[White "Charlie"]
[Black "Dave"]
[Result "1/2-1/2"]

1. d4 d5 1/2-1/2

[Event "Game 3"]
[White "Eve"]
[Black "Frank"]
[Result "0-1"]

1. c4 c5 0-1
'''


def test_split_single_game():
    """Test splitting PGN with single game."""
    games = split_games(SINGLE_GAME_PGN)

    assert len(games) == 1
    game = games[0]

    assert game.event == "Test Event"
    assert game.white == "Player1"
    assert game.black == "Player2"
    assert game.result == "1-0"
    assert game.game_number == 1
    assert "1. e4 e5" in game.moves


def test_split_multiple_games():
    """Test splitting PGN with multiple games."""
    games = split_games(MULTI_GAME_PGN)

    assert len(games) == 3

    # Check first game
    assert games[0].event == "Game 1"
    assert games[0].white == "Alice"
    assert games[0].black == "Bob"
    assert games[0].game_number == 1

    # Check second game
    assert games[1].event == "Game 2"
    assert games[1].white == "Charlie"
    assert games[1].black == "Dave"
    assert games[1].game_number == 2

    # Check third game
    assert games[2].event == "Game 3"
    assert games[2].white == "Eve"
    assert games[2].black == "Frank"
    assert games[2].game_number == 3


def test_pgn_game_properties():
    """Test PGNGame property accessors."""
    games = split_games(SINGLE_GAME_PGN)
    game = games[0]

    assert game.event == "Test Event"
    assert game.white == "Player1"
    assert game.black == "Player2"
    assert game.date == "2026.01.10"
    assert game.result == "1-0"


def test_empty_pgn():
    """Test handling of empty PGN."""
    with pytest.raises(EmptyPGNError):
        split_games("")

    with pytest.raises(EmptyPGNError):
        split_games("   \n\n   ")


def test_pgn_without_headers():
    """Test handling of PGN starting with moves (invalid)."""
    invalid_pgn = "1. e4 e5 2. Nf3 Nc6"

    with pytest.raises(InvalidPGNFormatError) as exc_info:
        split_games(invalid_pgn)

    assert "no headers" in str(exc_info.value).lower()


def test_pgn_with_variations():
    """Test parsing game with variations."""
    pgn_with_var = '''[Event "Test"]
[White "A"]
[Black "B"]
[Result "*"]

1. e4 e5 2. Nf3 (2. Bc4 Bc5) 2... Nc6 *
'''

    games = split_games(pgn_with_var)
    assert len(games) == 1
    assert "(2. Bc4" in games[0].moves


def test_pgn_with_comments():
    """Test parsing game with comments."""
    pgn_with_comments = '''[Event "Test"]
[White "A"]
[Black "B"]
[Result "*"]

1. e4 {Good move!} e5 2. Nf3 *
'''

    games = split_games(pgn_with_comments)
    assert len(games) == 1
    assert "{Good move!}" in games[0].moves


def test_count_games():
    """Test fast game counting."""
    count = count_games(MULTI_GAME_PGN)
    assert count == 3

    count_single = count_games(SINGLE_GAME_PGN)
    assert count_single == 1


def test_count_games_empty():
    """Test counting games in empty PGN."""
    count = count_games("")
    assert count == 0


def test_malformed_header():
    """Test handling of malformed header."""
    # Header with extra spaces
    pgn = '''[Event   "Test Game"]
[White "Player"]
[Black "Opponent"]
[Result "*"]

1. e4 e5 *
'''

    games = split_games(pgn)
    assert len(games) == 1
    # Should still parse the event
    assert "Test Game" in games[0].event


def test_missing_optional_headers():
    """Test parsing with minimal headers."""
    minimal_pgn = '''[Event "Minimal"]
[Result "*"]

1. e4 e5 *
'''

    games = split_games(minimal_pgn)
    assert len(games) == 1
    assert games[0].event == "Minimal"
    assert games[0].white == "?"  # Default value
    assert games[0].black == "?"  # Default value


def test_game_with_multiple_blank_lines():
    """Test parsing with extra blank lines between sections."""
    pgn = '''[Event "Test"]


1. e4 e5


*
'''

    games = split_games(pgn)
    assert len(games) == 1


def test_raw_content_preserved():
    """Test that raw content is preserved."""
    games = split_games(SINGLE_GAME_PGN)
    game = games[0]

    assert "[Event \"Test Event\"]" in game.raw_content
    assert "1. e4 e5" in game.raw_content
