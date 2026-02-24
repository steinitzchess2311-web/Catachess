import React from 'react';
import './explorer.css';
import { useExplorer } from './useExplorer';
import { FilterBar } from './components/FilterBar';
import { MoveTable } from './components/MoveTable';
import { WinBar } from './components/WinBar';
import { PositionGameList } from './components/PositionGameList';
import { PlayerFilterRow } from './components/PlayerFilterRow';
import { totalGames, formatGames } from './types';

interface ExplorerPanelProps {
  fen: string;
  onMoveSelect: (san: string) => void;
  /** Controlled player list — owned by parent (AnalysisPage via useExplorerPlayers) */
  players: string[];
  onAddPlayer: (name: string) => void;
  onRemovePlayer: (name: string) => void;
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

export function ExplorerPanel({ fen, onMoveSelect, players, onAddPlayer, onRemovePlayer }: ExplorerPanelProps) {

  const { data, loading, error, mastersFilters, setMastersFilters } = useExplorer(fen, players);
  const total = data ? totalGames(data) : 0;

  return (
    <div className="explorer-panel">
      <div className="explorer-body">
        <FilterBar
          filters={mastersFilters}
          onChange={setMastersFilters}
          playerFilterActive={players.length > 0}
        />

        <PlayerFilterRow
          players={players}
          onAdd={onAddPlayer}
          onRemove={onRemovePlayer}
        />

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
