"""
FEN (Forsyth-Edwards Notation) Validator

Validates FEN strings according to the standard format:
[piece placement] [active color] [castling] [en passant] [halfmove] [fullmove]

Reference: https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation
"""

from dataclasses import dataclass
from typing import Optional


# Standard starting position FEN
STANDARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@dataclass
class FenValidationResult:
    """Result of FEN validation."""

    valid: bool
    error: Optional[str] = None
    normalized_fen: Optional[str] = None


def validate_fen(fen: str) -> FenValidationResult:
    """
    Validate FEN string format.

    Args:
        fen: FEN string to validate

    Returns:
        FenValidationResult with validation status and optional error message

    Examples:
        >>> result = validate_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> result.valid
        True

        >>> result = validate_fen("invalid")
        >>> result.valid
        False
        >>> result.error
        'Invalid FEN: must have at least 4 parts'
    """
    if not fen or not isinstance(fen, str):
        return FenValidationResult(
            valid=False,
            error="FEN must be a non-empty string"
        )

    # Normalize whitespace
    fen = " ".join(fen.split())

    # FEN has 6 parts, but minimum 4 are required
    parts = fen.split()
    if len(parts) < 4:
        return FenValidationResult(
            valid=False,
            error=f"Invalid FEN: must have at least 4 parts, got {len(parts)}"
        )

    # Validate piece placement (part 1)
    piece_placement = parts[0]
    validation_result = _validate_piece_placement(piece_placement)
    if not validation_result.valid:
        return validation_result

    # Validate active color (part 2)
    active_color = parts[1]
    if active_color not in ("w", "b"):
        return FenValidationResult(
            valid=False,
            error=f"Invalid active color: must be 'w' or 'b', got '{active_color}'"
        )

    # Validate castling availability (part 3)
    castling = parts[2]
    if not _validate_castling(castling):
        return FenValidationResult(
            valid=False,
            error=f"Invalid castling availability: '{castling}'"
        )

    # Validate en passant target (part 4)
    en_passant = parts[3]
    if not _validate_en_passant(en_passant):
        return FenValidationResult(
            valid=False,
            error=f"Invalid en passant target: '{en_passant}'"
        )

    # Parts 5 and 6 (halfmove clock and fullmove number) are optional
    if len(parts) >= 5:
        try:
            halfmove = int(parts[4])
            if halfmove < 0:
                return FenValidationResult(
                    valid=False,
                    error=f"Halfmove clock must be >= 0, got {halfmove}"
                )
        except ValueError:
            return FenValidationResult(
                valid=False,
                error=f"Invalid halfmove clock: must be a number, got '{parts[4]}'"
            )

    if len(parts) >= 6:
        try:
            fullmove = int(parts[5])
            if fullmove < 1:
                return FenValidationResult(
                    valid=False,
                    error=f"Fullmove number must be >= 1, got {fullmove}"
                )
        except ValueError:
            return FenValidationResult(
                valid=False,
                error=f"Invalid fullmove number: must be a number, got '{parts[5]}'"
            )

    # If we have less than 6 parts, pad with defaults
    if len(parts) == 4:
        fen = f"{fen} 0 1"
    elif len(parts) == 5:
        fen = f"{fen} 1"

    return FenValidationResult(
        valid=True,
        normalized_fen=fen
    )


def _validate_piece_placement(placement: str) -> FenValidationResult:
    """
    Validate the piece placement part of FEN.

    Format: 8 ranks separated by '/', each rank has pieces/empty squares
    Valid pieces: pnbrqkPNBRQK
    Valid numbers: 1-8 (consecutive empty squares)
    """
    ranks = placement.split("/")

    if len(ranks) != 8:
        return FenValidationResult(
            valid=False,
            error=f"Piece placement must have 8 ranks, got {len(ranks)}"
        )

    valid_pieces = set("pnbrqkPNBRQK")

    for i, rank in enumerate(ranks, 1):
        if not rank:
            return FenValidationResult(
                valid=False,
                error=f"Rank {i} is empty"
            )

        # Check each character in the rank
        square_count = 0
        for char in rank:
            if char in valid_pieces:
                square_count += 1
            elif char.isdigit():
                digit = int(char)
                if digit < 1 or digit > 8:
                    return FenValidationResult(
                        valid=False,
                        error=f"Invalid digit in rank {i}: {char} (must be 1-8)"
                    )
                square_count += digit
            else:
                return FenValidationResult(
                    valid=False,
                    error=f"Invalid character in rank {i}: '{char}'"
                )

        # Each rank must have exactly 8 squares
        if square_count != 8:
            return FenValidationResult(
                valid=False,
                error=f"Rank {i} must have 8 squares, got {square_count}"
            )

    return FenValidationResult(valid=True)


def _validate_castling(castling: str) -> bool:
    """
    Validate castling availability.

    Valid values: '-' (none), or any combination of K, Q, k, q
    """
    if castling == "-":
        return True

    # Check for invalid characters
    valid_chars = set("KQkq")
    if not all(c in valid_chars for c in castling):
        return False

    # Check for duplicates
    if len(castling) != len(set(castling)):
        return False

    return True


def _validate_en_passant(en_passant: str) -> bool:
    """
    Validate en passant target square.

    Valid values: '-' (none), or a square like 'e3', 'e6'
    """
    if en_passant == "-":
        return True

    # Must be 2 characters: file (a-h) + rank (1-8)
    if len(en_passant) != 2:
        return False

    file, rank = en_passant[0], en_passant[1]

    if file not in "abcdefgh":
        return False

    if rank not in "12345678":
        return False

    # En passant target must be on rank 3 or 6
    if rank not in "36":
        return False

    return True


def is_standard_fen(fen: str) -> bool:
    """
    Check if FEN is the standard starting position.

    Args:
        fen: FEN string to check

    Returns:
        True if FEN is the standard starting position
    """
    # Normalize and compare
    normalized = " ".join(fen.split())
    return normalized == STANDARD_FEN
