/**
 * Parsing Module - Shared Types
 *
 * Common type definitions for FEN and PGN parsing.
 * Created: 2025-02-15
 */

import { StudyTree } from '../tree/type';

/**
 * Standard starting position FEN
 */
export const STANDARD_STARTING_FEN =
  'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

/**
 * Result of a parsing operation (FEN or PGN)
 */
export interface ParseResult {
  /** Whether parsing was successful */
  success: boolean;

  /** Parsed study tree (null if parsing failed) */
  tree: StudyTree | null;

  /** PGN headers extracted from input (if applicable) */
  headers: Record<string, string>;

  /** Custom starting FEN position (undefined = standard position) */
  startingFen?: string;

  /** Parse errors (empty if success = true) */
  errors: string[];
}

/**
 * FEN validation result
 */
export interface FenValidation {
  /** Whether FEN is valid */
  valid: boolean;

  /** Error message if invalid */
  error?: string;

  /** FEN components (if valid) */
  components?: FenComponents;
}

/**
 * FEN string components
 *
 * Standard FEN has 6 parts separated by spaces:
 * 1. Piece placement
 * 2. Active color (w/b)
 * 3. Castling rights (KQkq)
 * 4. En passant target
 * 5. Halfmove clock
 * 6. Fullmove number
 */
export interface FenComponents {
  /** Piece placement (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR") */
  piecePlacement: string;

  /** Active color: "w" or "b" */
  activeColor: 'w' | 'b';

  /** Castling availability (e.g., "KQkq", "-") */
  castling: string;

  /** En passant target square (e.g., "e3", "-") */
  enPassant: string;

  /** Halfmove clock (50-move rule) */
  halfmoveClock: number;

  /** Fullmove number */
  fullmoveNumber: number;
}

/**
 * Parse options
 */
export interface ParseOptions {
  /** Strict mode - reject non-standard positions */
  strict?: boolean;

  /** Maximum nodes allowed in tree */
  maxNodes?: number;
}

/**
 * PGN metadata (for future PGN import)
 */
export interface PgnMetadata {
  /** Event name */
  event?: string;

  /** Site/location */
  site?: string;

  /** Date (YYYY.MM.DD) */
  date?: string;

  /** Round */
  round?: string;

  /** White player */
  white?: string;

  /** Black player */
  black?: string;

  /** Result (1-0, 0-1, 1/2-1/2, *) */
  result?: string;

  /** Other custom headers */
  [key: string]: string | undefined;
}

/**
 * Type guard: check if FEN is standard starting position
 */
export function isStandardStartingFen(fen: string): boolean {
  return fen === STANDARD_STARTING_FEN;
}

/**
 * Type guard: check if parse result is successful
 */
export function isParseSuccess(result: ParseResult): result is ParseResult & {
  success: true;
  tree: StudyTree;
} {
  return result.success && result.tree !== null;
}
