// ============================================================
// PlayerCardGrid — player search result cards
// Supports single-click (→ games view) + checkbox multi-select
// ============================================================

import React from 'react';
import type { PlayerSuggestion } from '../types';

interface Props {
  query: string;
  players: PlayerSuggestion[];
  loading: boolean;
  /** Single-click on main card body → open games for this player */
  onSelect: (name: string) => void;
  /** Multi-select state (names currently checked) */
  selectedNames: string[];
  /** Toggle a player in/out of selection */
  onToggle: (name: string) => void;
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

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export function PlayerCardGrid({ query, players, loading, onSelect, selectedNames, onToggle }: Props) {
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
      {players.map((p, i) => {
        const isSelected = selectedNames.includes(p.name);
        return (
          <div
            key={p.name}
            className={`ps-pcard${isSelected ? ' is-selected' : ''}`}
            style={{ animationDelay: `${Math.min(i, 10) * 40}ms` }}
          >
            {/* Checkbox toggle — stops propagation so main click still works */}
            <button
              type="button"
              className={`ps-pcard__checkbox${isSelected ? ' is-checked' : ''}`}
              onClick={e => { e.stopPropagation(); onToggle(p.name); }}
              aria-pressed={isSelected}
              aria-label={isSelected ? `Deselect ${p.name}` : `Select ${p.name} for multi-player filter`}
              title={isSelected ? 'Remove from selection' : 'Add to selection'}
            >
              {isSelected ? <CheckIcon /> : null}
            </button>

            {/* Main body — click opens games */}
            <button
              type="button"
              className="ps-pcard__main"
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
          </div>
        );
      })}
    </div>
  );
}
