// ============================================================
// LiveBoard — 实时对局棋盘
//
// 职责：
//   - 只管棋盘渲染和走棋输入
//   - 轮到自己时可拖拽/点击走棋，否则锁定
//   - 升变使用 react-chessboard 内置 UI
//   - 支持翻转棋盘
// ============================================================

import React, { useCallback, useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { useBoardSize } from '@patch/board/useBoardSize';
import type { PlayerColor } from '../types';

interface LiveBoardProps {
  fen: string;
  myColor: PlayerColor | null;     // null = 观战
  turn: PlayerColor;               // 当前轮到哪方走棋
  isOver: boolean;
  onMove: (from: string, to: string, promotion?: string) => void;
}

export function LiveBoard({ fen, myColor, turn, isOver, onMove }: LiveBoardProps) {
  const [sizeRef, boardWidth] = useBoardSize(500);
  // 默认方向：我的颜色朝下，观战者看白方
  const [orientation, setOrientation] = useState<'white' | 'black'>(
    myColor === 'black' ? 'black' : 'white',
  );

  // 是否轮到我走棋
  const isMyTurn = !isOver && myColor !== null && turn === myColor;

  const handlePieceDrop = useCallback(
    (source: string, target: string, _piece: string): boolean => {
      if (!isMyTurn) return false;
      onMove(source, target);
      return true; // react-chessboard 需要返回 true 才显示动画
    },
    [isMyTurn, onMove],
  );

  // 升变选择回调（react-chessboard 内置弹窗）
  const handlePromotion = useCallback(
    (piece?: string, from?: string, to?: string): boolean => {
      if (!from || !to || !piece || !isMyTurn) return false;
      // piece 格式：'wQ' | 'bQ' | ...，取第二个字符小写
      const promotion = piece[1]?.toLowerCase();
      if (promotion) onMove(from, to, promotion);
      return true;
    },
    [isMyTurn, onMove],
  );

  const toggleFlip = () =>
    setOrientation((o) => (o === 'white' ? 'black' : 'white'));

  return (
    <div
      ref={sizeRef}
      className="ug-board-wrapper"
      style={{ width: '100%', height: '100%' }}
    >
      <Chessboard
        id="live-board"
        position={fen}
        boardOrientation={orientation}
        boardWidth={boardWidth}
        onPieceDrop={handlePieceDrop}
        onPromotionPieceSelect={handlePromotion}
        isDraggablePiece={isMyTurn ? undefined : () => false}
        // 标准棋盘颜色，与 studyBoard 统一
        customDarkSquareStyle={{ backgroundColor: '#779954' }}
        customLightSquareStyle={{ backgroundColor: '#e9edcc' }}
        animationDuration={120}
        // 允许内置升变弹窗
        promotionToSquare={null}
      />

      {/* 翻转按钮 */}
      <button
        type="button"
        className="ug-board-flip-btn"
        onClick={toggleFlip}
        title="Flip board (F)"
        aria-label="Flip board"
      >
        Flip
      </button>
    </div>
  );
}
