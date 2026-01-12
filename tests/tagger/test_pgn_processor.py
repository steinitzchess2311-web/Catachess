"""
Tests for PGN processor.
"""

import tempfile
from pathlib import Path

import pytest

from backend.core.tagger.analysis.pgn_processor import PGNProcessor, Position


class TestPGNProcessor:
    """Test PGN processing functionality."""

    @pytest.fixture
    def sample_pgn(self):
        """Create a temporary PGN file for testing."""
        pgn_content = """[Event "Test"]
[Site "Test"]
[Date "2024.01.01"]
[White "White Player"]
[Black "Black Player"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0

[Event "Test 2"]
[Site "Test"]
[Date "2024.01.02"]
[White "White Player 2"]
[Black "Black Player 2"]
[Result "1/2-1/2"]

1. d4 d5 2. c4 1/2-1/2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pgn', delete=False) as f:
            f.write(pgn_content)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink()

    def test_extract_positions(self, sample_pgn):
        """Test position extraction from PGN."""
        processor = PGNProcessor(sample_pgn)
        positions = list(processor.extract_positions())

        # First game: e4 e5 Nf3 Nc6 Bb5 = 5 plies
        # Second game: d4 d5 c4 = 3 plies
        # Total = 8 positions
        assert len(positions) == 8

        # Check first position
        first_pos = positions[0]
        assert isinstance(first_pos, Position)
        assert first_pos.game_index == 0
        assert first_pos.move_number == 1
        assert first_pos.played_move_uci == "e2e4"

    def test_skip_opening_moves(self, sample_pgn):
        """Test skipping opening moves."""
        processor = PGNProcessor(sample_pgn)
        positions = list(processor.extract_positions(skip_opening_moves=2))

        # Should skip first 2 plies of each game
        # Game 1: 5 plies total, skip 2 = 3 remaining
        # Game 2: 3 plies total, skip 2 = 1 remaining
        # Total = 4 positions
        assert len(positions) == 4

    def test_count_games(self, sample_pgn):
        """Test game counting."""
        processor = PGNProcessor(sample_pgn)
        assert processor.count_games() == 2

    def test_position_metadata(self, sample_pgn):
        """Test that position metadata is correctly extracted."""
        processor = PGNProcessor(sample_pgn)
        positions = list(processor.extract_positions())

        first_pos = positions[0]
        assert "Event" in first_pos.game_headers
        assert first_pos.game_headers["Event"] == "Test"
        assert first_pos.game_headers["White"] == "White Player"
