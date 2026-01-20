import React, { useCallback } from 'react';
import { Chessboard } from 'react-chessboard';
import { useStudy } from '../studyContext';
import { getMoveSan } from '../chessJS/replay';

export interface StudyBoardProps {
  className?: string;
  boardWidth?: number;
}

export function StudyBoard({ className, boardWidth = 400 }: StudyBoardProps) {
  const { state, addMove, setError } = useStudy();

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
      
      {/* Analysis Placeholder */}
      <div className="study-board-controls">
        <button 
          className="analysis-button"
          onClick={() => console.log('Analysis clicked (placeholder)')}
          style={{
            padding: '8px 16px',
            backgroundColor: '#4a4a4a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'not-allowed', // Disabled for now
            opacity: 0.7
          }}
          disabled
        >
          Analyze (Coming Soon)
        </button>
      </div>
    </div>
  );
}

export default StudyBoard;
