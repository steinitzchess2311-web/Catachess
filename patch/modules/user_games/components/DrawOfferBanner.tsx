// ============================================================
// DrawOfferBanner — 提和通知条
// 出现在棋盘上方，不覆盖主界面
// ============================================================

import React from 'react';

interface DrawOfferBannerProps {
  /** 是否有对手发来的提和请求 */
  incoming: boolean;
  /** 是否是我们发出的（等待对手）*/
  outgoing: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export function DrawOfferBanner({
  incoming,
  outgoing,
  onAccept,
  onDecline,
}: DrawOfferBannerProps) {
  if (!incoming && !outgoing) return null;

  return (
    <div className="ug-draw-banner">
      {incoming ? (
        <>
          <span className="ug-draw-banner__text">
            Opponent offers a draw
          </span>
          <div className="ug-draw-banner__actions">
            <button
              type="button"
              className="ug-draw-banner__btn ug-draw-banner__btn--accept"
              onClick={onAccept}
            >
              Accept
            </button>
            <button
              type="button"
              className="ug-draw-banner__btn ug-draw-banner__btn--decline"
              onClick={onDecline}
            >
              Decline
            </button>
          </div>
        </>
      ) : (
        <span className="ug-draw-banner__text ug-draw-banner__text--waiting">
          Draw offer sent — waiting for opponent...
        </span>
      )}
    </div>
  );
}
