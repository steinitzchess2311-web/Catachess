// ============================================================
// PositionGameList — explorer game list filtered by player[]
// Uses useMastersGames with cursor-pagination + IntersectionObserver
// ============================================================

import React, { useRef, useEffect, useState } from 'react';
import { useMastersGames } from '../hooks/useMastersGames';
import type { PlayerColorFilter, SortOrder } from '../types';

interface Props {
  fen: string;
  players: string[];
  playerColor: PlayerColorFilter;
}

const SORT_OPTIONS: { label: string; value: SortOrder }[] = [
  { label: 'Elo ↓', value: 'elo_desc' },
  { label: 'Newest', value: 'year_desc' },
  { label: 'Oldest', value: 'year_asc' },
];

function LoadingDots() {
  return (
    <div className="explorer-loading">
      <div className="explorer-loading__dot" />
      <div className="explorer-loading__dot" />
      <div className="explorer-loading__dot" />
    </div>
  );
}

export function PositionGameList({ fen, players, playerColor }: Props) {
  const [sort, setSort] = useState<SortOrder>('elo_desc');
  const { games, loading, error, hasMore, loadMore, total } = useMastersGames(fen, players, playerColor, sort);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  // Infinite scroll: use the list container as root so it works inside any scroll parent
  useEffect(() => {
    const el = sentinelRef.current;
    const root = listRef.current;
    if (!el || !root) return;
    const io = new IntersectionObserver(
      entries => { if (entries[0].isIntersecting) loadMore(); },
      { root, rootMargin: '200px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [loadMore]);

  return (
    <div className="explorer-games" ref={listRef} style={{ overflowY: 'auto', flex: 1, minHeight: 0 }}>
      {/* Sort bar */}
      <div className="explorer-pgames-header">
        <div className="explorer-pgames-sort">
          {SORT_OPTIONS.map(o => (
            <button
              key={o.value}
              type="button"
              className={`explorer-chip${sort === o.value ? ' is-active' : ''}`}
              onClick={() => setSort(o.value)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="explorer-error">{error}</div>}

      {!loading && !error && games.length === 0 && (
        <div className="explorer-empty">No games found for this position</div>
      )}

      {games.map((g, i) => {
        const accentClass =
          g.result === 'white' ? 'explorer-game--white-wins'
          : g.result === 'black' ? 'explorer-game--black-wins'
          : 'explorer-game--draw';

        const resultText =
          g.result === 'white' ? '1–0'
          : g.result === 'black' ? '0–1'
          : '½–½';

        return (
          <div
            key={g.id}
            className={`explorer-game ${accentClass}`}
            style={{ animationDelay: `${Math.min(i, 10) * 35}ms`, cursor: 'pointer' }}
            role="button"
            tabIndex={0}
            title="Open game"
            onClick={() => window.open(`/game/${g.id}`, '_blank', 'noopener')}
            onKeyDown={e => e.key === 'Enter' && window.open(`/game/${g.id}`, '_blank', 'noopener')}
          >
            <div className="explorer-game__body">
              <div className="explorer-game__row">
                <span className="explorer-game__piece explorer-game__piece--white">♔</span>
                <span className="explorer-game__name">{g.white}</span>
                {g.white_elo != null && (
                  <span className="explorer-game__elo">{g.white_elo}</span>
                )}
              </div>
              <div className="explorer-game__row">
                <span className="explorer-game__piece explorer-game__piece--black">♚</span>
                <span className="explorer-game__name">{g.black}</span>
                {g.black_elo != null && (
                  <span className="explorer-game__elo">{g.black_elo}</span>
                )}
              </div>
            </div>
            <div className="explorer-game__aside">
              <span className="explorer-game__result">{resultText}</span>
              {g.year != null && <span className="explorer-game__date">{g.year}</span>}
            </div>
          </div>
        );
      })}

      {/* Invisible sentinel — triggers loadMore via IntersectionObserver */}
      {hasMore && <div ref={sentinelRef} className="explorer-pgames-sentinel" />}

      {loading && <LoadingDots />}

      {!loading && !hasMore && games.length > 0 && (
        <div className="explorer-pgames-end">{total} games</div>
      )}
    </div>
  );
}
