// ============================================================
// PlayerCardGrid — 棋手搜索结果卡片列表
// ============================================================

import React from 'react';
import type { PlayerSuggestion } from '../types';

interface Props {
  query: string;
  players: PlayerSuggestion[];
  loading: boolean;
  onSelect: (name: string) => void;
}

function formatGames(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}

function SkeletonPlayerCard() {
  return (
    <div className="ps-pcard ps-pcard--skeleton" aria-hidden>
      <div className="ps-pcard__icon" />
      <div className="ps-pcard__body">
        <div className="ps-skel ps-skel--pname" />
        <div className="ps-skel ps-skel--pgames" />
      </div>
    </div>
  );
}

export function PlayerCardGrid({ query, players, loading, onSelect }: Props) {
  if (loading) {
    return (
      <div className="ps-pgrid">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonPlayerCard key={i} />
        ))}
      </div>
    );
  }

  if (players.length === 0) {
    return (
      <div className="ps-empty">
        <span className="ps-empty-icon">♟</span>
        <p>No players found for "{query}"</p>
        <p className="ps-empty-hint">Try a different spelling or last name only</p>
      </div>
    );
  }

  return (
    <div className="ps-pgrid">
      {players.map((p, i) => (
        <button
          key={p.name}
          className="ps-pcard"
          style={{ animationDelay: `${Math.min(i, 10) * 40}ms` }}
          onClick={() => onSelect(p.name)}
        >
          <div className="ps-pcard__icon" aria-hidden>♟</div>
          <div className="ps-pcard__body">
            <span className="ps-pcard__name">{p.name}</span>
            <span className="ps-pcard__games">{formatGames(p.games)} games</span>
          </div>
          <svg className="ps-pcard__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      ))}
    </div>
  );
}
