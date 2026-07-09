/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Game viewer page with database game details and analysis tools.
*/

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import '../../frontend/web/src/pages/analysis/analysis.css';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useExplorerPlayers, loadPlayersFromStorage } from '../modules/explorer/hooks/useExplorerPlayers';
import { StudyProvider, useStudy } from '../studyContext';
import { StudyBoard } from '../board/studyBoard';
import { MoveTree } from '../sidebar/movetree';
import { StudyErrorBoundary } from '../components/ErrorBoundary';
import { AnalysisSettings } from '../sidebar/components/AnalysisSettings';
import { AnalysisPanel } from '../sidebar/components/AnalysisPanel';
import { useEngineAnalysis } from '../sidebar/hooks/useEngineAnalysis';
import type { EngineMode } from '../engine/types';
import { uciLineToSan } from '../chessJS/uci';
import { getTurn } from '../chessJS/fen';
import { formatSanWithMoveNumbers } from '../sidebar/utils/formatters';
import { exportPgn } from '../pgn/export';
import { fetchGame } from '../modules/explorer/api';
import type { GameDetail } from '../modules/explorer/types';
import { uciMovesToTree } from './uciToTree';
import { ExplorerPanel } from '../modules/explorer';
import { TrainPanel, TrainEntryModal } from '../modules/train';
import { StudyPickerModal } from '../components/StudyPickerModal';

// =============================================================================
// Game info card — TWIC-style
// =============================================================================

function GameInfoCard({ game }: { game: GameDetail }) {
  const resultText =
    game.winner === 'white' ? '1–0'
    : game.winner === 'black' ? '0–1'
    : '½–½';

  const resultClass =
    game.winner === 'white' ? 'game-card__result--white'
    : game.winner === 'black' ? 'game-card__result--black'
    : 'game-card__result--draw';

  const dateStr = game.month ?? (game.year != null && game.year > 100 ? String(game.year) : null);

  return (
    <div className="game-card">
      <div className="game-card__source">TWIC Database</div>

      <div className="game-card__players">
        <div className="game-card__player">
          <span className="game-card__dot game-card__dot--white" />
          <span className="game-card__name">{game.white.name}</span>
          {game.white.rating != null && (
            <span className="game-card__rating">{game.white.rating}</span>
          )}
        </div>
        <div className="game-card__player">
          <span className="game-card__dot game-card__dot--black" />
          <span className="game-card__name">{game.black.name}</span>
          {game.black.rating != null && (
            <span className="game-card__rating">{game.black.rating}</span>
          )}
        </div>
      </div>

      <div className={`game-card__result ${resultClass}`}>
        <span className="game-card__result-rule" />
        <span className="game-card__result-text">{resultText}</span>
        <span className="game-card__result-rule" />
      </div>

      {(game.event || dateStr) && (
        <div className="game-card__meta">
          {game.event && <span className="game-card__event">{game.event}</span>}
          {dateStr && <span className="game-card__date">{dateStr}</span>}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Left sidebar — Game | Analysis tabs
// =============================================================================

function GameSidebar({ game }: { game: GameDetail }) {
  const { state } = useStudy();
  const [activeTab, setActiveTab] = useState<'info' | 'analysis'>('info');
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);
  const [engineMode, setEngineMode] = useState<EngineMode>('auto');

  const engineAnalysis = useEngineAnalysis({
    enabled: activeTab === 'analysis' && engineEnabled,
    fen: state.currentFen,
    multipv,
    engineMode,
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

      {activeTab === 'info' && <GameInfoCard game={game} />}

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
            engineLabel={engineMode === 'auto' ? 'Auto engine' : engineMode === 'stockfish' ? 'Stockfish' : engineMode === 'lc0' ? 'Leela/LC0' : 'AlphaZero'}
          />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Bottom output bar — FEN + local PGN export
// =============================================================================

function GameOutputBar({ game }: { game: GameDetail }) {
  const { state } = useStudy();
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');
  const fen = state.currentFen;

  useEffect(() => {
    if (copyState === 'idle') return;
    const t = window.setTimeout(() => setCopyState('idle'), 1500);
    return () => window.clearTimeout(t);
  }, [copyState]);

  const handleCopyFen = async () => {
    if (!fen) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(fen);
      } else {
        const el = document.createElement('textarea');
        el.value = fen;
        el.style.position = 'absolute';
        el.style.left = '-9999px';
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
      }
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
  };

  const handleExportPgn = () => {
    const white = game.white.name + (game.white.rating != null ? ` (${game.white.rating})` : '');
    const black = game.black.name + (game.black.rating != null ? ` (${game.black.rating})` : '');
    const result =
      game.winner === 'white' ? '1-0'
      : game.winner === 'black' ? '0-1'
      : '1/2-1/2';

    const headers: Record<string, string> = {
      White: white,
      Black: black,
      Result: result,
    };
    if (game.event) headers['Event'] = game.event;
    if (game.year != null && game.year > 100) headers['Date'] = String(game.year);

    const { pgn } = exportPgn(state.tree, headers, {
      includeComments: true,
      includeNags: true,
      includeVariations: true,
    });

    const blob = new Blob([pgn], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${game.id}.pgn`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="game-output-bar">
      {/* Use .study-fen-wrap (position:relative) so .is-inline absolute button works */}
      <div className="study-fen-wrap game-output-fen-wrap">
        <textarea className="study-fen-box" readOnly value={fen || ''} />
        <button
          type="button"
          className="study-fen-button is-inline"
          onClick={handleCopyFen}
          disabled={!fen}
        >
          {copyState === 'copied' ? 'Copied' : copyState === 'error' ? 'Failed' : 'Copy FEN'}
        </button>
      </div>
      <button type="button" className="study-fen-button" onClick={handleExportPgn}>
        Export PGN
      </button>
    </div>
  );
}

// =============================================================================
// Inner content — must live inside StudyProvider
// =============================================================================

function GameViewerContent({ game }: { game: GameDetail }) {
  const { state, loadTree, addMove, enterTrainMode } = useStudy();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const layoutRef = useRef<HTMLDivElement>(null);
  const [rightbarWidth, setRightbarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState<'tree' | 'explorer'>('tree');

  const urlPlayers = searchParams.getAll('player');
  const explorerPlayers = urlPlayers.length > 0 ? urlPlayers : loadPlayersFromStorage();
  const onPlayersUrlChange = useCallback((next: string[]) => {
    setSearchParams(prev => {
      const updated = new URLSearchParams(prev);
      updated.delete('player');
      next.forEach(p => updated.append('player', p));
      return updated;
    }, { replace: true });
  }, [setSearchParams]);
  const { addPlayer, removePlayer } = useExplorerPlayers({
    players: explorerPlayers,
    onUrlChange: onPlayersUrlChange,
  });
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  const handleSendNavigate = useCallback(
    (studyId: string) => navigate(`/patch/workspace/${studyId}`),
    [navigate],
  );

  const rightbarMin = 220;
  const rightbarMax = 520;

  useEffect(() => {
    const tree = uciMovesToTree(game.moves);
    loadTree(tree);
  }, [game, loadTree]);

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
      <div className="analysis-header">
        <h2 className="analysis-title">Game Viewer</h2>
        <div className="analysis-header-actions">
          <button
            type="button"
            className="analysis-send-btn"
            onClick={() => setShowPicker(true)}
          >
            Save to Study
          </button>
        </div>
      </div>
      <div className="patch-study-layout" ref={layoutRef}>
        {!state.isTrainMode && (
          <div className="patch-study-sidebar">
            <GameSidebar game={game} />
          </div>
        )}

        <div className="patch-study-main">
          <StudyBoard isLocked={state.isTrainMode} />
        </div>

        <div
          className="patch-study-splitter"
          onPointerDown={startResize}
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize move tree panel"
        />

        <div className="patch-study-rightbar" style={{ width: rightbarWidth }}>
          {state.isTrainMode ? (
            <TrainPanel />
          ) : (
            <div className="patch-right-panel">
              <div className="patch-sidebar-tabs">
                <button
                  type="button"
                  className={`patch-sidebar-tab${rightPanelTab === 'tree' ? ' is-active' : ''}`}
                  onClick={() => setRightPanelTab('tree')}
                >
                  Moves
                </button>
                <button
                  type="button"
                  className={`patch-sidebar-tab${rightPanelTab === 'explorer' ? ' is-active' : ''}`}
                  onClick={() => setRightPanelTab('explorer')}
                >
                  Explorer
                </button>
                <button
                  type="button"
                  className="patch-sidebar-tab"
                  onClick={() => setShowTrainModal(true)}
                >
                  Train
                </button>
              </div>
              <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
                {rightPanelTab === 'tree' ? (
                  <MoveTree />
                ) : (
                  <ExplorerPanel
                    fen={state.currentFen}
                    onMoveSelect={addMove}
                    players={explorerPlayers}
                    onAddPlayer={addPlayer}
                    onRemovePlayer={removePlayer}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom output bar — hidden in train mode */}
      {!state.isTrainMode && (
        <div className="patch-study-footer-row">
          <div className="patch-study-footer-spacer" />
          <div className="patch-study-footer-box">
            <GameOutputBar game={game} />
          </div>
          <div className="patch-study-footer-spacer" />
        </div>
      )}

      {showTrainModal && (
        <TrainEntryModal
          onCancel={() => setShowTrainModal(false)}
          onConfirm={() => {
            setShowTrainModal(false);
            enterTrainMode();
          }}
        />
      )}

      {/* Send to Study 弹窗 */}
      {showPicker && (
        <StudyPickerModal
          currentTree={state.tree}
          onClose={() => setShowPicker(false)}
          onNavigate={handleSendNavigate}
        />
      )}
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
// Outer shell
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
