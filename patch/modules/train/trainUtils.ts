/**
 * trainUtils.ts - Utility functions for train mode
 */

/**
 * Extracts move number and turn from a FEN string.
 * FEN format: "pieces activeColor castling ep halfmove fullmove"
 */
export function getMoveInfoFromFen(fen: string): { moveNumber: number; isWhiteTurn: boolean } {
  const parts = fen.split(' ');
  const activeColor = parts[1] ?? 'w';
  const fullmove = parseInt(parts[5] ?? '1', 10);
  const isWhiteTurn = activeColor === 'w';
  return {
    moveNumber: isNaN(fullmove) ? 1 : fullmove,
    isWhiteTurn,
  };
}

/**
 * Computes the starting ply from a FEN position.
 * Ply 1 = White's first move (move 1).
 * Ply 2 = Black's first move (move 1).
 * Formula: startPly = (moveNumber - 1) * 2 + (isWhiteTurn ? 1 : 2)
 */
export function getStartPlyFromFen(fen: string): number {
  const { moveNumber, isWhiteTurn } = getMoveInfoFromFen(fen);
  return (moveNumber - 1) * 2 + (isWhiteTurn ? 1 : 2);
}
