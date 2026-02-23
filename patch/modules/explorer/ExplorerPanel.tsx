import React, { useEffect, useRef, useState } from 'react';
import './explorer.css';
import { useExplorer } from './useExplorer';
import { FilterBar } from './components/FilterBar';
import { MoveTable } from './components/MoveTable';
import { WinBar } from './components/WinBar';
import { PositionGameList } from './components/PositionGameList';
import { PlayerFilterBadge } from './components/PlayerFilterBadge';
import { fetchMastersStats } from './api';
import type { PlayerStatsResponse } from './api';
import { totalGames, formatGames } from './types';

interface ExplorerPanelProps {
  fen: string;
  onMoveSelect: (san: string) => void;
  /** When set, the game list and win bar are filtered to these player name variants */
  playerFilter?: string[];
  onClearPlayerFilter?: () => void;
}

function LoadingDots() {
  return (
    <div className="explorer-loading">
      <div className="explorer-loading__dot" />
      <div className="explorer-loading__dot" />
      <div className="explorer-loading__dot" />
    </div>
  );
}

export function ExplorerPanel({ fen, onMoveSelect, playerFilter, onClearPlayerFilter }: ExplorerPanelProps) {
  const { data, loading, error, mastersFilters, setMastersFilters } = useExplorer(fen);

  const total = data ? totalGames(data) : 0;
  const hasPlayerFilter = (playerFilter?.length ?? 0) > 0;

  // ---- Player stats (parallel request to /masters/stats) ----
  const [playerStats, setPlayerStats] = useState<PlayerStatsResponse | null>(null);
  const statsKeyRef = useRef('');

  useEffect(() => {
    if (!hasPlayerFilter || !playerFilter || !fen) {
      setPlayerStats(null);
      return;
    }

    const key = `${fen}::${playerFilter.join(',')}`;
    statsKeyRef.current = key;
    setPlayerStats(null);

    const controller = new AbortController();
    fetchMastersStats(fen, playerFilter, controller.signal)
      .then(s => { if (statsKeyRef.current === key) setPlayerStats(s); })
      .catch(() => {});

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fen, playerFilter?.join(','), hasPlayerFilter]);

  // ---- Derived display values ----
  const displayTotal = hasPlayerFilter && playerStats
    ? playerStats.total
    : total;

  return (
    <div className="explorer-panel">
      <div className="explorer-body">
        <FilterBar filters={mastersFilters} onChange={setMastersFilters} />

        {/* Active player filter badge */}
        {hasPlayerFilter && playerFilter && onClearPlayerFilter && (
          <PlayerFilterBadge players={playerFilter} onClear={onClearPlayerFilter} />
        )}

        {loading && <LoadingDots />}

        {error && <div className="explorer-error">{error}</div>}

        {!loading && data && (total > 0 || (hasPlayerFilter && playerStats)) && (
          <div className="explorer-summary">
            <WinBar
              white={data.white}
              draws={data.draws}
              black={data.black}
              playerStats={playerStats ?? undefined}
            />
            {displayTotal > 0 && (
              <span className="explorer-summary__count">{formatGames(displayTotal)}</span>
            )}
          </div>
        )}

        {!loading && data && (
          <MoveTable moves={data.moves} onMoveClick={onMoveSelect} />
        )}

        {/* Game list: always /masters/games (infinite scroll + sort) */}
        <PositionGameList fen={fen} players={playerFilter ?? []} />
      </div>
    </div>
  );
}
