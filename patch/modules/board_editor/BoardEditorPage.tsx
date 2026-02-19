import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Chessboard, ChessboardDnDProvider } from 'react-chessboard';
import { api } from '@ui/assets/api';
import { useBoardEditor } from './useBoardEditor';
import { SparePieces } from './SparePieces';
import { EditorControls } from './EditorControls';
import './BoardEditor.css';

export function BoardEditorPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const studyId = searchParams.get('study_id') || undefined;

  const boardContainerRef = useRef<HTMLDivElement>(null);
  const [boardWidth, setBoardWidth] = useState(480);

  const {
    fen,
    legalFen,
    selected,
    orientation,
    turn,
    castling,
    enPassant,
    availableCastling,
    setFen,
    setSelected,
    onSquareClick,
    onSquareRightClick,
    onPieceDrop,
    onPieceDropOffBoard,
    onSparePieceDrop,
    setTurnAction,
    setCastlingAction,
    setEnPassantAction,
    flipBoard,
    clearBoard,
    resetToStart,
  } = useBoardEditor();

  // Measure board container for responsive sizing
  useEffect(() => {
    if (!boardContainerRef.current) return;
    const measure = () => {
      const el = boardContainerRef.current;
      if (!el) return;
      const w = el.clientWidth;
      if (w > 0) setBoardWidth(w);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(boardContainerRef.current);
    return () => ro.disconnect();
  }, []);

  const pieceSize = Math.floor(boardWidth / 8);

  const handleCreateChapter = useCallback(
    async (fenStr: string) => {
      if (!studyId) return;
      try {
        const title = prompt('Chapter title:', 'New Position') || 'New Position';
        await api.post('/api/v1/import-export/fen/import', {
          study_id: studyId,
          chapter_title: title,
          fen: fenStr,
        });
        navigate(`/patch/workspace/${studyId}`);
      } catch (e) {
        alert('Failed to create chapter: ' + (e instanceof Error ? e.message : String(e)));
      }
    },
    [studyId, navigate]
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target?.closest('input, textarea')) return;
      if (e.key === 'f' || e.key === 'F') flipBoard();
      if (e.key === 'Escape') setSelected('pointer');
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [flipBoard, setSelected]);

  const boardCursor = selected === 'trash' ? 'crosshair' : 'default';
  const isDraggable = selected === 'pointer';

  return (
    <div className="board-editor-page">
      <div className="board-editor-header">
        <button
          type="button"
          className="board-editor-back-btn"
          onClick={() => navigate(studyId ? `/${studyId}` : '/workspace/private')}
        >
          ← Back
        </button>
        <h2 className="board-editor-title">Board Editor</h2>
      </div>

      {/* ChessboardDnDProvider lets SparePiece drag onto the Chessboard */}
      <ChessboardDnDProvider>
        <div className="board-editor-layout">
          {/* Board column */}
          <div className="board-editor-board-col">
            <SparePieces
              color={orientation === 'white' ? 'b' : 'w'}
              selected={selected}
              onSelect={setSelected}
              pieceSize={pieceSize}
            />

            <div
              ref={boardContainerRef}
              className="board-editor-board-wrap"
              style={{ cursor: boardCursor }}
            >
              <Chessboard
                id="board-editor"
                position={fen}
                boardWidth={boardWidth}
                boardOrientation={orientation}
                arePiecesDraggable={isDraggable}
                dropOffBoard="trash"
                onPieceDrop={onPieceDrop}
                onPieceDropOffBoard={onPieceDropOffBoard}
                onSparePieceDrop={onSparePieceDrop}
                onSquareClick={onSquareClick}
                onSquareRightClick={onSquareRightClick}
                animationDuration={100}
                customDarkSquareStyle={{ backgroundColor: '#779954' }}
                customLightSquareStyle={{ backgroundColor: '#e9edcc' }}
              />
            </div>

            <SparePieces
              color={orientation === 'white' ? 'w' : 'b'}
              selected={selected}
              onSelect={setSelected}
              pieceSize={pieceSize}
            />
          </div>

          {/* Controls column */}
          <EditorControls
            fen={fen}
            legalFen={legalFen}
            selected={selected}
            turn={turn}
            castling={castling}
            enPassant={enPassant}
            availableCastling={availableCastling}
            onSetFen={setFen}
            onSetSelected={setSelected}
            onSetTurn={setTurnAction}
            onSetCastling={setCastlingAction}
            onSetEnPassant={setEnPassantAction}
            onFlip={flipBoard}
            onClear={clearBoard}
            onReset={resetToStart}
            onCreateChapter={studyId ? handleCreateChapter : undefined}
          />
        </div>
      </ChessboardDnDProvider>
    </div>
  );
}

export default BoardEditorPage;
