/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Study sidebar tabs for chapters, analysis, and predictor panels.
*/

import React, { useEffect, useState, useMemo } from 'react';
import { useStudy } from '../studyContext';
import { uciLineToSan } from '../chessJS/uci';
import { getTurn } from '../chessJS/fen';
import { ChapterList } from './ChapterList';
import { getCacheManager } from '../engine/cache';
import { AnalysisSettings } from './components/AnalysisSettings';
import { AnalysisPanel } from './components/AnalysisPanel';
import { ImitatorSettings } from './components/ImitatorSettings';
import { ImitatorPanel } from './components/ImitatorPanel';
import { useEngineAnalysis } from './hooks/useEngineAnalysis';
import { usePredictor, type PredictorProvider } from './hooks/useImitator';
import type { EngineMode } from '../engine/types';
import { formatSanWithMoveNumbers } from './utils/formatters';

export interface StudySidebarProps {
  chapters: Array<{ id: string; title?: string; order?: number }>;
  currentChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
  onRenameChapter: (chapterId: string, title: string) => Promise<void> | void;
  onDeleteChapter: (chapterId: string) => Promise<void> | void;
  onReorderChapters: (
    order: string[],
    context: { draggedId: string; targetId: string; placement: 'before' | 'after' }
  ) => Promise<void> | void;
}

export function StudySidebar({
  chapters,
  currentChapterId,
  onSelectChapter,
  onCreateChapter,
  onRenameChapter,
  onDeleteChapter,
  onReorderChapters,
}: StudySidebarProps) {
  const { state } = useStudy();

  const [activeTab, setActiveTab] = useState<'chapters' | 'analysis' | 'imitator'>('chapters');
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);
  const [engineMode, setEngineMode] = useState<EngineMode>('auto');
  const [predictorProvider, setPredictorProvider] = useState<PredictorProvider>('maia');
  const [predictorTopK, setPredictorTopK] = useState(5);
  const [predictorElo, setPredictorElo] = useState(1500);
  const [predictorEnabled, setPredictorEnabled] = useState(false);

  // Get the global cache manager instance
  const cacheManager = getCacheManager();

  // Use custom hooks
  const engineAnalysis = useEngineAnalysis({
    enabled: activeTab === 'analysis' && engineEnabled,
    fen: state.currentFen,
    multipv,
    engineMode,
  });

  const predictor = usePredictor({
    enabled: activeTab === 'imitator' && predictorEnabled,
    fen: state.currentFen,
    provider: predictorProvider,
    topK: predictorTopK,
    elo: predictorElo,
  });

  // Expose cache stats to window for debugging
  useEffect(() => {
    (window as any).cacheStats = () => cacheManager.printStats();
    (window as any).cacheClear = () => cacheManager.clear();
    return () => {
      delete (window as any).cacheStats;
      delete (window as any).cacheClear;
    };
  }, [cacheManager]);

  // Memoize formatted lines to avoid expensive UCI->SAN conversion on every render.
  // Must use analysisFen (the FEN that produced these lines), NOT state.currentFen.
  // Using state.currentFen would cause a race: lines from the old position applied to
  // the new FEN → chess.js throws "Invalid move" inside useMemo → white screen.
  const formattedLines = useMemo(() => {
    if (!engineAnalysis.analysisFen || engineAnalysis.lines.length === 0) return [];
    const fen = engineAnalysis.analysisFen;
    return engineAnalysis.lines.map((line) => {
      const sanLine = uciLineToSan(line.pv || [], fen);
      const sanMoves = sanLine
        .map((step) => step.san)
        .filter((move): move is string => Boolean(move));
      const sanText = formatSanWithMoveNumbers(sanMoves, fen);
      return { ...line, sanText };
    });
  }, [engineAnalysis.lines, engineAnalysis.analysisFen]);

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
          Predictor
        </button>
      </div>

      {activeTab === 'chapters' && (
        <ChapterList
          chapters={chapters}
          currentChapterId={currentChapterId}
          onSelectChapter={onSelectChapter}
          onCreateChapter={onCreateChapter}
          onRenameChapter={onRenameChapter}
          onDeleteChapter={onDeleteChapter}
          onReorderChapters={onReorderChapters}
        />
      )}

      {activeTab === 'analysis' && (
        <div className="patch-analysis-scroll">
          <AnalysisSettings
            currentDepth={engineAnalysis.currentDepth}
            nps={engineAnalysis.nps}
            multipv={multipv}
            onMultipvChange={setMultipv}
            engineMode={engineMode}
            onEngineModeChange={setEngineMode}
            engineEnabled={engineEnabled}
            onEngineEnabledChange={setEngineEnabled}
          />
          <AnalysisPanel
            engineEnabled={engineEnabled}
            lines={formattedLines}
            error={engineAnalysis.error}
            turn={getTurn(state.currentFen) ?? 'w'}
            engineLabel={engineMode === 'auto' ? 'Auto engine' : engineMode === 'stockfish' ? 'Stockfish' : 'AlphaZero'}
          />
        </div>
      )}

      {activeTab === 'imitator' && (
        <div className="patch-analysis-scroll">
          <ImitatorSettings
            provider={predictorProvider}
            onProviderChange={setPredictorProvider}
            topK={predictorTopK}
            onTopKChange={setPredictorTopK}
            elo={predictorElo}
            onEloChange={setPredictorElo}
            enabled={predictorEnabled}
            onEnabledChange={setPredictorEnabled}
          />
          <ImitatorPanel
            result={predictor.result}
          />
        </div>
      )}
    </div>
  );
}

export default StudySidebar;
