import React from 'react';
import { getPieceImageUrl } from '@ui/modules/chess_pieces';
import type { EditorPiece, PieceColor, PieceType } from './fenManipulation';
import type { Selected } from './useBoardEditor';

const PIECE_ORDER: PieceType[] = ['k', 'q', 'r', 'b', 'n', 'p'];

interface SparePiecesProps {
  color: PieceColor;
  selected: Selected;
  onSelect: (piece: EditorPiece) => void;
  pieceSize: number;
}

export function SparePieces({ color, selected, onSelect, pieceSize }: SparePiecesProps) {
  return (
    <div
      className="board-editor-spare"
      style={{ height: pieceSize, display: 'flex', alignItems: 'center' }}
    >
      {PIECE_ORDER.map((type) => {
        const piece: EditorPiece = { color, type };
        const imgUrl = getPieceImageUrl({ type, color });
        const isSelected =
          typeof selected === 'object' &&
          selected.color === color &&
          selected.type === type;

        return (
          <button
            key={type}
            className={`board-editor-spare-piece${isSelected ? ' is-selected' : ''}`}
            style={{ width: pieceSize, height: pieceSize }}
            onClick={() => onSelect(piece)}
            title={`${color === 'w' ? 'White' : 'Black'} ${type.toUpperCase()}`}
            type="button"
          >
            <img
              src={imgUrl}
              alt={`${color}${type}`}
              style={{ width: '100%', height: '100%', display: 'block' }}
              draggable={false}
            />
          </button>
        );
      })}
    </div>
  );
}
