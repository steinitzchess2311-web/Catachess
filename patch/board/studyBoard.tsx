import React, { useCallback } from 'react';
import { Chessboard } from 'react-chessboard';
import { useStudy } from '../studyContext';
import { getMoveSan } from '../chessJS/replay';
import { StudyTree } from '../tree/StudyTree';

export interface StudyBoardProps {
  className?: string;
  boardWidth?: number;
}

export function StudyBoard({ className, boardWidth = 500 }: StudyBoardProps) {
  const { state, addMove, setError, selectNode } = useStudy();

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
    <div className={`study-board-container ${className || ''}`} style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: 'fit-content' }}>
      <div className="study-board-wrapper" style={{ width: boardWidth, height: boardWidth }}>
        <Chessboard
          id="study-board"
          position={state.currentFen}
          onPieceDrop={onPieceDrop}
          boardWidth={boardWidth}
          customDarkSquareStyle={{ backgroundColor: '#779954' }}
          customLightSquareStyle={{ backgroundColor: '#e9edcc' }}
          animationDuration={200}
        />
      </div>
      <div className="study-board-nav" style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
        <button type="button" onClick={moveToStart} style={{ width: '40px' }}>|&lt;</button>
        <button type="button" onClick={moveToPrev} style={{ width: '40px' }}>&lt;</button>
        <button type="button" onClick={moveToNext} style={{ width: '40px' }}>&gt;</button>
        <button type="button" onClick={moveToEnd} style={{ width: '40px' }}>&gt;|</button>
      </div>
      <div
        className="study-board-footer-box"
        style={{
          width: boardWidth,
          height: 200,
          border: '1px solid #000',
        }}
      />
    </div>
  );
}

export default StudyBoard;
