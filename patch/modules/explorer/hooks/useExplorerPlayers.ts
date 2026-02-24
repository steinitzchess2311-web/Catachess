/**
 * useExplorerPlayers
 *
 * Single source of truth for the Explorer player filter.
 * Persistence strategy:
 *   - URL params (?player=A&player=B)  → cross-device, shareable links
 *   - localStorage (explorer_players)  → same-browser session (survives tab switches)
 *
 * Priority on init: URL > localStorage > empty
 * On every change: writes to both URL and localStorage.
 */

import { useCallback, useRef } from 'react';

const LS_KEY = 'explorer_players';

// ── localStorage helpers ──────────────────────────────────────────────────────

export function loadPlayersFromStorage(): string[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((p): p is string => typeof p === 'string') : [];
  } catch {
    return [];
  }
}

function savePlayersToStorage(players: string[]): void {
  try {
    if (players.length === 0) {
      localStorage.removeItem(LS_KEY);
    } else {
      localStorage.setItem(LS_KEY, JSON.stringify(players));
    }
  } catch {
    // storage unavailable — ignore
  }
}

// ── Hook ──────────────────────────────────────────────────────────────────────

interface UseExplorerPlayersOptions {
  /** Current players from URL (searchParams.getAll('player')) */
  players: string[];
  /** Callback to write players back to URL */
  onUrlChange: (players: string[]) => void;
}

interface UseExplorerPlayersResult {
  addPlayer: (name: string) => void;
  removePlayer: (name: string) => void;
}

export function useExplorerPlayers({
  players,
  onUrlChange,
}: UseExplorerPlayersOptions): UseExplorerPlayersResult {
  // Keep onUrlChange stable via ref so callbacks don't recreate on every render
  const onUrlChangeRef = useRef(onUrlChange);
  onUrlChangeRef.current = onUrlChange;

  const addPlayer = useCallback((name: string) => {
    if (players.includes(name)) return;
    const next = [...players, name];
    savePlayersToStorage(next);
    onUrlChangeRef.current(next);
  }, [players]);

  const removePlayer = useCallback((name: string) => {
    const next = players.filter(p => p !== name);
    savePlayersToStorage(next);
    onUrlChangeRef.current(next);
  }, [players]);

  return { addPlayer, removePlayer };
}
