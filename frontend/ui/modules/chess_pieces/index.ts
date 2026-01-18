/**
 * Chess Piece Sets Module
 *
 * Manages different visual styles for chess pieces.
 */

export interface PieceSet {
  name: string;
  path: string;
}

export const pieceSets: PieceSet[] = [
  { name: 'Normal', path: 'normal' },
  { name: 'Cats', path: 'cats' },
];

let currentSetIndex = 0;

const assetsBase = '/assets/pieces';

const pieceImageUrls: Record<string, Record<string, string>> = {
  normal: {
    white_pawn: `${assetsBase}/normal/white_pawn.png`,
    white_knight: `${assetsBase}/normal/white_knight.png`,
    white_bishop: `${assetsBase}/normal/white_bishop.png`,
    white_rook: `${assetsBase}/normal/white_rook.png`,
    white_queen: `${assetsBase}/normal/white_queen.png`,
    white_king: `${assetsBase}/normal/white_king.png`,
    black_pawn: `${assetsBase}/normal/black_pawn.png`,
    black_knight: `${assetsBase}/normal/black_knight.png`,
    black_bishop: `${assetsBase}/normal/black_bishop.png`,
    black_rook: `${assetsBase}/normal/black_rook.png`,
    black_queen: `${assetsBase}/normal/black_queen.png`,
    black_king: `${assetsBase}/normal/black_king.png`,
  },
  cats: {
    white_pawn: `${assetsBase}/cats/white_pawn.png`,
    white_knight: `${assetsBase}/cats/white_knight.png`,
    white_bishop: `${assetsBase}/cats/white_bishop.png`,
    white_rook: `${assetsBase}/cats/white_rook.png`,
    white_queen: `${assetsBase}/cats/white_queen.png`,
    white_king: `${assetsBase}/cats/white_king.png`,
    black_pawn: `${assetsBase}/cats/black_pawn.png`,
    black_knight: `${assetsBase}/cats/black_knight.png`,
    black_bishop: `${assetsBase}/cats/black_bishop.png`,
    black_rook: `${assetsBase}/cats/black_rook.png`,
    black_queen: `${assetsBase}/cats/black_queen.png`,
    black_king: `${assetsBase}/cats/black_king.png`,
  },
};

/**
 * Get the URL for a given piece in the current set.
 */
export function getPieceImageUrl(piece: { type: string; color: string }): string {
  const set = pieceSets[currentSetIndex];
  const key = `${piece.color}_${piece.type}`;
  return pieceImageUrls[set.path]?.[key] || '';
}

/**
 * Cycle to the next piece set.
 */
export function nextPieceSet(): void {
  currentSetIndex = (currentSetIndex + 1) % pieceSets.length;
}

/**
 * Get the current piece set.
 */
export function getCurrentPieceSet(): PieceSet {
  return pieceSets[currentSetIndex];
}
