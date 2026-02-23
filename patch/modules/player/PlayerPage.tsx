// ============================================================
// PlayerPage — master player search
//
// Routes:
//   /players          — search / idle
//   /players/:name    — game list for a specific player
//                       (name = encodeURIComponent of DB name)
//
// Navigation uses React Router location.state to carry back-
// navigation context so the search results are restored when
// the user presses ← from a player's game list.
// ============================================================

import React, { useState, useCallback } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import './player.css';
import { PlayerSearchInput } from './components/PlayerSearchInput';
import { PlayerCardGrid } from './components/PlayerCardGrid';
import { FilterBar } from './components/FilterBar';
import { GameList } from './components/GameList';
import { usePlayerGames } from './hooks/usePlayerGames';
import { fetchPlayerSuggestions } from './api';
import { DEFAULT_FILTERS } from './types';
import type { SearchFilters, PlayerSuggestion } from './types';

// ---- Location state shapes ----

interface BackState {
  prevQuery: string;
  prevList: PlayerSuggestion[];
}

// ---- View state machine ----

type ViewState =
  | { kind: 'idle' }
  | { kind: 'players'; query: string; list: PlayerSuggestion[]; loading: boolean }
  | { kind: 'games';   player: string };

// ---- Hero illustration ----

function HeroIllustration() {
  return (
    <svg className="ps-hero-board" viewBox="0 0 120 120" fill="none" aria-hidden>
      {[0,1,2,3,4,5,6,7].map(r =>
        [0,1,2,3,4,5,6,7].map(c => (
          <rect
            key={`${r}-${c}`}
            x={c * 15} y={r * 15} width={15} height={15}
            fill={(r + c) % 2 === 0 ? 'rgba(255,255,255,0.08)' : 'transparent'}
          />
        ))
      )}
      <text x="22" y="48" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.7)">♛</text>
      <text x="52" y="78" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.4)">♞</text>
      <text x="82" y="38" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.6)">♜</text>
      <text x="37" y="103" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.3)">♝</text>
      <text x="97" y="68" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.5)">♚</text>
    </svg>
  );
}

// ---- Games sub-view ----

interface GamesViewProps {
  player: string;
  onBack: () => void;
}

function GamesView({ player, onBack }: GamesViewProps) {
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);
  const { games, loading, error, hasMore, total, loadMore } = usePlayerGames(player, filters);

  return (
    <div className="ps-results-inner">
      <div className="ps-results-header">
        <div className="ps-results-title">
          <button className="ps-back-btn" onClick={onBack} aria-label="Back to players">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <span className="ps-results-player">{player}</span>
          {!loading && games.length > 0 && (
            <span className="ps-results-count">· {total}{hasMore ? '+' : ''} games</span>
          )}
        </div>
        <FilterBar filters={filters} onChange={setFilters} />
      </div>

      {!loading && !error && games.length === 0 && (
        <div className="ps-empty">
          <span className="ps-empty-icon">♟</span>
          <p>No games found</p>
          <p className="ps-empty-hint">Try adjusting the filters</p>
        </div>
      )}

      <GameList
        games={games}
        loading={loading}
        error={error}
        hasMore={hasMore}
        total={total}
        onLoadMore={loadMore}
      />
    </div>
  );
}

// ---- Explore bar (floating CTA when players are selected) ----

interface ExploreBarProps {
  selectedNames: string[];
  onClear: () => void;
  onExplore: () => void;
}

function ExploreBar({ selectedNames, onClear, onExplore }: ExploreBarProps) {
  if (selectedNames.length === 0) return null;

  const label = selectedNames.length === 1
    ? selectedNames[0]
    : `${selectedNames[0]} +${selectedNames.length - 1}`;

  return (
    <div className="ps-explore-bar" role="toolbar" aria-label="Player selection actions">
      <div className="ps-explore-bar__info">
        <span className="ps-explore-bar__icon" aria-hidden>♟</span>
        <span className="ps-explore-bar__label" title={selectedNames.join(', ')}>
          {label}
        </span>
        <button
          type="button"
          className="ps-explore-bar__clear"
          onClick={onClear}
          aria-label="Clear selection"
          title="Clear selection"
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden>
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
      <button
        type="button"
        className="ps-explore-bar__btn"
        onClick={onExplore}
        title="Open opening explorer in Analysis Board"
      >
        Explore openings
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>
  );
}

// ---- Main page ----

const PlayerPage: React.FC = () => {
  const navigate = useNavigate();
  const { name: nameParam } = useParams<{ name?: string }>();
  const location = useLocation();

  // Lazy init: URL param → games view; location.state → restored search results
  const [view, setView] = useState<ViewState>(() => {
    if (nameParam) {
      return { kind: 'games', player: decodeURIComponent(nameParam) };
    }
    const s = location.state as BackState | null;
    if (s?.prevQuery) {
      return { kind: 'players', query: s.prevQuery, list: s.prevList, loading: false };
    }
    return { kind: 'idle' };
  });

  const [selectedNames, setSelectedNames] = useState<string[]>([]);

  // Search button / Enter → fetch player list
  const handleSearch = useCallback(async (query: string) => {
    const q = query.trim();
    if (!q) return;
    setView({ kind: 'players', query: q, list: [], loading: true });
    setSelectedNames([]);
    try {
      const data = await fetchPlayerSuggestions(q, 30);
      setView({ kind: 'players', query: q, list: data.players, loading: false });
    } catch {
      setView({ kind: 'players', query: q, list: [], loading: false });
    }
  }, []);

  // Navigate to a player's game list, carrying search context for back navigation
  const goToPlayer = useCallback((name: string, backState?: BackState) => {
    navigate('/players/' + encodeURIComponent(name), {
      state: backState ?? null,
    });
  }, [navigate]);

  // Autocomplete dropdown pick → go straight to games (no prior search results)
  const handlePickPlayer = useCallback((exactName: string) => {
    goToPlayer(exactName);
  }, [goToPlayer]);

  // Player card body click → go to games, pass current results as back context
  const handleSelectPlayer = useCallback((name: string) => {
    const backState: BackState | undefined =
      view.kind === 'players'
        ? { prevQuery: view.query, prevList: view.list }
        : undefined;
    goToPlayer(name, backState);
  }, [view, goToPlayer]);

  // Back button → restore search results if available, else go to /players
  const handleBack = useCallback(() => {
    const s = location.state as BackState | null;
    if (s?.prevQuery) {
      // Navigate to /players and restore search results via location.state
      navigate('/players', { state: s });
    } else {
      navigate('/players');
    }
  }, [navigate, location.state]);

  // Toggle player name in multi-select (for ExploreBar)
  const handleToggle = useCallback((name: string) => {
    setSelectedNames(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name],
    );
  }, []);

  // Navigate to analysis with selected player names as URL params
  const handleExplore = useCallback(() => {
    if (selectedNames.length === 0) return;
    const params = new URLSearchParams();
    selectedNames.forEach(n => params.append('player', n));
    navigate(`/analysis?${params.toString()}`);
  }, [navigate, selectedNames]);

  return (
    <div className="ps-page">
      {/* Hero */}
      <div className="ps-hero">
        <HeroIllustration />
        <div className="ps-hero-content">
          <p className="ps-hero-eyebrow">Master Database · 4.6 Million Games</p>
          <h1 className="ps-hero-title">Player Game Search</h1>
          <p className="ps-hero-desc">
            Search any master player's complete game history. Filter by year, result, and color.
          </p>
          <PlayerSearchInput
            onSearch={handleSearch}
            onPickPlayer={handlePickPlayer}
          />
        </div>
      </div>

      {/* Results area */}
      {view.kind !== 'idle' && (
        <div className="ps-results">
          {view.kind === 'players' && (
            <div className="ps-results-inner">
              <div className="ps-results-title ps-results-title--query">
                <span>Results for "<strong>{view.query}</strong>"</span>
                <div className="ps-results-title-right">
                  {selectedNames.length > 0 && (
                    <span className="ps-results-selected">
                      {selectedNames.length} selected
                    </span>
                  )}
                  <span className="ps-results-count">{view.list.length} players</span>
                </div>
              </div>
              <PlayerCardGrid
                query={view.query}
                players={view.list}
                loading={view.loading}
                onSelect={handleSelectPlayer}
                selectedNames={selectedNames}
                onToggle={handleToggle}
              />
            </div>
          )}

          {view.kind === 'games' && (
            <GamesView player={view.player} onBack={handleBack} />
          )}
        </div>
      )}

      {/* Floating explore bar — shown when multi-select is active */}
      <ExploreBar
        selectedNames={selectedNames}
        onClear={() => setSelectedNames([])}
        onExplore={handleExplore}
      />
    </div>
  );
};

export default PlayerPage;
