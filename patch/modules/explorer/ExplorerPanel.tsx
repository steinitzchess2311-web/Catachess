import React from 'react';
import './explorer.css';
import { useExplorer } from './useExplorer';
import { FilterBar } from './components/FilterBar';
import { MoveTable } from './components/MoveTable';
import { GameList } from './components/GameList';
import { WinBar } from './components/WinBar';
import { totalGames, formatGames } from './types';
import type { ExplorerTab } from './types';

interface ExplorerPanelProps {
  fen: string;
  onMoveSelect: (san: string) => void;
}

const TAB_LABELS: Record<ExplorerTab, string> = {
  masters: 'Masters',
  lichess: 'Lichess',
  player: 'Player',
};

const TABS: ExplorerTab[] = ['masters', 'lichess', 'player'];

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
  const {
    data, loading, error,
    queuePosition, playerStatus,
    tab, setTab,
    mastersFilters, setMastersFilters,
    lichessFilters, setLichessFilters,
    playerFilters,  setPlayerFilters,
    triggerPlayerFetch,
  } = useExplorer(fen);

  const total = data ? totalGames(data) : 0;
  const topGames    = data?.topGames    ?? [];
  const recentGames = data?.recentGames ?? [];

  return (
    <div className="explorer-panel">
      {/* Masters / Lichess / Player tabs */}
      <div className="patch-sidebar-tabs">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            className={`patch-sidebar-tab${tab === t ? ' is-active' : ''}`}
            onClick={() => setTab(t)}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <div className="explorer-body">
        <FilterBar
          tab={tab}
          mastersFilters={mastersFilters}
          setMastersFilters={setMastersFilters}
          lichessFilters={lichessFilters}
          setLichessFilters={setLichessFilters}
          playerFilters={playerFilters}
          setPlayerFilters={setPlayerFilters}
          onPlayerSearch={triggerPlayerFetch}
        />

        {loading && <LoadingDots />}

        {tab === 'player' && playerStatus === 'indexing' && !loading && (
          <div className="explorer-queue-msg">
            {queuePosition != null && queuePosition > 0
              ? `Queued — position ${queuePosition}`
              : 'Indexing player games…'}
          </div>
        )}

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

        {!loading && recentGames.length > 0 && (
          <GameList games={recentGames} label="Recent games" />
        )}

        {tab === 'player' && playerStatus === 'idle' && !loading && !data && (
          <div className="explorer-empty">
            Enter a Lichess username<br />and press Search.
          </div>
        )}
      </div>
    </div>
  );
}
