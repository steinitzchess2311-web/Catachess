import React, { useEffect, useRef, useState } from 'react';
import { useStudy } from '../studyContext';
import { uciLineToSan } from '../chessJS/uci';
import { getFullmoveNumber, getTurn } from '../chessJS/fen';
import { analyzeWithFallback } from '../engine/client';
import type { EngineLine, EngineSource } from '../engine/types';
import { ChapterList } from './ChapterList';

export interface StudySidebarProps {
  chapters: Array<{ id: string; title?: string; order?: number }>;
  currentChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
}

const FALLBACK_BACKOFF_MS = 10000;

function formatScore(raw: number | string): string {
  if (typeof raw === 'string') {
    if (raw.startsWith('mate')) {
      const mate = raw.slice(4);
      return `M${mate}`;
    }
    return raw;
  }
  const value = raw / 100;
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
}

function formatSanWithMoveNumbers(sanMoves: string[], fen: string): string {
  if (sanMoves.length === 0) return '';
  const turn = getTurn(fen) || 'w';
  let moveNumber = getFullmoveNumber(fen) || 1;
  const parts: string[] = [];
  let isWhite = turn === 'w';
  for (const san of sanMoves) {
    if (isWhite) {
      parts.push(`${moveNumber}. ${san}`);
    } else {
      parts.push(`${moveNumber}... ${san}`);
      moveNumber += 1;
    }
    isWhite = !isWhite;
  }
  return parts.join(' ');
}

export function StudySidebar({
  chapters,
  currentChapterId,
  onSelectChapter,
  onCreateChapter,
}: StudySidebarProps) {
  const { state } = useStudy();
  const [activeTab, setActiveTab] = useState<'chapters' | 'analysis' | 'imitator'>('chapters');
  const [depth, setDepth] = useState(14);
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);
  const [engineMode, setEngineMode] = useState<'cloud' | 'sf'>('sf');
  const [cloudBlocked, setCloudBlocked] = useState(false);
  const [engineNotice, setEngineNotice] = useState<string | null>(null);
  const [lines, setLines] = useState<EngineLine[]>([]);
  const [status, setStatus] = useState<'idle' | 'running' | 'ready' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [health, setHealth] = useState<'unknown' | 'ok' | 'down'>('unknown');
  const [source, setSource] = useState<EngineSource | null>(null);
  const [coachOptions, setCoachOptions] = useState<string[]>([]);
  const [playerOptions, setPlayerOptions] = useState<Array<{ id: string; name: string }>>([]);
  const [coachStatus, setCoachStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [playerStatus, setPlayerStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [coachError, setCoachError] = useState<string | null>(null);
  const [playerError, setPlayerError] = useState<string | null>(null);
  const [selectedCoach, setSelectedCoach] = useState<string>('');
  const [selectedPlayer, setSelectedPlayer] = useState<string>('');
  const [imitatorTargets, setImitatorTargets] = useState<
    Array<{
      id: string;
      label: string;
      source: 'library' | 'user';
      player?: string;
      playerId?: string;
      kind: 'coach' | 'player';
    }>
  >([]);
  const [imitatorResults, setImitatorResults] = useState<
    Record<
      string,
      {
        status: 'idle' | 'running' | 'ready' | 'error';
        moves: Array<{
          move: string;
          uci?: string;
          score_cp?: number | null;
          tags?: string[];
          probability?: number;
        }>;
        updated?: number;
        error?: string | null;
      }
    >
  >({});
  const inFlightRef = useRef(false);
  const pollRef = useRef<number | null>(null);
  const nextAllowedRef = useRef<number>(0);
  const cacheRef = useRef<
    Map<string, { lines: EngineLine[]; source: EngineSource; updated: number }>
  >(new Map());
  const imitatorRequestRef = useRef(0);

  const resolveTaggerBase = () => {
    try {
      const env = (import.meta as any)?.env;
      const base = env?.VITE_TAGGER_BLACKBOX_URL || env?.VITE_TAGGER_BASE;
      if (base) return base as string;
    } catch {
      // ignore
    }
    return 'https://tagger.catachess.com';
  };

  const TAGGER_BASE = resolveTaggerBase();
  const getCacheKey = (fen: string) => `${engineMode}:${depth}:${multipv}:${fen}`;

  const formatProbability = (value?: number) => {
    if (value === undefined || value === null || Number.isNaN(value)) return '—';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatTags = (tags?: string[]) => {
    if (!tags || tags.length === 0) return '—';
    return tags.join(', ');
  };

  const analyzePosition = async (fen: string) => {
    if (!fen || inFlightRef.current) return;
    if (engineMode === 'cloud' && cloudBlocked) return;
    const now = Date.now();
    if (now < nextAllowedRef.current) return;
    const cacheKey = getCacheKey(fen);
    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setLines(cached.lines);
      setSource(cached.source);
      setStatus('ready');
      setLastUpdated(cached.updated);
      setHealth('ok');
      return;
    }
    inFlightRef.current = true;
    setStatus('running');
    setError(null);
    try {
      const result = await analyzeWithFallback(fen, depth, multipv, engineMode);
      setLines(result.lines);
      setSource(result.source);
      setStatus('ready');
      const updated = Date.now();
      setLastUpdated(updated);
      setHealth('ok');
      cacheRef.current.set(cacheKey, {
        lines: result.lines,
        source: result.source,
        updated,
      });
    } catch (e: any) {
      if (e?.message?.includes('429')) {
        nextAllowedRef.current = Date.now() + FALLBACK_BACKOFF_MS;
      }
      if (engineMode === 'cloud') {
        setCloudBlocked(true);
        setEngineNotice('Cloud Eval unavailable. Please select SFCata engine.');
        setStatus('error');
        setError(e?.message || 'Engine request failed');
        setHealth('down');
      } else {
        setStatus('error');
        setError(e?.message || 'Engine request failed');
        setHealth('down');
      }
    } finally {
      inFlightRef.current = false;
    }
  };

  useEffect(() => {
    if (activeTab !== 'analysis' || !engineEnabled) return;

    analyzePosition(state.currentFen);
    if (pollRef.current) window.clearInterval(pollRef.current);
    if (engineMode === 'sf') {
      pollRef.current = window.setInterval(() => {
        analyzePosition(state.currentFen);
      }, 2000);
    }

    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [activeTab, engineEnabled, state.currentFen, depth, multipv, engineMode, cloudBlocked]);

  useEffect(() => {
    if (activeTab !== 'imitator') return;

    const loadCoaches = async () => {
      setCoachStatus('loading');
      setCoachError(null);
      try {
        const resp = await fetch(`${TAGGER_BASE}/tagger/imitator/players?source=library`);
        if (!resp.ok) throw new Error(`Coach list failed (${resp.status})`);
        const data = await resp.json();
        const players = Array.isArray(data.players) ? data.players : [];
        setCoachOptions(players);
        setCoachStatus('ready');
        if (!selectedCoach && players.length > 0) setSelectedCoach(players[0]);
      } catch (e: any) {
        setCoachStatus('error');
        setCoachError(e?.message || 'Failed to load coaches');
      }
    };

    const loadPlayers = async () => {
      setPlayerStatus('loading');
      setPlayerError(null);
      try {
        const resp = await fetch(
          `${TAGGER_BASE}/tagger/imitator/players?source=user&status=success&include_ids=true`
        );
        if (!resp.ok) throw new Error(`Player list failed (${resp.status})`);
        const data = await resp.json();
        const players = Array.isArray(data.players) ? data.players : [];
        setPlayerOptions(players);
        setPlayerStatus('ready');
        if (!selectedPlayer && players.length > 0) setSelectedPlayer(players[0].id);
      } catch (e: any) {
        setPlayerStatus('error');
        setPlayerError(e?.message || 'Failed to load players');
      }
    };

    if (coachStatus === 'idle') void loadCoaches();
    if (playerStatus === 'idle') void loadPlayers();
  }, [activeTab, TAGGER_BASE, coachStatus, playerStatus, selectedCoach, selectedPlayer]);

  useEffect(() => {
    if (activeTab !== 'imitator') return;
    if (!state.currentFen || imitatorTargets.length === 0) return;

    const currentRequest = imitatorRequestRef.current + 1;
    imitatorRequestRef.current = currentRequest;

    setImitatorResults((prev) => {
      const next = { ...prev };
      for (const target of imitatorTargets) {
        next[target.id] = {
          ...next[target.id],
          status: 'running',
          error: null,
        };
      }
      return next;
    });

    const run = async () => {
      const tasks = imitatorTargets.map(async (target) => {
        const payload: Record<string, any> = {
          fen: state.currentFen,
          top_n: 5,
          depth: 14,
          source: target.source,
        };
        if (target.playerId) payload.player_id = target.playerId;
        if (target.player) payload.player = target.player;
        const resp = await fetch(`${TAGGER_BASE}/tagger/imitator`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(text || `Imitator error (${resp.status})`);
        }
        return resp.json();
      });

      const results = await Promise.allSettled(tasks);
      if (imitatorRequestRef.current !== currentRequest) return;

      setImitatorResults((prev) => {
        const next = { ...prev };
        results.forEach((result, index) => {
          const target = imitatorTargets[index];
          if (!target) return;
          if (result.status === 'fulfilled') {
            next[target.id] = {
              status: 'ready',
              moves: Array.isArray(result.value?.moves) ? result.value.moves : [],
              updated: Date.now(),
              error: null,
            };
          } else {
            next[target.id] = {
              status: 'error',
              moves: [],
              updated: Date.now(),
              error: result.reason?.message || 'Imitator failed',
            };
          }
        });
        return next;
      });
    };

    void run();
  }, [activeTab, state.currentFen, imitatorTargets, TAGGER_BASE]);

  useEffect(() => {
    if (engineEnabled) return;
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setStatus('idle');
    setHealth('down');
    setLines([]);
    setError(null);
    setLastUpdated(null);
    setSource(null);
    setCloudBlocked(false);
    setEngineNotice(null);
  }, [engineEnabled]);

  useEffect(() => {
    if (activeTab !== 'analysis' || !engineEnabled) return;
    setLines([]);
    setStatus('idle');
    setError(null);
    setSource(null);
    setCloudBlocked(false);
    setEngineNotice(null);
  }, [activeTab, engineEnabled, state.currentFen, depth, multipv, engineMode]);

  const renderAnalysis = () => (
    <div className="patch-analysis-panel">
      <div className="patch-analysis-status">
        <span className={`patch-analysis-badge is-${status}`}>{status}</span>
        <span className="patch-analysis-health">
          {!engineEnabled
            ? 'Engine Off'
            : health === 'ok'
              ? 'Engine OK'
              : health === 'down'
                ? 'Engine Down'
                : 'Engine Unknown'}
        </span>
        {source && <span className="patch-analysis-source">{source}</span>}
        {lastUpdated && (
          <span className="patch-analysis-updated">
            {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>
      {engineNotice && <div className="patch-analysis-error">{engineNotice}</div>}
      {!engineNotice && error && <div className="patch-analysis-error">{error}</div>}
      <div className="patch-analysis-lines">
        {!engineEnabled && (
          <div className="patch-analysis-empty">No analysis yet. Turn on engine to analyze.</div>
        )}
        {engineEnabled && lines.length === 0 && (
          <div className="patch-analysis-empty">No analysis yet.</div>
        )}
        {lines.map((line) => {
          const sanLine = uciLineToSan(line.pv || [], state.currentFen);
          const sanMoves = sanLine
            .map((step) => step.san)
            .filter((move): move is string => Boolean(move));
          const sanText = formatSanWithMoveNumbers(sanMoves, state.currentFen);
          return (
          <div key={`pv-${line.multipv}`} className="patch-analysis-line">
            <div className="patch-analysis-score">{formatScore(line.score)}</div>
            <div className="patch-analysis-pv">
              {sanText || (line.pv?.join(' ') ?? '')}
            </div>
          </div>
        );
        })}
      </div>
    </div>
  );

  const renderImitatorPanel = () => (
    <div className="patch-analysis-panel patch-imitator-panel">
      {imitatorTargets.length === 0 && (
        <div className="patch-analysis-empty">
          Add a coach or player to generate style-guided moves.
        </div>
      )}
      {imitatorTargets.map((target) => {
        const result = imitatorResults[target.id] || { status: 'idle', moves: [] };
        return (
          <div key={target.id} className="patch-imitator-card">
            <div className="patch-imitator-header">
              <div>
                <div className="patch-imitator-title">{target.label}</div>
                <div className="patch-imitator-meta">
                  {target.kind === 'coach' ? 'Coach' : 'Player'}
                  {result.updated && (
                    <span className="patch-imitator-updated">
                      {new Date(result.updated).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>
              <button
                type="button"
                className="patch-imitator-remove"
                onClick={() => {
                  setImitatorTargets((prev) => prev.filter((item) => item.id !== target.id));
                  setImitatorResults((prev) => {
                    const next = { ...prev };
                    delete next[target.id];
                    return next;
                  });
                }}
              >
                Remove
              </button>
            </div>
            <div className="patch-imitator-status">
              <span className={`patch-analysis-badge is-${result.status}`}>{result.status}</span>
              {result.error && <span className="patch-analysis-error">{result.error}</span>}
            </div>
            <div className="patch-imitator-moves">
              {result.status === 'running' && (
                <div className="patch-analysis-empty">Analyzing...</div>
              )}
              {result.status !== 'running' && result.moves.length === 0 && (
                <div className="patch-analysis-empty">No moves yet.</div>
              )}
              {result.moves.map((move, idx) => (
                <div key={`${target.id}-${idx}`} className="patch-imitator-row">
                  <div className="patch-imitator-prob">{formatProbability(move.probability)}</div>
                  <div className="patch-imitator-move">
                    {move.move || move.uci}
                    {move.tags && move.tags.length > 0 && (
                      <span className="patch-imitator-tags">{formatTags(move.tags)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="patch-sidebar-content">
      <div className="patch-sidebar-tabs">
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'chapters' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('chapters')}
        >
          Chapters
        </button>
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'analysis' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          Analysis
        </button>
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'imitator' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('imitator')}
        >
          Imitator
        </button>
      </div>

      {activeTab === 'chapters' && (
        <ChapterList
          chapters={chapters}
          currentChapterId={currentChapterId}
          onSelectChapter={onSelectChapter}
          onCreateChapter={onCreateChapter}
        />
      )}

      {activeTab === 'analysis' && (
        <div className="patch-analysis-scroll">
          <div className="patch-analysis-settings">
            <div className="patch-analysis-field">
              <span className="patch-analysis-label">Depth</span>
              <select value={depth} onChange={(e) => setDepth(Number(e.target.value))}>
                {[8, 10, 12, 14, 16, 18, 20].map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div className="patch-analysis-field">
              <span className="patch-analysis-label">Lines</span>
              <select value={multipv} onChange={(e) => setMultipv(Number(e.target.value))}>
                {[1, 2, 3, 4, 5].map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div className="patch-analysis-toggle">
              <label className="patch-toggle">
                <input
                  type="checkbox"
                  checked={engineEnabled}
                  onChange={(e) => {
                    const enabled = e.target.checked;
                    setEngineEnabled(enabled);
                    if (enabled) {
                      setEngineMode('sf');
                      setCloudBlocked(false);
                      setEngineNotice(null);
                    }
                  }}
                  aria-label="Engine"
                />
                <span className="patch-toggle-track" />
              </label>
            </div>
            <div className="patch-analysis-field">
              <span className="patch-analysis-label">Engine</span>
              <select
                value={engineMode}
                disabled={!engineEnabled}
                onChange={(e) => {
                  setEngineMode(e.target.value as 'cloud' | 'sf');
                  setCloudBlocked(false);
                  setEngineNotice(null);
                }}
              >
                <option value="cloud">Lichess Cloud</option>
                <option value="sf">SFCata</option>
              </select>
            </div>
          </div>
          {renderAnalysis()}
        </div>
      )}

      {activeTab === 'imitator' && (
        <div className="patch-analysis-scroll">
          <div className="patch-imitator-settings">
            <div className="patch-imitator-field">
              <span className="patch-analysis-label">Add Coach</span>
              <select
                value={selectedCoach}
                onChange={(e) => setSelectedCoach(e.target.value)}
                disabled={coachStatus !== 'ready'}
              >
                {coachStatus === 'loading' && <option>Loading...</option>}
                {coachStatus === 'error' && <option>Unavailable</option>}
                {coachStatus === 'ready' &&
                  coachOptions.map((name) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
              </select>
            </div>
            <button
              type="button"
              className="patch-imitator-add"
              disabled={!selectedCoach || coachStatus !== 'ready'}
              onClick={() => {
                const name = selectedCoach;
                if (!name) return;
                const id = `coach:${name}`;
                setImitatorTargets((prev) => {
                  if (prev.some((item) => item.id === id)) return prev;
                  return [
                    ...prev,
                    {
                      id,
                      label: name,
                      source: 'library',
                      player: name,
                      kind: 'coach',
                    },
                  ];
                });
              }}
            >
              Add
            </button>
            <div className="patch-imitator-field">
              <span className="patch-analysis-label">Add Players</span>
              <select
                value={selectedPlayer}
                onChange={(e) => setSelectedPlayer(e.target.value)}
                disabled={playerStatus !== 'ready'}
              >
                {playerStatus === 'loading' && <option>Loading...</option>}
                {playerStatus === 'error' && <option>Unavailable</option>}
                {playerStatus === 'ready' &&
                  playerOptions.map((player) => (
                    <option key={player.id} value={player.id}>
                      {player.name}
                    </option>
                  ))}
              </select>
            </div>
            <button
              type="button"
              className="patch-imitator-add"
              disabled={!selectedPlayer || playerStatus !== 'ready'}
              onClick={() => {
                const player = playerOptions.find((item) => item.id === selectedPlayer);
                if (!player) return;
                const id = `player:${player.id}`;
                setImitatorTargets((prev) => {
                  if (prev.some((item) => item.id === id)) return prev;
                  return [
                    ...prev,
                    {
                      id,
                      label: player.name,
                      source: 'user',
                      playerId: player.id,
                      kind: 'player',
                    },
                  ];
                });
              }}
            >
              Add
            </button>
          </div>
          {(coachError || playerError) && (
            <div className="patch-analysis-error">
              {coachError || playerError}
            </div>
          )}
          {renderImitatorPanel()}
        </div>
      )}
    </div>
  );
}

export default StudySidebar;
