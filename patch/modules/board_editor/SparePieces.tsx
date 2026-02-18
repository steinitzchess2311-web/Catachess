import React from 'react';
import { SparePiece } from 'react-chessboard';
import type { EditorPiece, PieceColor, PieceType } from './fenManipulation';
import type { Selected } from './useBoardEditor';

const PIECE_ORDER: PieceType[] = ['k', 'q', 'r', 'b', 'n', 'p'];

// EditorPiece { color: 'w'|'b', type: 'q'|... } → react-chessboard "wQ" format
export function toRcbPiece(color: PieceColor, type: PieceType): string {
  return `${color}${type.toUpperCase()}`;
}

interface SparePiecesProps {
  color: PieceColor;
  selected: Selected;
  onSelect: (piece: EditorPiece) => void;
  pieceSize: number;
}

export function SparePieces({ color, selected, onSelect, pieceSize }: SparePiecesProps) {
  return (
    <div className="board-editor-spare" style={{ height: pieceSize, display: 'flex', alignItems: 'center' }}>
      {PIECE_ORDER.map((type) => {
        const piece: EditorPiece = { color, type };
        const rcbPiece = toRcbPiece(color, type);
        const isSelected =
          typeof selected === 'object' &&
          selected.color === color &&
          selected.type === type;

        return (
          <div
            key={type}
            className={`board-editor-spare-piece${isSelected ? ' is-selected' : ''}`}
            style={{ width: pieceSize, height: pieceSize }}
            onClick={() => onSelect(piece)}
            title={`${color === 'w' ? 'White' : 'Black'} ${type.toUpperCase()}`}
          >
            <SparePiece
              piece={rcbPiece as any}
              width={pieceSize}
              dndId={`spare-${rcbPiece}`}
            />
          </div>
        );
      })}
    </div>
  );
}
