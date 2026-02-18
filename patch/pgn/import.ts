/**
 * PGN Import
 *
 * Provides:
 *   importPgn(pgn)           – single-game import (returns PgnParseResult)
 *   importMultiPgn(content)  – multi-game import (splits then parses each)
 *
 * Uses the custom recursive parser (parser.ts) which preserves variations,
 * comments, shapes, and clock annotations.
 */

import { parsePgn } from './parser';
import { splitMultiPgn } from './splitter';
import type { StudyTree as StudyTreeData } from '../tree/type';

// ---------------------------------------------------------------------------
// Single-game import
// ---------------------------------------------------------------------------

export interface PgnParseOptions {
  strict?: boolean;
}

export interface PgnParseResult {
  success: boolean;
  tree: StudyTreeData | null;
  /** PGN headers (White, Black, Event, …) */
  headers: Record<string, string>;
  /** From [FEN "…"] header if present */
  startingFen: string | undefined;
  errors: string[];
}

const MAX_PGN_CHARS = 500_000; // 500 KB – matches Lichess limit

/**
 * Import a single-game PGN string into a StudyTree.
 * Returns the parsed tree, headers, and any non-fatal errors.
 */
export function importPgn(pgnContent: string, _options?: PgnParseOptions): PgnParseResult {
  if (pgnContent.length > MAX_PGN_CHARS) {
    return {
      success: false,
      tree: null,
      headers: {},
      startingFen: undefined,
      errors: [`PGN exceeds ${MAX_PGN_CHARS} characters`],
    };
  }

  try {
    const { headers, tree, startingFen, errors } = parsePgn(pgnContent);
    return {
      success: true,
      tree,
      headers,
      startingFen,
      errors,
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Unknown PGN parse error';
    return {
      success: false,
      tree: null,
      headers: {},
      startingFen: undefined,
      errors: [msg],
    };
  }
}

// ---------------------------------------------------------------------------
// Multi-game import
// ---------------------------------------------------------------------------

export interface MultiPgnGame {
  headers: Record<string, string>;
  tree: StudyTreeData;
  startingFen: string | undefined;
  errors: string[];
}

export interface MultiPgnImportResult {
  games: MultiPgnGame[];
  /** Total number of games found before applying `max` */
  totalCount: number;
  /** True when the source had more games than `max` */
  truncated: boolean;
}

/**
 * Import a string that may contain multiple PGN games.
 *
 * @param content  Raw PGN text
 * @param max      Maximum number of games to parse (default 64)
 */
export function importMultiPgn(content: string, max = 64): MultiPgnImportResult {
  if (content.length > MAX_PGN_CHARS) {
    return {
      games: [],
      totalCount: 0,
      truncated: false,
    };
  }

  const allPgns = splitMultiPgn(content, 10_000);
  const totalCount = allPgns.length;
  const truncated = totalCount > max;
  const pgnsToProcess = allPgns.slice(0, max);

  const games: MultiPgnGame[] = pgnsToProcess.map((pgn) => {
    const { headers, tree, startingFen, errors } = parsePgn(pgn);
    return { headers, tree, startingFen, errors };
  });

  return { games, totalCount, truncated };
}

// ---------------------------------------------------------------------------
// Legacy compatibility exports (kept for callers that imported these)
// ---------------------------------------------------------------------------

export function detectGames(_pgnContent: string): unknown[] {
  return [];
}

export function parseMultiplePgn(_pgnContent: string): unknown[] {
  return [];
}
