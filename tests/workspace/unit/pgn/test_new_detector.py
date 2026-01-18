"""
Tests for new PGN detector.
"""

from core.new_pgn import detect_games


SINGLE_GAME_PGN = """[Event "Test Event"]
[Site "Test Site"]
[Date "2026.01.10"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
"""

MULTI_GAME_PGN = """[Event "Game 1"]
[White "Alice"]
[Black "Bob"]
[Result "*"]

1. e4 e5 *

[Event "Game 2"]
[White "Charlie"]
[Black "Dave"]
[Result "1/2-1/2"]

1. d4 d5 1/2-1/2
"""

NO_HEADER_PGN = """1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0"""

CUSTOM_FEN_PGN = """[Event "FEN Test"]
[SetUp "1"]
[FEN "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
[White "Alpha"]
[Black "Beta"]
[Result "*"]

1. e4 *
"""


def test_detect_single_game():
    games = detect_games(SINGLE_GAME_PGN)
    assert len(games) == 1
    game = games[0]
    assert game.headers["Event"] == "Test Event"
    assert game.headers["White"] == "Player1"
    assert "1. e4 e5" in game.movetext


def test_detect_multiple_games():
    games = detect_games(MULTI_GAME_PGN)
    assert len(games) == 2
    assert games[0].headers["Event"] == "Game 1"
    assert games[1].headers["Event"] == "Game 2"


def test_detect_missing_headers_returns_empty():
    games = detect_games(NO_HEADER_PGN)
    assert games == []


def test_detect_preserves_custom_fen_headers():
    games = detect_games(CUSTOM_FEN_PGN)
    assert len(games) == 1
    game = games[0]
    assert game.headers["FEN"].startswith("rnbqkbnr/pppppppp")
