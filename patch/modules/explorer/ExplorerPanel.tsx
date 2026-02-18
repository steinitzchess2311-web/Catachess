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
  /** Current board FEN — re-queries automatically on each change. */
  fen: string;
  /** Called with a SAN move when user clicks a row in the move table. */
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
    data,
    loading,
    queuePosition,
    playerStatus,
    error,
    tab,
    setTab,
    mastersFilters,
    setMastersFilters,
    lichessFilters,
    setLichessFilters,
    playerFilters,
    setPlayerFilters,
    triggerPlayerFetch,
  } = useExplorer(fen);

  const total = data ? totalGames(data) : 0;

  return (
    <div className="explorer-panel">
      {/* DB tab bar — reuses the existing pill tab CSS */}
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

      {/* Scrollable body */}
      <div className="explorer-body">
        {/* Filters */}
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

        {/* Loading state */}
        {loading && <LoadingDots />}

        {/* Player-specific status */}
        {tab === 'player' && playerStatus === 'indexing' && !loading && (
          <div className="explorer-queue-msg">
            {queuePosition != null && queuePosition > 0
              ? `Queued — position ${queuePosition}`
              : 'Indexing player games…'}
          </div>
        )}

        {/* Error */}
        {error && <div className="explorer-error">{error}</div>}

        {/* Summary win bar */}
        {!loading && data && total > 0 && (
          <div className="explorer-summary">
            <WinBar white={data.white} draws={data.draws} black={data.black} />
            <span className="explorer-summary__count">{formatGames(total)}</span>
          </div>
        )}

        {/* Move table */}
        {!loading && data && (
          <MoveTable moves={data.moves} onMoveClick={onMoveSelect} />
        )}

        {/* Game lists */}
        {!loading && data && (
          <>
            {data.topGames.length > 0 && (
              <GameList games={data.topGames} label="Top games" />
            )}
            {data.recentGames.length > 0 && (
              <GameList games={data.recentGames} label="Recent games" />
            )}
          </>
        )}

        {/* Player idle state */}
        {tab === 'player' && playerStatus === 'idle' && !loading && !data && (
          <div className="explorer-empty">
            Enter a Lichess username<br />and press Search.
          </div>
        )}
      </div>
    </div>
  );
}
