import React, { useState, useEffect } from 'react';
import type { CastlingToggles, EditorPiece } from './fenManipulation';
import type { Selected } from './useBoardEditor';

interface EditorControlsProps {
  fen: string;
  legalFen: string | undefined;
  selected: Selected;
  turn: 'w' | 'b';
  castling: CastlingToggles;
  enPassant: string;
  availableCastling: CastlingToggles;
  onSetFen: (fen: string) => void;
  onSetSelected: (s: Selected) => void;
  onSetTurn: (t: 'w' | 'b') => void;
  onSetCastling: (c: CastlingToggles) => void;
  onSetEnPassant: (ep: string) => void;
  onFlip: () => void;
  onClear: () => void;
  onReset: () => void;
  onCreateChapter?: (fen: string) => void;
}

export function EditorControls({
  fen,
  legalFen,
  selected,
  turn,
  castling,
  enPassant,
  availableCastling,
  onSetFen,
  onSetSelected,
  onSetTurn,
  onSetCastling,
  onSetEnPassant,
  onFlip,
  onClear,
  onReset,
  onCreateChapter,
}: EditorControlsProps) {
  const [fenInput, setFenInput] = useState(fen);
  const [fenError, setFenError] = useState<string | null>(null);

  // Sync FEN input when external FEN changes (but only if not currently editing)
  useEffect(() => {
    setFenInput(fen);
    setFenError(null);
  }, [fen]);

  const handleFenInputChange = (value: string) => {
    setFenInput(value);
    setFenError(null);
  };

  const commitFenInput = () => {
    const trimmed = fenInput.trim();
    if (!trimmed) return;
    // Basic structure check before dispatching
    const parts = trimmed.split(/\s+/);
    if (parts.length < 4) {
      setFenError('Invalid FEN — need at least 4 fields');
      return;
    }
    onSetFen(trimmed);
  };

  const handleCastlingToggle = (key: keyof CastlingToggles) => {
    onSetCastling({ ...castling, [key]: !castling[key] });
  };

  const isPointer = selected === 'pointer';
  const isTrash = selected === 'trash';
  const isSelectedPiece = typeof selected === 'object';

  return (
    <div className="board-editor-controls">
      {/* Tool selector */}
      <section className="board-editor-section">
        <div className="board-editor-tools">
          <button
            type="button"
            className={`board-editor-tool-btn${isPointer ? ' is-active' : ''}`}
            onClick={() => onSetSelected('pointer')}
            title="Move pieces (drag)"
          >
            ✋
          </button>
          <button
            type="button"
            className={`board-editor-tool-btn${isTrash ? ' is-active' : ''}`}
            onClick={() => onSetSelected('trash')}
            title="Delete pieces (click)"
          >
            🗑
          </button>
        </div>
        {isSelectedPiece && (
          <div className="board-editor-tool-hint">
            Click board squares to place · Click same piece to remove
          </div>
        )}
        {isTrash && (
          <div className="board-editor-tool-hint">
            Click pieces to delete · Right-click to flip color
          </div>
        )}
        {isPointer && (
          <div className="board-editor-tool-hint">
            Drag pieces to move · Right-click to flip color
          </div>
        )}
      </section>

      {/* Turn */}
      <section className="board-editor-section">
        <label className="board-editor-label">Turn</label>
        <div className="board-editor-radio-group">
          <label className="board-editor-radio">
            <input
              type="radio"
              name="turn"
              checked={turn === 'w'}
              onChange={() => onSetTurn('w')}
            />
            White
          </label>
          <label className="board-editor-radio">
            <input
              type="radio"
              name="turn"
              checked={turn === 'b'}
              onChange={() => onSetTurn('b')}
            />
            Black
          </label>
        </div>
      </section>

      {/* Castling */}
      <section className="board-editor-section">
        <label className="board-editor-label">Castling</label>
        <div className="board-editor-castling-grid">
          {(['K', 'Q', 'k', 'q'] as const).map((key) => (
            <label
              key={key}
              className={`board-editor-castling-item${!availableCastling[key] ? ' is-disabled' : ''}`}
              title={availableCastling[key] ? '' : 'Requires king and rook on original squares'}
            >
              <input
                type="checkbox"
                checked={castling[key]}
                disabled={!availableCastling[key]}
                onChange={() => handleCastlingToggle(key)}
              />
              {key === 'K' ? '♔ O-O' : key === 'Q' ? '♔ O-O-O' : key === 'k' ? '♚ O-O' : '♚ O-O-O'}
            </label>
          ))}
        </div>
      </section>

      {/* En passant */}
      <section className="board-editor-section">
        <label className="board-editor-label">En passant</label>
        <select
          className="board-editor-select"
          value={enPassant}
          onChange={(e) => onSetEnPassant(e.target.value)}
        >
          <option value="-">None (-)</option>
          {['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'].map((file) => {
            const rank = turn === 'w' ? '6' : '3';
            const sq = `${file}${rank}`;
            return (
              <option key={sq} value={sq}>
                {sq}
              </option>
            );
          })}
        </select>
      </section>

      {/* FEN display / input */}
      <section className="board-editor-section">
        <label className="board-editor-label">FEN</label>
        <textarea
          className="board-editor-fen-input"
          value={fenInput}
          onChange={(e) => handleFenInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              commitFenInput();
            }
          }}
          onBlur={commitFenInput}
          rows={2}
          spellCheck={false}
        />
        {fenError && <div className="board-editor-error">{fenError}</div>}
        {!legalFen && !fenError && (
          <div className="board-editor-error">Position is not legal</div>
        )}
      </section>

      {/* Copy FEN */}
      <section className="board-editor-section">
        <button
          type="button"
          className="board-editor-btn"
          onClick={() => navigator.clipboard.writeText(fen)}
        >
          Copy FEN
        </button>
      </section>

      {/* Board actions */}
      <section className="board-editor-section">
        <div className="board-editor-action-row">
          <button type="button" className="board-editor-btn" onClick={onFlip}>
            Flip
          </button>
          <button type="button" className="board-editor-btn" onClick={onReset}>
            Reset
          </button>
          <button type="button" className="board-editor-btn" onClick={onClear}>
            Clear
          </button>
        </div>
      </section>

      {/* Create chapter */}
      {onCreateChapter && (
        <section className="board-editor-section">
          <button
            type="button"
            className="board-editor-btn primary"
            disabled={!legalFen}
            onClick={() => legalFen && onCreateChapter(legalFen)}
            title={!legalFen ? 'Position must be legal to create a chapter' : ''}
          >
            Create Chapter
          </button>
        </section>
      )}
    </div>
  );
}
