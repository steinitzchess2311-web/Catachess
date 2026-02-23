// ============================================================
// GameCard — 单局对局卡片
// ============================================================

import React from 'react';
import type { GameListItem } from '../types';

interface Props {
  game: GameListItem;
  /** 入场动画延迟，ms */
  delay?: number;
}

const RESULT_LABEL: Record<GameListItem['result'], string> = {
  white: '1 — 0',
  black: '0 — 1',
  draw:  '½ — ½',
};

export function GameCard({ game, delay = 0 }: Props) {
  const resultClass =
    game.result === 'white' ? 'ps-card--white-wins'
    : game.result === 'black' ? 'ps-card--black-wins'
    : 'ps-card--draw';

  return (
    <div
      className={`ps-card ${resultClass}`}
      style={{ animationDelay: `${delay}ms` }}
      role="button"
      tabIndex={0}
      onClick={() => window.open(`/game/${game.id}`, '_blank', 'noopener')}
      onKeyDown={(e) => e.key === 'Enter' && window.open(`/game/${game.id}`, '_blank', 'noopener')}
    >
      {/* 左侧彩色条 */}
      <div className="ps-card__accent" aria-hidden />

      {/* 棋手信息 */}
      <div className="ps-card__players">
        <div className="ps-card__player">
          <span className="ps-card__piece ps-card__piece--white">♔</span>
          <span className="ps-card__name">{game.white}</span>
          <span className="ps-card__elo">{game.white_elo ?? '—'}</span>
        </div>
        <div className="ps-card__player">
          <span className="ps-card__piece ps-card__piece--black">♚</span>
          <span className="ps-card__name">{game.black}</span>
          <span className="ps-card__elo">{game.black_elo ?? '—'}</span>
        </div>
      </div>

      {/* 结果 */}
      <div className="ps-card__result">
        {RESULT_LABEL[game.result]}
      </div>

      {/* 元信息 */}
      <div className="ps-card__meta">
        {game.year && <span className="ps-card__year">{game.year}</span>}
        {game.event && <span className="ps-card__event">{game.event}</span>}
      </div>
    </div>
  );
}
