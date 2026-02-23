// ============================================================
// PlayerFilterBadge — 展示当前激活的棋手过滤器，可清除
// ============================================================

import React from 'react';

interface Props {
  players: string[];
  onClear: () => void;
}

export function PlayerFilterBadge({ players, onClear }: Props) {
  const label = players.length === 1
    ? players[0]
    : `${players[0]} +${players.length - 1}`;

  return (
    <div className="explorer-player-filter">
      <span className="explorer-player-filter__icon" aria-hidden>♟</span>
      <span className="explorer-player-filter__label" title={players.join(', ')}>
        {label}
      </span>
      <button
        className="explorer-player-filter__clear"
        onClick={onClear}
        aria-label="Clear player filter"
        title="Clear player filter"
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden>
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}
