/**
 * FEN Import Module
 *
 * Import chess positions from FEN (Forsyth-Edwards Notation) strings.
 *
 * Features:
 * - ✅ Validate FEN format and playability
 * - ✅ Create empty StudyTree with custom starting position
 * - ✅ Return starting_fen for Chapter metadata
 * - ✅ Support any valid chess position (endgames, puzzles, etc.)
 *
 * Created: 2025-02-15
 * See: /fen_import.md for implementation plan
 */

import { Chess } from 'chess.js';
import { StudyTree, createEmptyTree } from '../tree/StudyTree';
import { TREE_SCHEMA_VERSION } from '../tree/type';
import {
  ParseResult,
  STANDARD_STARTING_FEN,
  isStandardStartingFen,
} from './types';
import {
  validateFen,
  normalizeFen,
  getFriendlyFenError,
} from './validators';

/**
 * Import a chess position from FEN string
 *
 * Creates an empty StudyTree (only root node) with a custom starting position.
 * The actual position analysis/moves will be added by the user after import.
 *
 * **Usage Example**:
 * ```typescript
 * // Import endgame position
 * const result = importFromFen('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');
 *
 * if (result.success) {
 *   // Save to chapter with starting_fen
 *   await createChapter({
 *     title: 'Rook Endgame',
 *     starting_fen: result.startingFen, // Save to metadata
 *     tree: result.tree                  // Empty tree (root only)
 *   });
 * }
 * ```
 *
 * **Architecture**:
 * - starting_fen is stored in Chapter metadata (Postgres)
 * - tree.json contains only SAN moves (no FEN)
 * - FEN is computed via replay from starting_fen
 *
 * @param fenString - FEN string representing the chess position
 * @returns ParseResult with empty tree and starting_fen
 */
export function importFromFen(fenString: string): ParseResult {
  // Step 1: Validate FEN format
  const validation = validateFen(fenString);

  if (!validation.valid) {
    const friendlyError = getFriendlyFenError(validation.error || 'Invalid FEN');

    return {
      success: false,
      tree: null,
      headers: {},
      errors: [friendlyError],
    };
  }

  // Step 2: Normalize FEN (add missing parts if needed)
  const normalizedFen = normalizeFen(fenString);

  // Step 3: Verify position is playable with chess.js
  try {
    // Create chess instance to ensure FEN is actually playable
    const chess = new Chess(normalizedFen);

    // Step 4: Create empty tree (only root node, no moves)
    const tree = createEmptyTree();

    // Set tree version
    tree.version = TREE_SCHEMA_VERSION;

    // No result yet (position to be analyzed)
    tree.meta.result = null;

    // Step 5: Extract headers from FEN components
    const headers: Record<string, string> = {
      FEN: normalizedFen,
    };

    // Add active color to headers
    if (validation.components) {
      const { activeColor, fullmoveNumber } = validation.components;
      headers.Turn = activeColor === 'w' ? 'White' : 'Black';
      headers.MoveNumber = String(fullmoveNumber);
    }

    // Step 6: Determine if we should save starting_fen
    // If it's the standard position, return undefined to save space
    const shouldSaveStartingFen = !isStandardStartingFen(normalizedFen);

    return {
      success: true,
      tree,
      headers,
      startingFen: shouldSaveStartingFen ? normalizedFen : undefined,
      errors: [],
    };
  } catch (error) {
    return {
      success: false,
      tree: null,
      headers: {},
      errors: [
        error instanceof Error
          ? error.message
          : 'Failed to create chess position from FEN',
      ],
    };
  }
}

/**
 * Quick validation of FEN without creating a tree
 *
 * Useful for UI validation before submitting.
 *
 * @param fenString - FEN string to validate
 * @returns Object with valid flag and optional error message
 */
export function quickValidateFen(fenString: string): {
  valid: boolean;
  error?: string;
} {
  const validation = validateFen(fenString);

  if (!validation.valid) {
    return {
      valid: false,
      error: getFriendlyFenError(validation.error || 'Invalid FEN'),
    };
  }

  return { valid: true };
}

/**
 * Get position description from FEN
 *
 * Returns human-readable information about the position.
 *
 * @param fenString - FEN string
 * @returns Position description
 */
export function getPositionInfo(fenString: string): {
  turn: 'White' | 'Black';
  moveNumber: number;
  isStandard: boolean;
  inCheck: boolean;
  gameOver: boolean;
} | null {
  try {
    const chess = new Chess(fenString);

    return {
      turn: chess.turn() === 'w' ? 'White' : 'Black',
      moveNumber: chess.moveNumber(),
      isStandard: isStandardStartingFen(fenString),
      inCheck: chess.inCheck(),
      gameOver: chess.isGameOver(),
    };
  } catch {
    return null;
  }
}

/**
 * Common FEN templates for quick import
 *
 * Useful for UI quick-select menus.
 */
export const FEN_TEMPLATES = {
  standard: {
    name: 'Standard Starting Position',
    fen: STANDARD_STARTING_FEN,
  },
  endgameKQvK: {
    name: 'King + Queen vs King',
    fen: '4k3/8/8/8/8/8/4Q3/4K3 w - - 0 1',
  },
  endgameKRvK: {
    name: 'King + Rook vs King',
    fen: '4k3/8/8/8/8/8/4R3/4K3 w - - 0 1',
  },
  endgameKRRvK: {
    name: 'King + 2 Rooks vs King',
    fen: 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
  },
  middlegame: {
    name: 'Typical Middlegame',
    fen: 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1',
  },
  puzzleBackRank: {
    name: 'Back Rank Mate Puzzle',
    fen: '6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1',
  },
} as const;

/**
 * Export for use in other modules
 */
export { STANDARD_STARTING_FEN, isStandardStartingFen };
