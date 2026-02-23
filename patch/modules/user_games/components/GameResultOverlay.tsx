// ============================================================
// GameResultOverlay — 对局结束覆盖层
// 半透明覆盖棋盘，显示胜负结果 + 操作按钮
// ============================================================

import React from 'react';
import type { GameResult, PlayerColor } from '../types';

// 人性化原因文案
const REASON_LABEL: Record<string, string> = {
  checkmate:              'by checkmate',
  resignation:            'by resignation',
  timeout:                'on time',
  stalemate:              'by stalemate',
  draw_agreement:         'by agreement',
  insufficient_material:  'by insufficient material',
  fifty_moves:            'by 50-move rule',
  threefold_repetition:   'by repetition',
  aborted:                '— game aborted',
};

interface GameResultOverlayProps {
  result: GameResult;
  myColor: PlayerColor | null;
  gameId: string;
  onNewGame: () => void;
}

export function GameResultOverlay({
  result,
  myColor,
  gameId,
  onNewGame,
}: GameResultOverlayProps) {
  // 判断我的结果
  const isWin  = myColor !== null && result.winner === myColor;
  const isLose = myColor !== null && result.winner !== null && result.winner !== myColor;
  const isDraw = result.winner === null;

  const headline = isDraw
    ? 'Draw'
    : isWin
    ? 'You Win!'
    : isLose
    ? 'You Lose'
    : result.result; // 观战者显示原始结果字符串

  const reasonText = REASON_LABEL[result.reason] ?? '';

  const headlineClass = isDraw
    ? 'ug-result__headline--draw'
    : isWin
    ? 'ug-result__headline--win'
    : 'ug-result__headline--lose';

  const handleAnalyze = () => {
    window.location.href = `/chess/${gameId}/analyze`;
  };

  return (
    <div className="ug-result-overlay" role="dialog" aria-modal aria-label="Game result">
      <div className="ug-result-card">
        {/* 结果标题 */}
        <div className={`ug-result__headline ${headlineClass}`}>
          {headline}
        </div>
        {reasonText && (
          <div className="ug-result__reason">{reasonText}</div>
        )}

        {/* 操作按钮 */}
        <div className="ug-result__actions">
          <button
            type="button"
            className="ug-result__btn ug-result__btn--primary"
            onClick={handleAnalyze}
          >
            Analyze
          </button>
          <button
            type="button"
            className="ug-result__btn ug-result__btn--secondary"
            onClick={onNewGame}
          >
            New Game
          </button>
        </div>
      </div>
    </div>
  );
}
