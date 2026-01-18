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

/**
 * Get the URL for a given piece in the current set.
 */
export function getPieceImageUrl(piece: { type: string; color: string }): string {
  const set = pieceSets[currentSetIndex];
  return `/assets/chess_pieces/${set.path}/${piece.color}_${piece.type}.svg`;
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
