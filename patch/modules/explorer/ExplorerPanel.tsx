import React from 'react';
import './explorer.css';
import { useExplorer } from './useExplorer';
import { FilterBar } from './components/FilterBar';
import { MoveTable } from './components/MoveTable';
import { WinBar } from './components/WinBar';
import { PositionGameList } from './components/PositionGameList';
import { PlayerFilterBadge } from './components/PlayerFilterBadge';
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

  // /masters — move stats + win counts, scoped to players or full DB
  const { data, loading, error, mastersFilters, setMastersFilters } = useExplorer(fen, players);

  const total = data ? totalGames(data) : 0;

  return (
    <div className="explorer-panel">
      <div className="explorer-body">
        <FilterBar
          filters={mastersFilters}
          onChange={setMastersFilters}
          playerFilterActive={hasPlayerFilter}
        />

        {hasPlayerFilter && onClearPlayerFilter && (
          <PlayerFilterBadge players={players} onClear={onClearPlayerFilter} />
        )}

        {loading && <LoadingDots />}

        {error && <div className="explorer-error">{error}</div>}

        {!loading && data && total > 0 && (
          <div className="explorer-summary">
            <WinBar white={data.white} draws={data.draws} black={data.black} />
            <span className="explorer-summary__count">{formatGames(total)}</span>
          </div>
        )}

        {!loading && data && (
          <MoveTable moves={data.moves} onMoveClick={onMoveSelect} />
        )}

        <PositionGameList fen={fen} players={players} />
      </div>
    </div>
  );
}
