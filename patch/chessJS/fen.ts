/**
 * FEN Utilities
 *
 * IMPORTANT: FEN is computed on-demand and NEVER stored in tree.json.
 * These utilities generate FEN from SAN move paths using chess.js replay.
 */

import { Chess } from 'chess.js';
import { replaySanPath, STARTING_FEN } from './replay';

// Re-export STARTING_FEN for convenience
export { STARTING_FEN };

/**
 * Result of computing FEN from a path
 */
export interface FenFromPathResult {
  /** Whether the computation succeeded */
  success: boolean;

  /** The computed FEN (null if failed) */
  fen: string | null;

  /** Error message if failed */
  error: string | null;

  /** Index of the first illegal move (-1 if all legal) */
  illegalMoveIndex: number;
}

/**
 * Computes FEN for a position reached by a sequence of SAN moves
 *
 * @param moves - Array of SAN moves from start position
 * @param startFen - Starting FEN (defaults to standard starting position)
 * @returns FenFromPathResult with the computed FEN or error
 *
 * @example
 * const result = fenFromPath(["e4", "e5", "Nf3"]);
 * if (result.success) {
 *   console.log("FEN:", result.fen);
 * }
 */
export function fenFromPath(moves: string[], startFen?: string): FenFromPathResult {
  const result = replaySanPath(moves, startFen);

  if (result.error) {
    return {
      success: false,
      fen: null,
      error: result.error,
      illegalMoveIndex: result.illegalMoveIndex,
    };
  }

  return {
    success: true,
    fen: result.finalFen,
    error: null,
    illegalMoveIndex: -1,
  };
}

/**
 * Parsed FEN components
 */
export interface FenParts {
  /** Board position (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR") */
  position: string;

  /** Active color: 'w' or 'b' */
  turn: 'w' | 'b';

  /** Castling availability (e.g., "KQkq", "-") */
  castling: string;

  /** En passant target square (e.g., "e3", "-") */
  enPassant: string;

  /** Halfmove clock (moves since last pawn move or capture) */
  halfmoveClock: number;

  /** Fullmove number */
  fullmoveNumber: number;
}

/**
 * FEN validation result
 */
export interface FenValidationResult {
  /** Whether the FEN is valid */
  valid: boolean;

  /** Error message if invalid */
  error: string | null;
}

/**
 * Parses a FEN string into its components
 *
 * @param fen - FEN string to parse
 * @returns Parsed components or null if invalid
 */
export function parseFen(fen: string): FenParts | null {
  const parts = fen.trim().split(/\s+/);
  if (parts.length < 4) {
    return null;
  }

  const position = parts[0];
  const turn = parts[1] as 'w' | 'b';
  const castling = parts[2];
  const enPassant = parts[3];
  const halfmoveClock = parseInt(parts[4] || '0', 10);
  const fullmoveNumber = parseInt(parts[5] || '1', 10);

  // Basic validation
  if (turn !== 'w' && turn !== 'b') {
    return null;
  }

  const ranks = position.split('/');
  if (ranks.length !== 8) {
    return null;
  }

  return {
    position,
    turn,
    castling,
    enPassant,
    halfmoveClock: isNaN(halfmoveClock) ? 0 : halfmoveClock,
    fullmoveNumber: isNaN(fullmoveNumber) ? 1 : fullmoveNumber,
  };
}

/**
 * Validates a FEN string using chess.js
 *
 * @param fen - FEN string to validate
 * @returns Validation result
 */
export function validateFen(fen: string): FenValidationResult {
  try {
    new Chess(fen);
    return { valid: true, error: null };
  } catch (e) {
    return {
      valid: false,
      error: e instanceof Error ? e.message : 'Invalid FEN',
    };
  }
}

/**
 * Composes a FEN string from its components
 *
 * @param parts - FEN components
 * @returns FEN string
 */
export function composeFen(parts: FenParts): string {
  return [
    parts.position,
    parts.turn,
    parts.castling || '-',
    parts.enPassant || '-',
    parts.halfmoveClock,
    parts.fullmoveNumber,
  ].join(' ');
}

/**
 * Checks if a FEN represents the standard starting position
 *
 * @param fen - FEN string to check
 * @returns true if it's the starting position
 */
export function isStartingPosition(fen: string): boolean {
  const parsed = parseFen(fen);
  const startParsed = parseFen(STARTING_FEN);

  if (!parsed || !startParsed) {
    return false;
  }

  // Compare position and turn (ignore move counters)
  return parsed.position === startParsed.position && parsed.turn === startParsed.turn;
}

/**
 * Gets the active color from a FEN string
 *
 * @param fen - FEN string
 * @returns 'w' or 'b', or null if invalid
 */
export function getTurn(fen: string): 'w' | 'b' | null {
  const parts = fen.trim().split(/\s+/);
  if (parts.length < 2) return null;

  const turn = parts[1];
  if (turn === 'w' || turn === 'b') {
    return turn;
  }
  return null;
}

/**
 * Gets the fullmove number from a FEN string
 *
 * @param fen - FEN string
 * @returns Fullmove number or null if invalid
 */
export function getFullmoveNumber(fen: string): number | null {
  const parts = fen.trim().split(/\s+/);
  if (parts.length < 6) return null;

  const num = parseInt(parts[5], 10);
  return isNaN(num) ? null : num;
}

/**
 * Gets the halfmove clock from a FEN string
 *
 * @param fen - FEN string
 * @returns Halfmove clock or null if invalid
 */
export function getHalfmoveClock(fen: string): number | null {
  const parts = fen.trim().split(/\s+/);
  if (parts.length < 5) return null;

  const num = parseInt(parts[4], 10);
  return isNaN(num) ? null : num;
}

// =============================================================================
// Unit Test Placeholders
// =============================================================================

/**
 * TODO: Unit tests for fen.ts
 *
 * Test cases to implement:
 *
 * 1. fenFromPath with valid moves
 *    - ["e4"] should return FEN after 1.e4
 *    - Verify the FEN is correct
 *
 * 2. fenFromPath with empty moves array
 *    - Should return starting FEN
 *
 * 3. fenFromPath with custom startFen
 *    - Should compute from custom position
 *
 * 4. fenFromPath with illegal move
 *    - Should return error and illegalMoveIndex
 *
 * 5. parseFen with valid FEN
 *    - Should return correct components
 *
 * 6. parseFen with invalid FEN
 *    - Should return null
 *
 * 7. validateFen
 *    - Valid FEN: should return valid=true
 *    - Invalid FEN: should return valid=false with error
 *
 * 8. composeFen
 *    - Should round-trip with parseFen
 *
 * 9. isStartingPosition
 *    - STARTING_FEN: should return true
 *    - After 1.e4: should return false
 *
 * 10. getTurn, getFullmoveNumber, getHalfmoveClock
 *     - Should extract correct values
 */
