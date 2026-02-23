import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  /** Initial player name variants from URL. Empty / undefined = full database. */
  playerFilter?: string[];
  /** Called when all players are cleared — lets the parent sync URL params. */
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
  // Internal player state — initialized from URL prop, then fully owned here
  const [players, setPlayers] = useState<string[]>(playerFilter ?? []);

  // Sync when the URL-provided prop changes (e.g. navigating to /analysis?player=X)
  const propKey = (playerFilter ?? []).join('\0');
  const prevPropKey = useRef(propKey);
  useEffect(() => {
    if (prevPropKey.current !== propKey) {
      prevPropKey.current = propKey;
      setPlayers(playerFilter ?? []);
    }
  });

  // When all players are removed, notify parent so URL params can be cleared
  const onClearRef = useRef(onClearPlayerFilter);
  useEffect(() => { onClearRef.current = onClearPlayerFilter; });

  const addPlayer = useCallback((name: string) => {
    setPlayers(prev => prev.includes(name) ? prev : [...prev, name]);
  }, []);

  const removePlayer = useCallback((name: string) => {
    setPlayers(prev => {
      const next = prev.filter(p => p !== name);
      if (next.length === 0) onClearRef.current?.();
      return next;
    });
  }, []);

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
          onAdd={addPlayer}
          onRemove={removePlayer}
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
