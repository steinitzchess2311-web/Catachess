import { parseFen, composeFen } from '../../chessJS/fen';

export type PieceColor = 'w' | 'b';
export type PieceType = 'p' | 'n' | 'b' | 'r' | 'q' | 'k';

export interface EditorPiece {
  color: PieceColor;
  type: PieceType;
}

export interface CastlingToggles {
  K: boolean;
  Q: boolean;
  k: boolean;
  q: boolean;
}

export const EMPTY_BOARD_FEN = '8/8/8/8/8/8/8/8 w - - 0 1';

// Expand FEN rank string to 8-element array ('.' = empty)
function expandRank(rank: string): string[] {
  const cells: string[] = [];
  for (const ch of rank) {
    const n = parseInt(ch, 10);
    if (!isNaN(n)) {
      for (let i = 0; i < n; i++) cells.push('.');
    } else {
      cells.push(ch);
    }
  }
  return cells;
}

// Compress 8-element array back to FEN rank string
function compressRank(cells: string[]): string {
  let result = '';
  let emptyCount = 0;
  for (const cell of cells) {
    if (cell === '.') {
      emptyCount++;
    } else {
      if (emptyCount > 0) {
        result += emptyCount;
        emptyCount = 0;
      }
      result += cell;
    }
  }
  if (emptyCount > 0) result += emptyCount;
  return result;
}

// "e4" → [rowIndex, colIndex] where rowIndex 0 = rank 8 (top)
function squareToIndices(square: string): [number, number] {
  const col = square.charCodeAt(0) - 'a'.charCodeAt(0);
  const rank = parseInt(square[1], 10);
  const row = 8 - rank;
  return [row, col];
}

function pieceToFenChar(piece: EditorPiece): string {
  return piece.color === 'w' ? piece.type.toUpperCase() : piece.type;
}

function fenCharToPiece(ch: string): EditorPiece | null {
  if (ch === '.') return null;
  const color: PieceColor = ch === ch.toUpperCase() ? 'w' : 'b';
  const type = ch.toLowerCase() as PieceType;
  return { color, type };
}

export function getPieceAt(fen: string, square: string): EditorPiece | null {
  const parts = parseFen(fen);
  if (!parts) return null;
  const ranks = parts.position.split('/');
  const [row, col] = squareToIndices(square);
  const cells = expandRank(ranks[row]);
  return fenCharToPiece(cells[col]);
}

// Place a piece on a square — clears en passant and halfmove clock
export function placePiece(fen: string, square: string, piece: EditorPiece): string {
  const parts = parseFen(fen);
  if (!parts) return fen;
  const ranks = parts.position.split('/');
  const [row, col] = squareToIndices(square);
  const cells = expandRank(ranks[row]);
  cells[col] = pieceToFenChar(piece);
  ranks[row] = compressRank(cells);
  return composeFen({ ...parts, position: ranks.join('/'), enPassant: '-', halfmoveClock: 0 });
}

// Remove a piece from a square — clears en passant and halfmove clock
export function removePiece(fen: string, square: string): string {
  const parts = parseFen(fen);
  if (!parts) return fen;
  const ranks = parts.position.split('/');
  const [row, col] = squareToIndices(square);
  const cells = expandRank(ranks[row]);
  cells[col] = '.';
  ranks[row] = compressRank(cells);
  return composeFen({ ...parts, position: ranks.join('/'), enPassant: '-', halfmoveClock: 0 });
}

// Move a piece from one square to another (editor-style, no legality check)
export function movePiece(fen: string, from: string, to: string): string {
  const piece = getPieceAt(fen, from);
  if (!piece) return fen;
  // Remove from source first (keeps FEN valid)
  const parts = parseFen(fen);
  if (!parts) return fen;
  const ranks = parts.position.split('/');

  const [fromRow, fromCol] = squareToIndices(from);
  const fromCells = expandRank(ranks[fromRow]);
  fromCells[fromCol] = '.';
  ranks[fromRow] = compressRank(fromCells);

  const [toRow, toCol] = squareToIndices(to);
  const toCells = expandRank(ranks[toRow]);
  toCells[toCol] = pieceToFenChar(piece);
  ranks[toRow] = compressRank(toCells);

  return composeFen({ ...parts, position: ranks.join('/'), enPassant: '-', halfmoveClock: 0 });
}

export function setTurn(fen: string, turn: 'w' | 'b'): string {
  const parts = parseFen(fen);
  if (!parts) return fen;
  return composeFen({ ...parts, turn });
}

export function setCastling(fen: string, castling: string): string {
  const parts = parseFen(fen);
  if (!parts) return fen;
  return composeFen({ ...parts, castling: castling || '-' });
}

export function setEnPassant(fen: string, ep: string): string {
  const parts = parseFen(fen);
  if (!parts) return fen;
  return composeFen({ ...parts, enPassant: ep || '-' });
}

// Compute which castling is physically possible based on king/rook positions
export function computeAvailableCastling(fen: string): CastlingToggles {
  const e1 = getPieceAt(fen, 'e1');
  const h1 = getPieceAt(fen, 'h1');
  const a1 = getPieceAt(fen, 'a1');
  const e8 = getPieceAt(fen, 'e8');
  const h8 = getPieceAt(fen, 'h8');
  const a8 = getPieceAt(fen, 'a8');

  const whiteKingOnE1 = e1 !== null && e1.type === 'k' && e1.color === 'w';
  const blackKingOnE8 = e8 !== null && e8.type === 'k' && e8.color === 'b';

  return {
    K: whiteKingOnE1 && h1 !== null && h1.type === 'r' && h1.color === 'w',
    Q: whiteKingOnE1 && a1 !== null && a1.type === 'r' && a1.color === 'w',
    k: blackKingOnE8 && h8 !== null && h8.type === 'r' && h8.color === 'b',
    q: blackKingOnE8 && a8 !== null && a8.type === 'r' && a8.color === 'b',
  };
}

export function castlingToString(toggles: CastlingToggles): string {
  const s = [
    toggles.K ? 'K' : '',
    toggles.Q ? 'Q' : '',
    toggles.k ? 'k' : '',
    toggles.q ? 'q' : '',
  ].join('');
  return s || '-';
}

export function parseCastlingString(castling: string): CastlingToggles {
  return {
    K: castling.includes('K'),
    Q: castling.includes('Q'),
    k: castling.includes('k'),
    q: castling.includes('q'),
  };
}

// Restrict castling to what's physically possible (call after any piece move/place/remove)
export function restrictCastlingToAvailable(fen: string): string {
  const parts = parseFen(fen);
  if (!parts) return fen;
  const current = parseCastlingString(parts.castling);
  const available = computeAvailableCastling(fen);
  const restricted: CastlingToggles = {
    K: current.K && available.K,
    Q: current.Q && available.Q,
    k: current.k && available.k,
    q: current.q && available.q,
  };
  const newStr = castlingToString(restricted);
  if (newStr === parts.castling) return fen;
  return composeFen({ ...parts, castling: newStr });
}
