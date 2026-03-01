/**
 * Web Worker: Large PGN File Parser
 *
 * Runs off the main thread so UI never freezes, even for multi-MB PGN files.
 *
 * Protocol
 * --------
 * IN  { type: 'parse'; content: string; batchSizeBytes: number }
 *
 * OUT { type: 'progress'; parsed: number; total: number }
 *     { type: 'done';     batches: ParsedBatch[]; totalGames: number; skipped: number }
 *     { type: 'error';    message: string }
 */

import { splitMultiPgn } from './splitter';
import { parsePgn } from './parser';

export interface ParsedGame {
  headers: Record<string, string>;
  tree: any; // StudyTreeData — any to avoid import chain bloat in worker bundle
  startingFen: string | undefined;
  errors: string[];
  rawLength: number;
}

export interface ParsedBatch {
  index: number; // 0-based
  games: ParsedGame[];
  /** Approximate byte size of all raw game strings in this batch */
  totalBytes: number;
}

// ---------------------------------------------------------------------------
// Worker message handler
// ---------------------------------------------------------------------------

self.onmessage = (event: MessageEvent) => {
  const { type, content, batchSizeBytes } = event.data as {
    type: string;
    content: string;
    batchSizeBytes: number;
  };

  if (type !== 'parse') return;

  try {
    // ── Step 1: Split raw PGN text into individual game strings ─────────────
    const rawGames = splitMultiPgn(content, 100_000);
    const total = rawGames.length;

    if (total === 0) {
      post({ type: 'done', batches: [], totalGames: 0, skipped: 0 });
      return;
    }

    // ── Step 2: Parse each game, report progress every 5 games ──────────────
    const parsedGames: (ParsedGame | null)[] = [];

    for (let i = 0; i < rawGames.length; i++) {
      const raw = rawGames[i];
      try {
        const { headers, tree, startingFen, errors } = parsePgn(raw);
        parsedGames.push({ headers, tree, startingFen, errors, rawLength: raw.length });
      } catch {
        // Malformed game — record null so we can count skipped
        parsedGames.push(null);
      }

      if ((i + 1) % 5 === 0 || i === rawGames.length - 1) {
        post({ type: 'progress', parsed: i + 1, total });
      }
    }

    // ── Step 3: Group valid games into size-bounded batches ─────────────────
    //
    // Each batch targets ≤ batchSizeBytes of raw PGN.  We never split a game
    // across batches — a game either belongs entirely to one batch or the next.
    const batches: ParsedBatch[] = [];
    let currentGames: ParsedGame[] = [];
    let currentBytes = 0;

    for (const game of parsedGames) {
      if (game === null) continue; // skip unparseable

      if (currentBytes + game.rawLength > batchSizeBytes && currentGames.length > 0) {
        batches.push({ index: batches.length, games: currentGames, totalBytes: currentBytes });
        currentGames = [];
        currentBytes = 0;
      }
      currentGames.push(game);
      currentBytes += game.rawLength;
    }

    if (currentGames.length > 0) {
      batches.push({ index: batches.length, games: currentGames, totalBytes: currentBytes });
    }

    const validCount  = parsedGames.filter(Boolean).length;
    const skipped     = parsedGames.length - validCount;

    post({ type: 'done', batches, totalGames: validCount, skipped });

  } catch (e) {
    post({ type: 'error', message: e instanceof Error ? e.message : 'Unknown worker error' });
  }
};

// Typed wrapper to silence TS on DedicatedWorkerGlobalScope
function post(msg: Record<string, unknown>) {
  (self as unknown as { postMessage(msg: unknown): void }).postMessage(msg);
}
