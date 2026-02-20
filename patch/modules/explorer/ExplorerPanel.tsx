import React from 'react';
import './explorer.css';
import { useExplorer } from './useExplorer';
import { FilterBar } from './components/FilterBar';
import { MoveTable } from './components/MoveTable';
import { GameList } from './components/GameList';
import { WinBar } from './components/WinBar';
import { totalGames, formatGames } from './types';

interface ExplorerPanelProps {
  fen: string;
  onMoveSelect: (san: string) => void;
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

export function ExplorerPanel({ fen, onMoveSelect }: ExplorerPanelProps) {
  const { data, loading, error, mastersFilters, setMastersFilters } = useExplorer(fen);

  const total     = data ? totalGames(data) : 0;
  const topGames  = data?.topGames    ?? [];

  return (
    <div className="explorer-panel">
      <div className="explorer-body">
        <FilterBar filters={mastersFilters} onChange={setMastersFilters} />

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

        {!loading && topGames.length > 0 && (
          <GameList games={topGames} label="Top games" />
        )}
      </div>
    </div>
  );
}
