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

const assetModules = import.meta.glob('../../../assets/chess_pieces/*/*.png', {
  eager: true,
  import: 'default',
}) as Record<string, string>;

const pieceImageUrls: Record<string, Record<string, string>> = {
  normal: {},
  cats: {},
};

Object.entries(assetModules).forEach(([path, url]) => {
  const segments = path.split('/');
  const file = segments[segments.length - 1];
  const set = segments[segments.length - 2];
  const key = file.replace('.png', '');
  if (pieceImageUrls[set]) {
    pieceImageUrls[set][key] = url;
  }
});

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
