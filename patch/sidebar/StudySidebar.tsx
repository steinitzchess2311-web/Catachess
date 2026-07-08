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
import { useImitator } from './hooks/useImitator';
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

  // Get the global cache manager instance
  const cacheManager = getCacheManager();

  // Use custom hooks
  const engineAnalysis = useEngineAnalysis({
    enabled: activeTab === 'analysis' && engineEnabled,
    fen: state.currentFen,
    multipv,
  });

  const imitator = useImitator({
    enabled: activeTab === 'imitator',
    fen: state.currentFen,
    depth: 14,
    multipv,
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

  // Imitator handlers
  const handleAddCoach = () => {
    const name = imitator.selectedCoach;
    if (!name) return;
    imitator.addTarget({
      id: `coach:${name}`,
      label: name,
      source: 'library',
      player: name,
      kind: 'coach',
    });
  };

  const handleAddPlayer = () => {
    const player = imitator.playerOptions.find((item) => item.id === imitator.selectedPlayer);
    if (!player) return;
    imitator.addTarget({
      id: `player:${player.id}`,
      label: player.name,
      source: 'user',
      playerId: player.id,
      kind: 'player',
    });
  };

  const handleAddEngine = () => {
    const engine = imitator.selectedEngine;
    const label = 'Engine (Auto)';
    imitator.addTarget({
      id: `engine:${engine}`,
      label,
      engine,
      kind: 'engine',
    });
  };

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
        {/* Imitator tab temporarily hidden
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'imitator' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('imitator')}
        >
          Imitator
        </button>
        */}
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
            engineEnabled={engineEnabled}
            onEngineEnabledChange={setEngineEnabled}
          />
          <AnalysisPanel
            engineEnabled={engineEnabled}
            lines={formattedLines}
            error={engineAnalysis.error}
            turn={getTurn(state.currentFen) ?? 'w'}
          />
        </div>
      )}

      {/* Imitator panel temporarily hidden
      {activeTab === 'imitator' && (
        <div className="patch-analysis-scroll">
          <ImitatorSettings
            coachOptions={imitator.coachOptions}
            selectedCoach={imitator.selectedCoach}
            onCoachChange={imitator.setSelectedCoach}
            coachStatus={imitator.coachStatus}
            onAddCoach={handleAddCoach}
            playerOptions={imitator.playerOptions}
            selectedPlayer={imitator.selectedPlayer}
            onPlayerChange={imitator.setSelectedPlayer}
            playerStatus={imitator.playerStatus}
            onAddPlayer={handleAddPlayer}
            selectedEngine={imitator.selectedEngine}
            onEngineChange={imitator.setSelectedEngine}
            onAddEngine={handleAddEngine}
            coachError={imitator.coachError}
            playerError={imitator.playerError}
          />
          <ImitatorPanel
            targets={imitator.targets}
            results={imitator.results}
            onRemoveTarget={imitator.removeTarget}
          />
        </div>
      )}
      */}
    </div>
  );
}

export default StudySidebar;
