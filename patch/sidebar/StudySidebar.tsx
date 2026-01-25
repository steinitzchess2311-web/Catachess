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
  const [activeTab, setActiveTab] = useState<'chapters' | 'analysis'>('chapters');
  const [depth, setDepth] = useState(14);
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);
  const [engineMode, setEngineMode] = useState<'cloud' | 'sf'>('cloud');
  const [cloudBlocked, setCloudBlocked] = useState(false);
  const [engineNotice, setEngineNotice] = useState<string | null>(null);
  const [lines, setLines] = useState<EngineLine[]>([]);
  const [status, setStatus] = useState<'idle' | 'running' | 'ready' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [health, setHealth] = useState<'unknown' | 'ok' | 'down'>('unknown');
  const [source, setSource] = useState<EngineSource | null>(null);
  const inFlightRef = useRef(false);
  const pollRef = useRef<number | null>(null);
  const nextAllowedRef = useRef<number>(0);

  const analyzePosition = async (fen: string) => {
    if (!fen || inFlightRef.current) return;
    if (engineMode === 'cloud' && cloudBlocked) return;
    const now = Date.now();
    if (now < nextAllowedRef.current) return;
    inFlightRef.current = true;
    setStatus('running');
    setError(null);
    try {
      const result = await analyzeWithFallback(fen, depth, multipv, engineMode);
      setLines(result.lines);
      setSource(result.source);
      setStatus('ready');
      setLastUpdated(Date.now());
      setHealth('ok');
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
    pollRef.current = window.setInterval(() => {
      analyzePosition(state.currentFen);
    }, 2000);

    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [activeTab, engineEnabled, state.currentFen, depth, multipv, engineMode, cloudBlocked]);

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
                      setEngineMode('cloud');
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
    </div>
  );
}

export default StudySidebar;
