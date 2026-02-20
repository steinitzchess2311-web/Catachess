import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { useStudy } from '../studyContext';
import { getMoveSan } from '../chessJS/replay';
import { StudyTree } from '../tree/StudyTree';
import type { Shape, ShapeArrow, ShapeCircle, ShapeColor } from '../tree/type';

const SHAPE_COLOR_CSS: Record<ShapeColor, string> = {
  green:  'rgba(0, 155, 60, 0.8)',
  red:    'rgba(220, 50, 40, 0.8)',
  blue:   'rgba(50, 130, 220, 0.8)',
  yellow: 'rgba(255, 200, 0, 0.8)',
};

const CIRCLE_COLOR_CSS: Record<ShapeColor, string> = {
  green:  'rgba(0, 155, 60, 0.6)',
  red:    'rgba(220, 50, 40, 0.6)',
  blue:   'rgba(50, 130, 220, 0.6)',
  yellow: 'rgba(255, 200, 0, 0.6)',
};

export interface StudyBoardProps {
  className?: string;
  boardWidth?: number;
}

function StudyBoardInner({ className, boardWidth = 500 }: StudyBoardProps) {
  const { state, addMove, setError, selectNode, setShapes } = useStudy();
  const [orientation, setOrientation] = useState<'white' | 'black'>('white');

  const toggleFlip = useCallback(() => {
    setOrientation((prev) => (prev === 'white' ? 'black' : 'white'));
  }, []);

  const moveToStart = useCallback(() => {
    selectNode(state.tree.rootId);
  }, [selectNode, state.tree.rootId]);

  const moveToPrev = useCallback(() => {
    const treeOps = new StudyTree(state.tree);
    const path = treeOps.getPathToNode(state.cursorNodeId);
    if (path.length <= 1) return;
    selectNode(path[path.length - 2]);
  }, [selectNode, state.cursorNodeId, state.tree]);

  const moveToNext = useCallback(() => {
    const current = state.tree.nodes[state.cursorNodeId];
    if (!current || current.children.length === 0) return;
    selectNode(current.children[0]);
  }, [selectNode, state.cursorNodeId, state.tree.nodes]);

  const moveToEnd = useCallback(() => {
    const treeOps = new StudyTree(state.tree);
    const mainline = treeOps.getMainline();
    if (mainline.length === 0) return;
    selectNode(mainline[mainline.length - 1].id);
  }, [selectNode, state.tree]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && (target.closest('input, textarea, [contenteditable="true"]') || target.isContentEditable)) {
        return;
      }
      switch (event.key) {
        case 'f':
        case 'F':
          event.preventDefault();
          toggleFlip();
          break;
        case 'ArrowLeft':
        case 'Backspace':
          event.preventDefault();
          moveToPrev();
          break;
        case 'ArrowRight':
          event.preventDefault();
          moveToNext();
          break;
        case 'ArrowUp':
          event.preventDefault();
          moveToStart();
          break;
        case 'ArrowDown':
          event.preventDefault();
          moveToEnd();
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [moveToEnd, moveToNext, moveToPrev, moveToStart, toggleFlip]);

  // ── Shape state ──────────────────────────────────────────────────────────────
  const [localShapes, setLocalShapes] = useState<Shape[]>([]);
  const localShapesRef = useRef<Shape[]>([]);
  localShapesRef.current = localShapes;

  useEffect(() => {
    const node = state.tree.nodes[state.cursorNodeId];
    setLocalShapes(node?.shapes ?? []);
  }, [state.cursorNodeId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Custom arrow drawing ─────────────────────────────────────────────────────
  const boardWrapperRef = useRef<HTMLDivElement>(null);
  const rightDragFromRef = useRef<string | null>(null);
  const [inProgressArrow, setInProgressArrow] = useState<[string, string, string] | null>(null);

  const getSquare = useCallback(
    (e: React.MouseEvent): string | null => {
      const rect = boardWrapperRef.current?.getBoundingClientRect();
      if (!rect) return null;
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const sz = boardWidth / 8;
      if (x < 0 || y < 0 || x > boardWidth || y > boardWidth) return null;
      const fi = Math.floor(x / sz);
      const ri = Math.floor(y / sz);
      if (fi < 0 || fi > 7 || ri < 0 || ri > 7) return null;
      const file = orientation === 'black' ? 7 - fi : fi;
      const rank = orientation === 'black' ? ri : 7 - ri;
      return (
        String.fromCharCode('a'.charCodeAt(0) + file) +
        String.fromCharCode('1'.charCodeAt(0) + rank)
      );
    },
    [boardWidth, orientation]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 2) return;
      rightDragFromRef.current = getSquare(e);
    },
    [getSquare]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!(e.buttons & 2) || !rightDragFromRef.current) {
        setInProgressArrow(null);
        return;
      }
      const to = getSquare(e);
      setInProgressArrow(
        to && to !== rightDragFromRef.current
          ? [rightDragFromRef.current, to, SHAPE_COLOR_CSS.green]
          : null
      );
    },
    [getSquare]
  );

  const handleMouseUp = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 2) return;
      const from = rightDragFromRef.current;
      rightDragFromRef.current = null;
      setInProgressArrow(null);
      if (!from) return;
      const to = getSquare(e);
      if (!to || to === from) return;

      const current = localShapesRef.current;
      const idx = current.findIndex(
        (s): s is ShapeArrow => s.type === 'arrow' && s.from === from && s.to === to
      );
      const newShapes: Shape[] =
        idx >= 0
          ? current.filter((_, i) => i !== idx)
          : [...current, { type: 'arrow', color: 'green', from, to } as ShapeArrow];
      setLocalShapes(newShapes);
      setShapes(state.cursorNodeId, newShapes);
    },
    [getSquare, state.cursorNodeId, setShapes]
  );

  const allDisplayArrows = useMemo<[string, string, string][]>(() => {
    const stored = localShapes
      .filter((s): s is ShapeArrow => s.type === 'arrow')
      .map((s): [string, string, string] => [s.from, s.to, SHAPE_COLOR_CSS[s.color]]);
    return inProgressArrow ? [...stored, inProgressArrow] : stored;
  }, [localShapes, inProgressArrow]);

  const displaySquareStyles = useMemo<Record<string, React.CSSProperties>>(() => {
    const styles: Record<string, React.CSSProperties> = {};
    localShapes
      .filter((s): s is ShapeCircle => s.type === 'circle')
      .forEach((s) => {
        styles[s.square] = { boxShadow: `inset 0 0 0 4px ${CIRCLE_COLOR_CSS[s.color]}` };
      });
    return styles;
  }, [localShapes]);

  const onSquareRightClick = useCallback(
    (square: string) => {
      const current = localShapesRef.current;
      const idx = current.findIndex(
        (s): s is ShapeCircle => s.type === 'circle' && s.square === square
      );
      const newShapes: Shape[] =
        idx >= 0
          ? current.filter((_, i) => i !== idx)
          : [...current, { type: 'circle', color: 'green', square } as ShapeCircle];
      setLocalShapes(newShapes);
      setShapes(state.cursorNodeId, newShapes);
    },
    [state.cursorNodeId, setShapes]
  );

  const onPieceDrop = useCallback(
    (sourceSquare: string, targetSquare: string, piece: string) => {
      const san = getMoveSan(state.currentFen, sourceSquare, targetSquare);
      if (!san) {
        setError('REPLAY_ERROR', 'Illegal move', { from: sourceSquare, to: targetSquare, piece });
        return false;
      }
      try {
        addMove(san);
        return true;
      } catch (e) {
        setError('REPLAY_ERROR', 'Failed to add move');
        return false;
      }
    },
    [state.currentFen, addMove, setError]
  );

  return (
    <div
      className={`study-board-container ${className || ''}`}
      style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: boardWidth }}
    >
      <div
        ref={boardWrapperRef}
        className="study-board-wrapper"
        style={{ width: boardWidth, height: boardWidth }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onContextMenu={(e) => e.preventDefault()}
      >
        <Chessboard
          id="study-board"
          position={state.currentFen}
          onPieceDrop={onPieceDrop}
          boardWidth={boardWidth}
          boardOrientation={orientation}
          customDarkSquareStyle={{ backgroundColor: '#779954' }}
          customLightSquareStyle={{ backgroundColor: '#e9edcc' }}
          animationDuration={150}
          customArrows={allDisplayArrows}
          customSquareStyles={displaySquareStyles}
          onSquareRightClick={onSquareRightClick}
          areArrowsAllowed={false}
        />
      </div>
      <div className="study-board-nav">
        <div className="study-board-nav-group">
          <button type="button" className="study-board-nav-button" onClick={moveToStart}>|&lt;</button>
          <button type="button" className="study-board-nav-button" onClick={moveToPrev}>&lt;</button>
          <button type="button" className="study-board-nav-button" onClick={moveToNext}>&gt;</button>
          <button type="button" className="study-board-nav-button" onClick={moveToEnd}>&gt;|</button>
          <button type="button" className="study-board-nav-button" onClick={toggleFlip}>Flip</button>
        </div>
      </div>
    </div>
  );
}

export const StudyBoard = React.memo(StudyBoardInner);
export default StudyBoard;
