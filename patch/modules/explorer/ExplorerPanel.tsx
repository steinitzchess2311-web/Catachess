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
  /** Player name variants to filter by. Empty / undefined = full database. */
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
  const hasPlayerFilter = (playerFilter?.length ?? 0) > 0;
  const players = hasPlayerFilter ? playerFilter! : [];

  // /masters — move stats scoped to players (or full DB when players=[])
  // Parallel with /masters/stats below when player filter is active.
  const { data, loading, error, mastersFilters, setMastersFilters } = useExplorer(fen, players);

  const total = data ? totalGames(data) : 0;

  // ---- /masters/stats — player-perspective Win Bar (parallel request) ----
  const [playerStats, setPlayerStats] = useState<PlayerStatsResponse | null>(null);
  const statsKeyRef = useRef('');

  useEffect(() => {
    if (!hasPlayerFilter || !fen) {
      setPlayerStats(null);
      return;
    }

    const key = `${fen}::${players.join(',')}`;
    statsKeyRef.current = key;
    setPlayerStats(null);

    const controller = new AbortController();
    fetchMastersStats(fen, players, controller.signal)
      .then(s => { if (statsKeyRef.current === key) setPlayerStats(s); })
      .catch(() => {});

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fen, players.join(','), hasPlayerFilter]);

  // ---- Derived display values ----
  // When player filter is active: count comes from /masters/stats (player-scoped)
  // When no filter: count comes from /masters aggregate
  const displayTotal = hasPlayerFilter && playerStats ? playerStats.total : total;

  return (
    <div className="explorer-panel">
      <div className="explorer-body">
        <FilterBar
          filters={mastersFilters}
          onChange={setMastersFilters}
          playerFilterActive={hasPlayerFilter}
        />

        {/* Active player filter badge */}
        {hasPlayerFilter && onClearPlayerFilter && (
          <PlayerFilterBadge players={players} onClear={onClearPlayerFilter} />
        )}

        {loading && <LoadingDots />}

        {error && <div className="explorer-error">{error}</div>}

        {/* Win Bar + total count */}
        {!loading && data && (total > 0 || (hasPlayerFilter && playerStats != null)) && (
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

        {/* Move table — always player-scoped when filter active */}
        {!loading && data && (
          <MoveTable moves={data.moves} onMoveClick={onMoveSelect} />
        )}

        {/* Game list — /masters/games, infinite scroll + sort */}
        <PositionGameList fen={fen} players={players} />
      </div>
    </div>
  );
}
