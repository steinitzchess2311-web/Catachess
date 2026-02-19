import React, { useCallback, useEffect, useMemo, useState } from 'react';
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

// Map CSS back to ShapeColor for arrows drawn by the user
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
  const isFlipped = orientation === 'black';
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
    const prevId = path[path.length - 2];
    selectNode(prevId);
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
    const lastNode = mainline[mainline.length - 1];
    selectNode(lastNode.id);
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

  // Derive customArrows from current node's shapes
  const customArrows = useMemo<[string, string, string][]>(() => {
    const node = state.tree.nodes[state.cursorNodeId];
    if (!node?.shapes) return [];
    return node.shapes
      .filter((s): s is ShapeArrow => s.type === 'arrow')
      .map((s) => [s.from, s.to, SHAPE_COLOR_CSS[s.color]]);
  }, [state.tree.nodes, state.cursorNodeId]);

  // Derive circle highlights from current node's shapes
  const customSquareStyles = useMemo<Record<string, React.CSSProperties>>(() => {
    const node = state.tree.nodes[state.cursorNodeId];
    if (!node?.shapes) return {};
    const styles: Record<string, React.CSSProperties> = {};
    node.shapes
      .filter((s): s is ShapeCircle => s.type === 'circle')
      .forEach((s) => {
        styles[s.square] = {
          boxShadow: `inset 0 0 0 4px ${CIRCLE_COLOR_CSS[s.color]}`,
        };
      });
    return styles;
  }, [state.tree.nodes, state.cursorNodeId]);

  // Capture user-drawn arrows and save to current node
  const onArrowsChange = useCallback(
    (arrows: [string, string, string?][]) => {
      const node = state.tree.nodes[state.cursorNodeId];
      const circles: Shape[] = node?.shapes?.filter((s): s is ShapeCircle => s.type === 'circle') ?? [];
      const newArrows: ShapeArrow[] = arrows.map(([from, to, color]) => ({
        type: 'arrow',
        color: (color ? (CSS_TO_SHAPE_COLOR[color] ?? 'green') : 'green') as ShapeColor,
        from,
        to,
      }));
      setShapes(state.cursorNodeId, [...circles, ...newArrows]);
    },
    [state.cursorNodeId, state.tree.nodes, setShapes]
  );

  const onPieceDrop = useCallback(
    (sourceSquare: string, targetSquare: string, piece: string) => {
      // 1. Convert to SAN and validate using current FEN
      const san = getMoveSan(state.currentFen, sourceSquare, targetSquare);

      if (!san) {
        // Illegal move
        setError('REPLAY_ERROR', 'Illegal move', {
          from: sourceSquare,
          to: targetSquare,
          piece,
        });
        return false;
      }

      // 2. Dispatch move
      try {
        addMove(san);
        return true;
      } catch (e) {
        // Should not happen if getMoveSan validated it, but just in case
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
          customArrows={customArrows}
          customSquareStyles={customSquareStyles}
          onArrowsChange={onArrowsChange}
          areArrowsAllowed={true}
        />
      </div>
      <div className="study-board-nav">
        <div className="study-board-nav-group">
          <button type="button" className="study-board-nav-button" onClick={moveToStart}>|&lt;</button>
          <button type="button" className="study-board-nav-button" onClick={moveToPrev}>&lt;</button>
          <button type="button" className="study-board-nav-button" onClick={moveToNext}>&gt;</button>
          <button type="button" className="study-board-nav-button" onClick={moveToEnd}>&gt;|</button>
          <button
            type="button"
            className="study-board-nav-button"
            onClick={toggleFlip}
          >
            Flip
          </button>
        </div>
      </div>
    </div>
  );
}

export default StudyBoard;
