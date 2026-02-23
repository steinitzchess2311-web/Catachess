// ============================================================
// GameControls — 对局操作按钮（认输 / 提和 / 中止）
// 根据对局阶段和走棋步数决定显示哪些按钮
// ============================================================

import React, { useState } from 'react';

interface GameControlsProps {
  phase: 'connecting' | 'waiting' | 'ongoing' | 'over' | 'disconnected';
  moveCount: number;          // 总步数，用于判断是否可以中止（< 2 步可中止）
  hasOutgoingDraw: boolean;   // 已发出提和请求
  onResign: () => void;
  onOfferDraw: () => void;
  onAbort: () => void;
}

export function GameControls({
  phase,
  moveCount,
  hasOutgoingDraw,
  onResign,
  onOfferDraw,
  onAbort,
}: GameControlsProps) {
  const [confirmResign, setConfirmResign] = useState(false);

  if (phase !== 'ongoing' && phase !== 'waiting') return null;

  // 双方都没走棋前（waiting 或 ongoing 步数 < 2），允许中止而不是认输
  const canAbort = moveCount < 2;

  const handleResignClick = () => {
    if (confirmResign) {
      onResign();
      setConfirmResign(false);
    } else {
      setConfirmResign(true);
      // 3 秒后自动取消确认
      setTimeout(() => setConfirmResign(false), 3000);
    }
  };

  return (
    <div className="ug-controls">
      {canAbort ? (
        <button
          type="button"
          className="ug-controls__btn ug-controls__btn--abort"
          onClick={onAbort}
        >
          Abort
        </button>
      ) : (
        <>
          {/* 提和按钮 */}
          <button
            type="button"
            className={[
              'ug-controls__btn',
              'ug-controls__btn--draw',
              hasOutgoingDraw ? 'ug-controls__btn--disabled' : '',
            ].join(' ')}
            onClick={onOfferDraw}
            disabled={hasOutgoingDraw}
            title={hasOutgoingDraw ? 'Draw offer sent' : 'Offer a draw'}
          >
            {hasOutgoingDraw ? 'Draw offered' : '½ Draw'}
          </button>

          {/* 认输按钮，点一次弹确认 */}
          <button
            type="button"
            className={[
              'ug-controls__btn',
              confirmResign
                ? 'ug-controls__btn--resign-confirm'
                : 'ug-controls__btn--resign',
            ].join(' ')}
            onClick={handleResignClick}
          >
            {confirmResign ? 'Confirm resign?' : 'Resign'}
          </button>
        </>
      )}
    </div>
  );
}
