import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { StudyProvider, useStudy } from '../studyContext';
import { StudyBoard } from '../board/studyBoard';
import { MoveTree } from '../sidebar/movetree';
import { StudyErrorBoundary } from '../components/ErrorBoundary';
import { AnalysisSettings } from '../sidebar/components/AnalysisSettings';
import { AnalysisPanel } from '../sidebar/components/AnalysisPanel';
import { useEngineAnalysis } from '../sidebar/hooks/useEngineAnalysis';
import { uciLineToSan } from '../chessJS/uci';
import { getTurn } from '../chessJS/fen';
import { formatSanWithMoveNumbers } from '../sidebar/utils/formatters';
import { fetchGame } from '../modules/explorer/api';
import type { GameDetail } from '../modules/explorer/types';
import { uciMovesToTree } from './uciToTree';

// =============================================================================
// Game metadata panel
// =============================================================================

function GameInfoPanel({ game }: { game: GameDetail }) {
  const resultText =
    game.winner === 'white' ? '1–0'
    : game.winner === 'black' ? '0–1'
    : '½–½';

  const accentClass =
    game.winner === 'white' ? 'game-info--white-wins'
    : game.winner === 'black' ? 'game-info--black-wins'
    : 'game-info--draw';

  const dateStr = game.month ?? (game.year != null && game.year > 100 ? String(game.year) : null);

  return (
    <div className={`game-info-panel ${accentClass}`}>
      <div className="game-info-result">{resultText}</div>

      <div className="game-info-players">
        <div className="game-info-player">
          <span className="game-info-piece game-info-piece--white">♔</span>
          <div className="game-info-player-body">
            <span className="game-info-name">{game.white.name}</span>
            {game.white.rating != null && (
              <span className="game-info-rating">{game.white.rating}</span>
            )}
          </div>
        </div>
        <div className="game-info-player">
          <span className="game-info-piece game-info-piece--black">♚</span>
          <div className="game-info-player-body">
            <span className="game-info-name">{game.black.name}</span>
            {game.black.rating != null && (
              <span className="game-info-rating">{game.black.rating}</span>
            )}
          </div>
        </div>
      </div>

      <div className="game-info-meta">
        {game.event && <div className="game-info-event">{game.event}</div>}
        {dateStr && <div className="game-info-date">{dateStr}</div>}
      </div>
    </div>
  );
}

// =============================================================================
// Left sidebar — tabs: Info | Analysis
// Must be inside StudyProvider (needs currentFen for engine)
// =============================================================================

function GameSidebar({ game }: { game: GameDetail }) {
  const { state } = useStudy();
  const [activeTab, setActiveTab] = useState<'info' | 'analysis'>('info');
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);

  const engineAnalysis = useEngineAnalysis({
    enabled: activeTab === 'analysis' && engineEnabled,
    fen: state.currentFen,
    multipv,
  });

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
          className={`patch-sidebar-tab${activeTab === 'info' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          Game
        </button>
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'analysis' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          Analysis
        </button>
      </div>

      {activeTab === 'info' && <GameInfoPanel game={game} />}

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
            status={engineAnalysis.status}
            health={engineAnalysis.health}
            error={engineAnalysis.error}
            lastUpdated={engineAnalysis.lastUpdated}
            engineOrigin={engineAnalysis.engineOrigin}
            turn={getTurn(state.currentFen) ?? 'w'}
          />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Inner content — must live inside StudyProvider
// =============================================================================

function GameViewerContent({ game }: { game: GameDetail }) {
  const { loadTree } = useStudy();
  const layoutRef = useRef<HTMLDivElement>(null);
  const [rightbarWidth, setRightbarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);

  const rightbarMin = 220;
  const rightbarMax = 520;

  // Load game tree once when game data arrives
  useEffect(() => {
    const tree = uciMovesToTree(game.moves);
    loadTree(tree);
  }, [game, loadTree]);

  // Rightbar resize
  const startResize = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;
    const onMove = (e: PointerEvent) => {
      if (!layoutRef.current) return;
      const rect = layoutRef.current.getBoundingClientRect();
      setRightbarWidth(Math.min(rightbarMax, Math.max(rightbarMin, rect.right - e.clientX)));
    };
    const onUp = () => setIsResizing(false);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  return (
    <div className="patch-study-page game-viewer-page">
      <div className="patch-study-layout" ref={layoutRef}>
        {/* Left: game info + engine analysis */}
        <div className="patch-study-sidebar">
          <GameSidebar game={game} />
        </div>

        {/* Center: board — draggable, all changes are local only */}
        <div className="patch-study-main">
          <StudyBoard />
        </div>

        {/* Resize handle */}
        <div
          className="patch-study-splitter"
          onPointerDown={startResize}
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize move tree panel"
        />

        {/* Right: move tree */}
        <div className="patch-study-rightbar" style={{ width: rightbarWidth }}>
          <div className="patch-right-panel">
            <MoveTree />
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Loading / error screens
// =============================================================================

function LoadingScreen() {
  return (
    <div className="game-viewer-loading">
      <div className="explorer-loading">
        <div className="explorer-loading__dot" />
        <div className="explorer-loading__dot" />
        <div className="explorer-loading__dot" />
      </div>
    </div>
  );
}

function ErrorScreen({ message }: { message: string }) {
  return (
    <div className="game-viewer-error">
      <p>{message}</p>
      <button type="button" className="patch-modal-button" onClick={() => window.history.back()}>
        Go back
      </button>
    </div>
  );
}

// =============================================================================
// Outer shell — fetches game, mounts StudyProvider
// =============================================================================

function GameViewerShell() {
  const { id } = useParams<{ id: string }>();
  const [game, setGame] = useState<GameDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) { setError('No game ID provided.'); return; }
    const controller = new AbortController();
    fetchGame(id, controller.signal)
      .then(setGame)
      .catch((e: unknown) => {
        if ((e as Error)?.name !== 'AbortError') {
          setError((e as Error)?.message ?? 'Failed to load game.');
        }
      });
    return () => controller.abort();
  }, [id]);

  if (error) return <ErrorScreen message={error} />;
  if (!game) return <LoadingScreen />;

  return (
    <StudyErrorBoundary>
      <StudyProvider>
        <GameViewerContent game={game} />
      </StudyProvider>
    </StudyErrorBoundary>
  );
}

export function GameViewerPage() {
  return <GameViewerShell />;
}

export default GameViewerPage;
