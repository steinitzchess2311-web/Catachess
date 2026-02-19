import { Chess } from 'chess.js';

export interface UciToSanResult {
  san: string | null;
  fenAfter: string | null;
  error?: string;
}

function parseUci(uci: string): { from: string; to: string; promotion?: string } | null {
  const trimmed = uci.trim().toLowerCase();
  if (trimmed.length !== 4 && trimmed.length !== 5) return null;
  const from = trimmed.slice(0, 2);
  const to = trimmed.slice(2, 4);
  const promotion = trimmed.length === 5 ? trimmed[4] : undefined;
  if (!/^[a-h][1-8]$/.test(from) || !/^[a-h][1-8]$/.test(to)) return null;
  if (promotion && !/^[qrbn]$/.test(promotion)) return null;
  return { from, to, promotion };
}

export function uciToSan(uci: string, fen: string): UciToSanResult {
  try {
    const parsed = parseUci(uci);
    if (!parsed) {
      return { san: null, fenAfter: null, error: 'Invalid UCI' };
    }
    const board = new Chess(fen);
    const move = board.move(parsed);
    if (!move) {
      return { san: null, fenAfter: null, error: 'Illegal move' };
    }
    return { san: move.san, fenAfter: board.fen() };
  } catch (e: any) {
    return { san: null, fenAfter: null, error: e?.message || 'Failed to convert UCI' };
  }
}

export function uciLineToSan(uciMoves: string[], startFen: string): UciToSanResult[] {
  if (uciMoves.length === 0) return [];
  const results: UciToSanResult[] = [];
  let board: Chess;

  try {
    board = new Chess(startFen);
  } catch (e: any) {
    return [{
      san: null,
      fenAfter: null,
      error: e?.message || 'Failed to convert UCI',
    }];
  }

  for (const uci of uciMoves) {
    const parsed = parseUci(uci);
    if (!parsed) {
      results.push({ san: null, fenAfter: null, error: 'Invalid UCI' });
      break;
    }

    const move = board.move(parsed);
    if (!move) {
      results.push({ san: null, fenAfter: null, error: 'Illegal move' });
      break;
    }

    results.push({ san: move.san, fenAfter: board.fen() });
  }

  return results;
}
