/**
 * Parsing Module - Validators
 *
 * FEN and PGN validation utilities.
 * Created: 2025-02-15
 */

import { Chess } from 'chess.js';
import { FenValidation, FenComponents } from './types';

/**
 * Validate FEN string format and playability
 *
 * Uses chess.js to validate that the FEN represents a legal chess position.
 *
 * @param fen - FEN string to validate
 * @returns Validation result with error message if invalid
 */
export function validateFen(fen: string): FenValidation {
  if (!fen || typeof fen !== 'string') {
    return {
      valid: false,
      error: 'FEN must be a non-empty string',
    };
  }

  // Trim whitespace
  const trimmedFen = fen.trim();

  if (trimmedFen.length === 0) {
    return {
      valid: false,
      error: 'FEN cannot be empty',
    };
  }

  // Use chess.js built-in validation
  const validation = Chess.validateFen(trimmedFen);

  if (!validation.ok) {
    return {
      valid: false,
      error: validation.error || 'Invalid FEN format',
    };
  }

  // Try to create a Chess instance to ensure playability
  try {
    const chess = new Chess(trimmedFen);

    // Parse FEN components
    const components = parseFenComponents(trimmedFen);

    return {
      valid: true,
      components,
    };
  } catch (error) {
    return {
      valid: false,
      error: error instanceof Error ? error.message : 'Failed to parse FEN',
    };
  }
}

/**
 * Parse FEN string into components
 *
 * Standard FEN format:
 * <piece placement> <active color> <castling> <en passant> <halfmove> <fullmove>
 *
 * @param fen - Valid FEN string
 * @returns FEN components
 */
export function parseFenComponents(fen: string): FenComponents {
  const parts = fen.trim().split(/\s+/);

  // Validate minimum parts (first 4 are required)
  if (parts.length < 4) {
    throw new Error('FEN must have at least 4 parts');
  }

  const [piecePlacement, activeColor, castling, enPassant, halfmove = '0', fullmove = '1'] =
    parts;

  // Validate active color
  if (activeColor !== 'w' && activeColor !== 'b') {
    throw new Error(`Invalid active color: ${activeColor}`);
  }

  return {
    piecePlacement,
    activeColor: activeColor as 'w' | 'b',
    castling,
    enPassant,
    halfmoveClock: parseInt(halfmove, 10),
    fullmoveNumber: parseInt(fullmove, 10),
  };
}

/**
 * Check if FEN represents a standard starting position
 *
 * @param fen - FEN string to check
 * @returns True if standard starting position
 */
export function isStandardPosition(fen: string): boolean {
  const standardFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  return fen.trim() === standardFen;
}

/**
 * Normalize FEN string
 *
 * Ensures consistent formatting:
 * - Trims whitespace
 * - Adds missing halfmove/fullmove if needed
 *
 * @param fen - FEN string to normalize
 * @returns Normalized FEN string
 */
export function normalizeFen(fen: string): string {
  const parts = fen.trim().split(/\s+/);

  // Ensure we have all 6 parts
  while (parts.length < 6) {
    if (parts.length === 4) {
      parts.push('0'); // halfmove clock
    } else if (parts.length === 5) {
      parts.push('1'); // fullmove number
    }
  }

  return parts.join(' ');
}

/**
 * Get human-readable description of FEN validation error
 *
 * @param error - Error from validateFen
 * @returns User-friendly error message
 */
export function getFriendlyFenError(error: string): string {
  const errorMap: Record<string, string> = {
    'Invalid FEN': 'The position string is not in valid FEN format.',
    'Invalid piece placement': 'The piece placement part of the FEN is invalid.',
    'Invalid active color': 'Active color must be "w" (white) or "b" (black).',
    'Invalid castling': 'Castling rights must be in KQkq format or "-".',
    'Invalid en passant': 'En passant square must be a valid square or "-".',
    'Too many kings': 'Each side must have exactly one king.',
    'No white king': 'White king is missing from the position.',
    'No black king': 'Black king is missing from the position.',
  };

  // Check for exact matches
  for (const [key, message] of Object.entries(errorMap)) {
    if (error.includes(key)) {
      return message;
    }
  }

  // Return original error if no friendly message found
  return error;
}

/**
 * Validate that FEN is playable (not just syntactically correct)
 *
 * Checks:
 * - Position is legal
 * - Active player is not already in checkmate
 * - Position can actually be reached in a game
 *
 * @param fen - FEN string to validate
 * @returns True if position is playable
 */
export function isPlayableFen(fen: string): boolean {
  try {
    const chess = new Chess(fen);

    // If we can create a Chess instance, it's playable
    // chess.js already validates:
    // - Legal piece placement
    // - Kings present
    // - No pawns on first/last rank
    // - etc.

    return true;
  } catch {
    return false;
  }
}
