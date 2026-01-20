/**
 * Chess.js Replay Utilities
 *
 * IMPORTANT: chess.js is only used for frontend replay/legality validation.
 * FEN is computed on-demand and NEVER stored in tree.json.
 *
 * This module provides functions to:
 * - Replay a sequence of SAN moves
 * - Validate move legality
 * - Generate FEN at any position in the move path
 */

import { Chess } from 'chess.js';

/** Standard starting FEN - used when no custom startFen is provided */
export const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

/**
 * Result of replaying a SAN move path
 */
export interface ReplayResult {
  /** The chess.js board instance after replay (null if failed on first move) */
  board: Chess | null;

  /** Successfully replayed SAN moves */
  historySan: string[];

  /** FEN after each successfully replayed move (index 0 = after first move) */
  historyFen: string[];

  /** Index of the first illegal move (-1 if all moves are legal) */
  illegalMoveIndex: number;

  /** Error message if an illegal move was encountered */
  error: string | null;

  /** Final FEN after replay (startFen if no moves, or FEN after last legal move) */
  finalFen: string;
}

/**
 * Replays a sequence of SAN moves from a starting position
 *
 * @param moves - Array of SAN moves to replay (e.g., ["e4", "e5", "Nf3"])
 * @param startFen - Starting FEN (defaults to standard starting position)
 * @returns ReplayResult with board state and any errors
 *
 * @example
 * const result = replaySanPath(["e4", "e5", "Nf3"]);
 * if (result.illegalMoveIndex === -1) {
 *   console.log("All moves legal, final FEN:", result.finalFen);
 * } else {
 *   console.log("Illegal move at index:", result.illegalMoveIndex);
 * }
 */
export function replaySanPath(moves: string[], startFen?: string): ReplayResult {
  const fen = startFen || STARTING_FEN;

  // Validate starting FEN
  let board: Chess;
  try {
    board = new Chess(fen);
  } catch (e) {
    return {
      board: null,
      historySan: [],
      historyFen: [],
      illegalMoveIndex: -1,
      error: `Invalid starting FEN: ${fen}`,
      finalFen: fen,
    };
  }

  const historySan: string[] = [];
  const historyFen: string[] = [];

  for (let i = 0; i < moves.length; i++) {
    const san = moves[i];

    try {
      const move = board.move(san);
      if (!move) {
        // Move is illegal
        return {
          board,
          historySan,
          historyFen,
          illegalMoveIndex: i,
          error: `Illegal move "${san}" at index ${i}`,
          finalFen: board.fen(),
        };
      }

      historySan.push(move.san);
      historyFen.push(board.fen());
    } catch (e) {
      // chess.js throws on invalid SAN format
      return {
        board,
        historySan,
        historyFen,
        illegalMoveIndex: i,
        error: `Invalid SAN "${san}" at index ${i}: ${e instanceof Error ? e.message : 'unknown error'}`,
        finalFen: board.fen(),
      };
    }
  }

  return {
    board,
    historySan,
    historyFen,
    illegalMoveIndex: -1,
    error: null,
    finalFen: board.fen(),
  };
}

/**
 * Result of validating a single move
 */
export interface ValidateMoveResult {
  /** Whether the move is legal */
  valid: boolean;

  /** The move in SAN notation (normalized by chess.js) */
  san: string | null;

  /** UCI notation of the move */
  uci: string | null;

  /** FEN after the move */
  fenAfter: string | null;

  /** Error message if invalid */
  error: string | null;
}

/**
 * Validates a single SAN move from a position
 *
 * @param fen - Current position FEN
 * @param san - SAN move to validate
 * @returns ValidateMoveResult
 */
export function validateMove(fen: string, san: string): ValidateMoveResult {
  let board: Chess;
  try {
    board = new Chess(fen);
  } catch (e) {
    return {
      valid: false,
      san: null,
      uci: null,
      fenAfter: null,
      error: `Invalid FEN: ${fen}`,
    };
  }

  try {
    const move = board.move(san);
    if (!move) {
      return {
        valid: false,
        san: null,
        uci: null,
        fenAfter: null,
        error: `Illegal move "${san}"`,
      };
    }

    return {
      valid: true,
      san: move.san,
      uci: move.from + move.to + (move.promotion || ''),
      fenAfter: board.fen(),
      error: null,
    };
  } catch (e) {
    return {
      valid: false,
      san: null,
      uci: null,
      fenAfter: null,
      error: `Invalid SAN "${san}": ${e instanceof Error ? e.message : 'unknown error'}`,
    };
  }
}

/**
 * Gets all legal moves from a position
 *
 * @param fen - Position FEN
 * @returns Array of legal moves in SAN notation
 */
export function getValidMoves(fen: string): string[] {
  try {
    const board = new Chess(fen);
    return board.moves();
  } catch (e) {
    return [];
  }
}

/**
 * Result of creating a replay state
 */
export interface CreateReplayStateResult {
  /** The chess.js board instance (null if FEN is invalid) */
  board: Chess | null;

  /** Error message if failed */
  error: string | null;
}

/**
 * Creates a new replay state (chess.js board instance)
 *
 * @param startFen - Starting FEN (defaults to standard starting position)
 * @returns Result with Chess instance or error
 */
export function createReplayState(startFen?: string): CreateReplayStateResult {
  const fen = startFen || STARTING_FEN;
  try {
    return { board: new Chess(fen), error: null };
  } catch (e) {
    return {
      board: null,
      error: `Invalid FEN: ${fen}${e instanceof Error ? ` - ${e.message}` : ''}`,
    };
  }
}

/**
 * Result of replaying a single move
 */
export interface ReplayMoveResult {
  /** Whether the move was successful */
  success: boolean;

  /** The move object from chess.js (null if failed) */
  move: ReturnType<Chess['move']> | null;

  /** FEN after the move (null if failed) */
  fenAfter: string | null;

  /** Error message if failed */
  error: string | null;
}

/**
 * Replays a single move on a board
 *
 * @param board - Chess.js board instance
 * @param san - SAN move to replay
 * @returns ReplayMoveResult with move details or error
 */
export function replayMove(board: Chess, san: string): ReplayMoveResult {
  try {
    const move = board.move(san);
    if (!move) {
      return {
        success: false,
        move: null,
        fenAfter: null,
        error: `Illegal move "${san}"`,
      };
    }
    return {
      success: true,
      move,
      fenAfter: board.fen(),
      error: null,
    };
  } catch (e) {
    return {
      success: false,
      move: null,
      fenAfter: null,
      error: `Invalid SAN "${san}": ${e instanceof Error ? e.message : 'unknown error'}`,
    };
  }
}

/**
 * Result of replaying multiple moves
 */
export interface ReplayMovesResult {
  /** Whether all moves were successful */
  success: boolean;

  /** Results for each move */
  results: ReplayMoveResult[];

  /** Index of the first failed move (-1 if all succeeded) */
  firstFailureIndex: number;

  /** Final FEN after all successful moves */
  finalFen: string;
}

/**
 * Replays multiple moves on a board
 *
 * @param board - Chess.js board instance
 * @param moves - Array of SAN moves
 * @returns ReplayMovesResult with individual results and summary
 */
export function replayMoves(board: Chess, moves: string[]): ReplayMovesResult {
  const results: ReplayMoveResult[] = [];
  let firstFailureIndex = -1;

  for (let i = 0; i < moves.length; i++) {
    const result = replayMove(board, moves[i]);
    results.push(result);

    if (!result.success && firstFailureIndex === -1) {
      firstFailureIndex = i;
      // Don't continue after first failure - subsequent moves would be based on wrong position
      break;
    }
  }

  return {
    success: firstFailureIndex === -1,
    results,
    firstFailureIndex,
    finalFen: board.fen(),
  };
}

/**
 * Converts a move (from, to) to SAN notation
 * Uses 'q' (Queen) as default promotion if not specified
 *
 * @param fen - Current FEN
 * @param from - Source square (e.g., "e2")
 * @param to - Target square (e.g., "e4")
 * @param promotion - Promotion piece (default 'q')
 * @returns SAN string if legal, null otherwise
 */
export function getMoveSan(fen: string, from: string, to: string, promotion: string = 'q'): string | null {
  try {
    const board = new Chess(fen);
    // Try move with promotion (defaults to queen)
    // Note: chess.js move({ from, to }) fails if promotion is needed but missing
    // So we always provide promotion='q' to check legality.
    // If the move is NOT a promotion, the extra field is ignored by chess.js (usually).
    // UPDATE: chess.js v1 (beta) might be strict.
    // Let's try without promotion first, then with.
    
    // Attempt 1: Try exact move (or if it's not a promotion)
    let move = null;
    try {
      move = board.move({ from, to });
    } catch (e) {
      // If it throws or returns null (depending on version), we try with promotion
    }

    if (move) return move.san;

    // Attempt 2: Try with promotion 'q'
    try {
       move = board.move({ from, to, promotion });
    } catch (e) {}
    
    if (move) return move.san;
    
    return null;
  } catch (e) {
    return null;
  }
}

// =============================================================================
// Unit Test Placeholders
// =============================================================================

/**
 * TODO: Unit tests for replay.ts
 *
 * Test cases to implement:
 *
 * 1. replaySanPath with valid moves
 *    - Standard opening: ["e4", "e5", "Nf3", "Nc6"]
 *    - Should return illegalMoveIndex = -1
 *    - historyFen should have correct FEN for each position
 *
 * 2. replaySanPath with illegal move
 *    - ["e4", "e4"] - second e4 is illegal
 *    - Should return illegalMoveIndex = 1
 *    - error should contain "Illegal move"
 *
 * 3. replaySanPath with invalid SAN
 *    - ["e4", "xyz"]
 *    - Should return illegalMoveIndex = 1
 *    - error should contain "Invalid SAN"
 *
 * 4. replaySanPath with custom startFen
 *    - FEN for position after 1.e4
 *    - moves: ["e5"]
 *    - Should succeed
 *
 * 5. replaySanPath with invalid startFen
 *    - Should return error about invalid FEN
 *
 * 6. validateMove with valid move
 *    - Should return valid=true, san normalized, uci, fenAfter
 *
 * 7. validateMove with illegal move
 *    - Should return valid=false with error
 *
 * 8. getValidMoves
 *    - From starting position, should return 20 moves
 */
