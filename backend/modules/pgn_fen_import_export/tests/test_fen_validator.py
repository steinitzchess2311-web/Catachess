"""
Tests for FEN Validator

Tests FEN string validation according to the standard format.
"""

import pytest

from ..services.fen_validator import (
    validate_fen,
    is_standard_fen,
    STANDARD_FEN,
    FenValidationResult,
)


class TestValidateFen:
    """Tests for validate_fen function."""

    def test_standard_starting_position(self):
        """Test validation of standard starting position."""
        result = validate_fen(STANDARD_FEN)

        assert result.valid is True
        assert result.error is None
        assert result.normalized_fen == STANDARD_FEN

    def test_custom_endgame_position(self):
        """Test validation of custom endgame position."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        result = validate_fen(fen)

        assert result.valid is True
        assert result.error is None
        assert result.normalized_fen == fen

    def test_fen_with_4_parts_auto_pads(self):
        """Test that FEN with only 4 parts gets auto-padded."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"
        result = validate_fen(fen)

        assert result.valid is True
        assert result.normalized_fen == f"{fen} 0 1"

    def test_fen_with_5_parts_auto_pads(self):
        """Test that FEN with only 5 parts gets auto-padded."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0"
        result = validate_fen(fen)

        assert result.valid is True
        assert result.normalized_fen == f"{fen} 1"

    def test_black_to_move(self):
        """Test FEN with black to move."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        result = validate_fen(fen)

        assert result.valid is True

    def test_en_passant_target(self):
        """Test FEN with en passant target."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        result = validate_fen(fen)

        assert result.valid is True
        assert "e3" in result.normalized_fen

    def test_no_castling_available(self):
        """Test FEN with no castling available."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1"
        result = validate_fen(fen)

        assert result.valid is True

    def test_partial_castling(self):
        """Test FEN with partial castling rights."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w Kq - 0 1"
        result = validate_fen(fen)

        assert result.valid is True

    def test_normalizes_whitespace(self):
        """Test that extra whitespace is normalized."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR   w   KQkq  -  0  1"
        result = validate_fen(fen)

        assert result.valid is True
        assert result.normalized_fen == STANDARD_FEN

    # === Invalid FEN tests ===

    def test_empty_string(self):
        """Test that empty string is invalid."""
        result = validate_fen("")

        assert result.valid is False
        assert "non-empty string" in result.error

    def test_none_value(self):
        """Test that None is invalid."""
        result = validate_fen(None)  # type: ignore

        assert result.valid is False
        assert "non-empty string" in result.error

    def test_too_few_parts(self):
        """Test that FEN with less than 4 parts is invalid."""
        result = validate_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w")

        assert result.valid is False
        assert "at least 4 parts" in result.error

    def test_invalid_active_color(self):
        """Test that invalid active color is rejected."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1"
        result = validate_fen(fen)

        assert result.valid is False
        assert "active color" in result.error.lower()

    def test_invalid_piece_placement_too_few_ranks(self):
        """Test that piece placement with wrong rank count is invalid."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP w KQkq - 0 1"  # Only 7 ranks
        result = validate_fen(fen)

        assert result.valid is False
        assert "8 ranks" in result.error

    def test_invalid_piece_placement_wrong_square_count(self):
        """Test that rank with wrong square count is invalid."""
        fen = "rnbqkbnr/ppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # 2nd rank has 7 squares
        result = validate_fen(fen)

        assert result.valid is False
        assert "8 squares" in result.error

    def test_invalid_piece_character(self):
        """Test that invalid piece character is rejected."""
        fen = "rnbqkbnr/ppppXppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = validate_fen(fen)

        assert result.valid is False
        assert "Invalid character" in result.error

    def test_invalid_castling(self):
        """Test that invalid castling string is rejected."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkqX - 0 1"
        result = validate_fen(fen)

        assert result.valid is False
        assert "castling" in result.error.lower()

    def test_duplicate_castling_rights(self):
        """Test that duplicate castling rights are rejected."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KKq - 0 1"
        result = validate_fen(fen)

        assert result.valid is False

    def test_invalid_en_passant_target(self):
        """Test that invalid en passant target is rejected."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e5 0 1"  # Must be rank 3 or 6
        result = validate_fen(fen)

        assert result.valid is False
        assert "en passant" in result.error.lower()

    def test_invalid_halfmove_clock(self):
        """Test that invalid halfmove clock is rejected."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - -1 1"
        result = validate_fen(fen)

        assert result.valid is False
        assert "Halfmove" in result.error

    def test_invalid_fullmove_number(self):
        """Test that invalid fullmove number is rejected."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"
        result = validate_fen(fen)

        assert result.valid is False
        assert "Fullmove" in result.error


class TestIsStandardFen:
    """Tests for is_standard_fen function."""

    def test_standard_fen_exact_match(self):
        """Test that standard FEN is recognized."""
        assert is_standard_fen(STANDARD_FEN) is True

    def test_standard_fen_with_extra_whitespace(self):
        """Test that standard FEN with extra whitespace is recognized."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR   w   KQkq  -  0  1"
        assert is_standard_fen(fen) is True

    def test_custom_position_is_not_standard(self):
        """Test that custom position is not recognized as standard."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        assert is_standard_fen(fen) is False

    def test_standard_position_black_to_move_is_not_standard(self):
        """Test that standard position with black to move is not standard FEN."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        assert is_standard_fen(fen) is False
