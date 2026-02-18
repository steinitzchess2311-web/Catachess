import { getFullmoveNumber, getTurn } from '../../chessJS/fen';

/**
 * Format engine score for display.
 * Stockfish scores are from the side-to-move's perspective (positive = side to move is better).
 * We normalize to white's perspective: positive = white better (+), negative = black better (-).
 */
export function formatScore(raw: number | string, turn: 'w' | 'b' = 'w'): string {
  if (typeof raw === 'string') {
    if (raw.startsWith('mate')) {
      const mateNum = parseInt(raw.slice(4), 10);
      // Flip for black to move so positive still means white is winning
      const normalized = turn === 'b' ? -mateNum : mateNum;
      return normalized > 0 ? `+M${normalized}` : `-M${Math.abs(normalized)}`;
    }
    return raw;
  }
  // Flip CP score for black to move
  const normalized = turn === 'b' ? -raw : raw;
  const value = normalized / 100;
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
}

/**
 * Format SAN moves with move numbers based on FEN position
 */
export function formatSanWithMoveNumbers(sanMoves: string[], fen: string): string {
  if (sanMoves.length === 0) return '';
  const turn = getTurn(fen) || 'w';
  let moveNumber = getFullmoveNumber(fen) || 1;
  const parts: string[] = [];
  let isWhite = turn === 'w';
  let isFirst = true;
  for (const san of sanMoves) {
    if (isWhite) {
      parts.push(`${moveNumber}.${san}`);
    } else if (isFirst && turn === 'b') {
      parts.push(`${moveNumber}...${san}`);
      moveNumber += 1;
    } else {
      parts.push(`${san}`);
      moveNumber += 1;
    }
    isFirst = false;
    isWhite = !isWhite;
  }
  return parts.join(' ');
}

/**
 * Format probability as percentage
 */
export function formatProbability(value?: number): string {
  if (value === undefined || value === null || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Format tags array for display
 */
export function formatTags(tags?: string[]): string {
  if (!tags || tags.length === 0) return '—';
  return tags.join(', ');
}
