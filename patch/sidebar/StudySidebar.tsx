import React, { useEffect, useRef, useState } from 'react';
import { useStudy } from '../studyContext';
import { ChapterList } from './ChapterList';

export interface StudySidebarProps {
  chapters: Array<{ id: string; title?: string; order?: number }>;
  currentChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
}

type EngineLine = {
  multipv: number;
  score: number | string;
  pv: string[];
};

const LICHESS_CLOUD_EVAL = 'https://lichess.org/api/cloud-eval';

export function StudySidebar({
  chapters,
  currentChapterId,
  onSelectChapter,
  onCreateChapter,
}: StudySidebarProps) {
  const { state } = useStudy();
  const [activeTab, setActiveTab] = useState<'chapters' | 'analysis'>('chapters');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [depth, setDepth] = useState(14);
  const [multipv, setMultipv] = useState(3);
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [lines, setLines] = useState<EngineLine[]>([]);
  const [status, setStatus] = useState<'idle' | 'running' | 'ready' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [health, setHealth] = useState<'unknown' | 'ok' | 'down'>('unknown');
  const inFlightRef = useRef(false);
  const pollRef = useRef<number | null>(null);
  const nextAllowedRef = useRef<number>(0);

  const analyzePosition = async (fen: string) => {
    if (!fen || inFlightRef.current) return;
    const now = Date.now();
    if (now < nextAllowedRef.current) return;
    inFlightRef.current = true;
    setStatus('running');
    setError(null);
    try {
      const params = new URLSearchParams({
        fen,
        multiPv: String(multipv),
      });
      const response = await fetch(`${LICHESS_CLOUD_EVAL}?${params.toString()}`);
      if (response.status === 429) {
        nextAllowedRef.current = Date.now() + 10000;
        throw new Error('Rate limited (429). Backing off for 10s.');
      }
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Engine error (${response.status})`);
      }
      const data = await response.json();
      const parsedLines: EngineLine[] = Array.isArray(data.pvs)
        ? data.pvs.map((pv: any, index: number) => ({
            multipv: index + 1,
            score: pv.mate != null ? `mate${pv.mate}` : pv.cp ?? 0,
            pv: typeof pv.moves === 'string' ? pv.moves.split(' ') : [],
          }))
        : [];
      setLines(parsedLines);
      setStatus('ready');
      setLastUpdated(Date.now());
      setHealth('ok');
    } catch (e: any) {
      setStatus('error');
      setError(e?.message || 'Engine request failed');
      setHealth('down');
    } finally {
      inFlightRef.current = false;
    }
  };

  useEffect(() => {
    if (activeTab !== 'analysis' || !autoAnalyze) return;

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
  }, [activeTab, autoAnalyze, state.currentFen, depth, multipv]);

  const renderAnalysis = () => (
    <div className="patch-analysis-panel">
      <div className="patch-analysis-status">
        <span className={`patch-analysis-badge is-${status}`}>{status}</span>
        <span className="patch-analysis-health">
          {health === 'ok' ? 'Engine OK' : health === 'down' ? 'Engine Down' : 'Engine Unknown'}
        </span>
        {lastUpdated && (
          <span className="patch-analysis-updated">
            {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>
      {error && <div className="patch-analysis-error">{error}</div>}
      <div className="patch-analysis-lines">
        {lines.length === 0 && <div className="patch-analysis-empty">No analysis yet.</div>}
        {lines.map((line) => (
          <div key={`pv-${line.multipv}`} className="patch-analysis-line">
            <div className="patch-analysis-score">{line.score}</div>
            <div className="patch-analysis-pv">{line.pv?.join(' ')}</div>
          </div>
        ))}
      </div>
      <div className="patch-analysis-controls">
        <label>
          <input
            type="checkbox"
            checked={autoAnalyze}
            onChange={(e) => setAutoAnalyze(e.target.checked)}
          />
          Auto
        </label>
        <button type="button" onClick={() => analyzePosition(state.currentFen)}>
          Analyze
        </button>
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
        {activeTab === 'analysis' && (
          <button
            type="button"
            className="patch-sidebar-settings"
            onClick={() => setSettingsOpen((prev) => !prev)}
          >
            Settings
          </button>
        )}
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
        <>
          {settingsOpen && (
            <div className="patch-analysis-settings">
              <label>
                Depth
                <select value={depth} onChange={(e) => setDepth(Number(e.target.value))}>
                  {[8, 10, 12, 14, 16, 18, 20].map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </label>
              <label>
                Lines
                <select value={multipv} onChange={(e) => setMultipv(Number(e.target.value))}>
                  {[1, 2, 3, 4, 5].map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </label>
            </div>
          )}
          {renderAnalysis()}
        </>
      )}
    </div>
  );
}

export default StudySidebar;
