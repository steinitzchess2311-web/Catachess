import React, { useEffect, useRef, useState, useMemo } from 'react';
import { useStudy } from '../studyContext';
import { uciLineToSan } from '../chessJS/uci';
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
  const componentRenderStart = performance.now();
  const renderCountRef = useRef(0);
  const prevPropsRef = useRef({ chapters, currentChapterId });
  renderCountRef.current++;

  // Detect what changed to trigger this render
  if (renderCountRef.current > 1) {
    console.log(`[COMPONENT PERF] ===== Render #${renderCountRef.current} Triggered =====`);
    if (prevPropsRef.current.chapters !== chapters) {
      console.log('[COMPONENT PERF] ⚠️ Chapters prop changed');
    }
    if (prevPropsRef.current.currentChapterId !== currentChapterId) {
      console.log('[COMPONENT PERF] ⚠️ CurrentChapterId prop changed');
    }
  }
  prevPropsRef.current = { chapters, currentChapterId };

  const { state } = useStudy();
  const prevStateRef = useRef({ currentFen: state.currentFen });

  // Track state changes
  if (renderCountRef.current > 1) {
    if (prevStateRef.current.currentFen !== state.currentFen) {
      console.log('[COMPONENT PERF] ⚠️ CurrentFen changed from study state');
      console.log('[COMPONENT PERF]   Old:', prevStateRef.current.currentFen.slice(0, 30) + '...');
      console.log('[COMPONENT PERF]   New:', state.currentFen.slice(0, 30) + '...');
    }
  }
  prevStateRef.current = { currentFen: state.currentFen };

  const [activeTab, setActiveTab] = useState<'chapters' | 'analysis' | 'imitator'>('chapters');
  const [depth, setDepth] = useState(14);
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);

  // Get the global cache manager instance
  const cacheManager = getCacheManager();

  // Use custom hooks
  const engineAnalysis = useEngineAnalysis({
    enabled: activeTab === 'analysis' && engineEnabled,
    fen: state.currentFen,
    depth,
    multipv,
  });

  const imitator = useImitator({
    enabled: activeTab === 'imitator',
    fen: state.currentFen,
    depth,
    multipv,
  });

  // Monitor component render performance
  useEffect(() => {
    const renderDuration = performance.now() - componentRenderStart;
    console.log('[COMPONENT PERF] ===== Render Cycle Complete =====');
    console.log(`[COMPONENT PERF] Render #${renderCountRef.current}`);
    console.log(`[COMPONENT PERF] Render duration: ${renderDuration.toFixed(2)}ms`);
    console.log('[COMPONENT PERF] Active tab:', activeTab);
    console.log('[COMPONENT PERF] Engine enabled:', engineEnabled);
    console.log('[COMPONENT PERF] Lines count:', engineAnalysis.lines.length);
    console.log('[COMPONENT PERF] Formatted lines count:', formattedLines.length);

    // Schedule a post-paint check
    requestAnimationFrame(() => {
      const paintDuration = performance.now() - componentRenderStart;
      console.log(`[COMPONENT PERF] Paint complete: ${paintDuration.toFixed(2)}ms`);
      console.log('[COMPONENT PERF] =====================================');
    });
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

  // Memoize formatted lines to avoid expensive UCI->SAN conversion on every render
  const formattedLines = useMemo(() => {
    const memoStart = performance.now();
    console.log('[ENGINE PERF] ===== Formatting Lines (useMemo triggered) =====');
    console.log('[ENGINE PERF] Lines to format:', engineAnalysis.lines.length);
    console.log('[ENGINE PERF] Current FEN:', state.currentFen.slice(0, 50) + '...');
    console.log('[ENGINE PERF] ⚠️ useMemo is running - dependencies changed');

    if (engineAnalysis.lines.length === 0) {
      console.log('[ENGINE PERF] No lines to format');
      return [];
    }

    const result = engineAnalysis.lines.map((line, index) => {
      const lineStart = performance.now();
      console.log(`[ENGINE PERF] Line ${index + 1}/${engineAnalysis.lines.length} - Starting conversion`);
      console.log(`[ENGINE PERF]   - UCI PV length: ${line.pv?.length || 0} moves`);

      // Step 1: UCI to SAN conversion
      const uciStart = performance.now();
      const sanLine = uciLineToSan(line.pv || [], state.currentFen);
      const uciDuration = performance.now() - uciStart;
      console.log(`[ENGINE PERF]   - UCI->SAN conversion: ${uciDuration.toFixed(2)}ms`);

      // Step 2: Extract SAN moves
      const extractStart = performance.now();
      const sanMoves = sanLine
        .map((step) => step.san)
        .filter((move): move is string => Boolean(move));
      const extractDuration = performance.now() - extractStart;
      console.log(`[ENGINE PERF]   - Extract SAN moves: ${extractDuration.toFixed(2)}ms`);

      // Step 3: Format with move numbers
      const formatStart = performance.now();
      const sanText = formatSanWithMoveNumbers(sanMoves, state.currentFen);
      const formatDuration = performance.now() - formatStart;
      console.log(`[ENGINE PERF]   - Format move numbers: ${formatDuration.toFixed(2)}ms`);

      const lineDuration = performance.now() - lineStart;
      console.log(`[ENGINE PERF]   - Line ${index + 1} total: ${lineDuration.toFixed(2)}ms`);

      return {
        ...line,
        sanText,
      };
    });

    const memoDuration = performance.now() - memoStart;
    console.log('[ENGINE PERF] ===== Formatting Complete =====');
    console.log(`[ENGINE PERF] Total formatting time: ${memoDuration.toFixed(2)}ms`);
    console.log(`[ENGINE PERF] Average per line: ${(memoDuration / engineAnalysis.lines.length).toFixed(2)}ms`);

    return result;
  }, [engineAnalysis.lines, state.currentFen]);

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
          onRenameChapter={onRenameChapter}
          onDeleteChapter={onDeleteChapter}
          onReorderChapters={onReorderChapters}
        />
      )}

      {activeTab === 'analysis' && (
        <div className="patch-analysis-scroll">
          <AnalysisSettings
            depth={depth}
            onDepthChange={setDepth}
            multipv={multipv}
            onMultipvChange={setMultipv}
            engineEnabled={engineEnabled}
            onEngineEnabledChange={setEngineEnabled}
          />
          <AnalysisPanel
            engineEnabled={engineEnabled}
            lines={formattedLines}
            status={engineAnalysis.status}
            health={engineAnalysis.health}
            error={engineAnalysis.error}
            lastUpdated={engineAnalysis.lastUpdated}
            engineOrigin={engineAnalysis.engineOrigin}
          />
        </div>
      )}

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
    </div>
  );
}

export default StudySidebar;
