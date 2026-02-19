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

const CSS_TO_SHAPE_COLOR: Record<string, ShapeColor> = Object.fromEntries(
  Object.entries(SHAPE_COLOR_CSS).map(([k, v]) => [v, k as ShapeColor])
);

export interface StudyBoardProps {
  className?: string;
  boardWidth?: number;
}

export function StudyBoard({ className, boardWidth = 500 }: StudyBoardProps) {
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
  // localShapes is the single source of truth for the current node's shapes.
  // It is initialised from node.shapes on navigation and updated by user interaction.
  //
  // FEEDBACK-LOOP GUARD:
  //   Whenever we call setLocalShapes(), displayArrows (useMemo) gets a new
  //   reference → customArrows prop changes → react-chessboard calls clearArrows()
  //   → onArrowsChange([]) fires. suppressArrowChange is set to true before any
  //   setLocalShapes call so that spurious onArrowsChange([]) is ignored.
  const [localShapes, setLocalShapes] = useState<Shape[]>([]);
  const localShapesRef = useRef<Shape[]>([]);
  localShapesRef.current = localShapes;
  const suppressArrowChange = useRef(false);

  // Load node's shapes whenever the cursor moves to a different node.
  useEffect(() => {
    const node = state.tree.nodes[state.cursorNodeId];
    suppressArrowChange.current = true;
    setLocalShapes(node?.shapes ?? []);
  }, [state.cursorNodeId]); // eslint-disable-line react-hooks/exhaustive-deps

  const displayArrows = useMemo<[string, string, string][]>(() => {
    return localShapes
      .filter((s): s is ShapeArrow => s.type === 'arrow')
      .map((s) => [s.from, s.to, SHAPE_COLOR_CSS[s.color]]);
  }, [localShapes]);

  const displaySquareStyles = useMemo<Record<string, React.CSSProperties>>(() => {
    const styles: Record<string, React.CSSProperties> = {};
    localShapes
      .filter((s): s is ShapeCircle => s.type === 'circle')
      .forEach((s) => {
        styles[s.square] = { boxShadow: `inset 0 0 0 4px ${CIRCLE_COLOR_CSS[s.color]}` };
      });
    return styles;
  }, [localShapes]);

  // Called by react-chessboard when user finishes drawing an arrow (right-click drag).
  // `arrows` contains only the user-drawn arrows, NOT the customArrows we passed in.
  // We merge them with any already-stored arrows so stored shapes are never lost.
  const onArrowsChange = useCallback(
    (arrows: [string, string, string?][]) => {
      if (suppressArrowChange.current) {
        suppressArrowChange.current = false;
        return;
      }
      const current = localShapesRef.current;
      const circles = current.filter((s): s is ShapeCircle => s.type === 'circle');
      const existingArrows = current.filter((s): s is ShapeArrow => s.type === 'arrow');

      const drawnArrows: ShapeArrow[] = arrows.map(([from, to, color]) => ({
        type: 'arrow',
        color: (color ? (CSS_TO_SHAPE_COLOR[color] ?? 'green') : 'green') as ShapeColor,
        from: from as string,
        to: to as string,
      }));

      // Union: keep all stored arrows + append any newly drawn ones (dedup by from+to).
      const merged = [...existingArrows];
      for (const drawn of drawnArrows) {
        if (!merged.some((a) => a.from === drawn.from && a.to === drawn.to)) {
          merged.push(drawn);
        }
      }

      const newShapes = [...circles, ...merged];
      suppressArrowChange.current = true; // guard against the re-render feedback
      setLocalShapes(newShapes);
      setShapes(state.cursorNodeId, newShapes);
    },
    [state.cursorNodeId, setShapes]
  );

  // Right-click on a square (no drag) → toggle a green circle on that square.
  const onSquareRightClick = useCallback(
    (square: string) => {
      const current = localShapesRef.current;
      const idx = current.findIndex(
        (s): s is ShapeCircle => s.type === 'circle' && s.square === square
      );
      const newShapes =
        idx >= 0
          ? current.filter((_, i) => i !== idx)
          : [...current, { type: 'circle', color: 'green', square } as ShapeCircle];
      suppressArrowChange.current = true;
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
      <div className="study-board-wrapper" style={{ width: boardWidth, height: boardWidth }}>
        <Chessboard
          id="study-board"
          position={state.currentFen}
          onPieceDrop={onPieceDrop}
          boardWidth={boardWidth}
          boardOrientation={orientation}
          customDarkSquareStyle={{ backgroundColor: '#779954' }}
          customLightSquareStyle={{ backgroundColor: '#e9edcc' }}
          animationDuration={200}
          customArrows={displayArrows}
          customSquareStyles={displaySquareStyles}
          onArrowsChange={onArrowsChange}
          onSquareRightClick={onSquareRightClick}
          areArrowsAllowed={true}
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

export default StudyBoard;
