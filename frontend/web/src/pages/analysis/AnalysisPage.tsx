import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { StudyProvider, useStudy } from '@patch/studyContext';
import { StudyBoard } from '@patch/board/studyBoard';
import { MoveTree } from '@patch/sidebar/movetree';
import { createEmptyTree } from '@patch/tree/StudyTree';
import { importPgn } from '@patch/pgn/import';
import { ExplorerPanel } from '@patch/modules/explorer';
import { AnalysisSidebar } from './AnalysisSidebar';
import { StudyPickerModal } from './StudyPickerModal';
import { OutputPanel } from '@patch/commentbox/OutputPanel';
import { exportPgn } from '@patch/pgn/export';
import './analysis.css';

// ---- Location state 类型 ------------------------------------

interface GameContext {
  gameId: string;
  white: string;
  black: string;
  result: string | null;
  timeControl: { initial: number; increment: number };
  backUrl: string;
}

interface AnalysisLocationState {
  pgn?: string;
  gameContext?: GameContext;
}

// ---- 工具 ---------------------------------------------------

function formatTimeControl(initial: number, increment: number): string {
  const mins = Math.floor(initial / 60);
  const secs = initial % 60;
  const base = secs > 0 ? `${mins}:${String(secs).padStart(2, '0')}` : String(mins);
  return `${base}+${increment}`;
}

function resultLabel(result: string | null): { text: string; cls: string } {
  if (result === '1-0') return { text: '1-0', cls: 'analysis-game-result--white' };
  if (result === '0-1') return { text: '0-1', cls: 'analysis-game-result--black' };
  if (result === '1/2-1/2') return { text: '½-½', cls: 'analysis-game-result--draw' };
  return { text: '?', cls: '' };
}

// ---- Game Banner（仅从 /chess/:id/analyze 跳转时显示）------

function GameBanner({ ctx, onBack }: { ctx: GameContext; onBack: () => void }) {
  const res = resultLabel(ctx.result);
  return (
    <div className="analysis-game-banner">
      <button
        type="button"
        className="analysis-game-back"
        onClick={onBack}
        title="Back to game"
      >
        ← Back
      </button>

      <div className="analysis-game-players">
        <span className="analysis-game-player">
          <span className="analysis-game-piece analysis-game-piece--white">♔</span>
          {ctx.white}
        </span>
        <span className={`analysis-game-result ${res.cls}`}>{res.text}</span>
        <span className="analysis-game-player">
          <span className="analysis-game-piece analysis-game-piece--black">♚</span>
          {ctx.black}
        </span>
      </div>

      <span className="analysis-game-tc">
        {formatTimeControl(ctx.timeControl.initial, ctx.timeControl.increment)}
      </span>
    </div>
  );
}

// ---- 主内容层（必须在 StudyProvider 内）--------------------

function AnalysisPageContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { state, loadTree, addMove } = useStudy();

  const locState = (location.state ?? {}) as AnalysisLocationState;
  const pgn = locState.pgn;
  const gameContext = locState.gameContext;

  // Player filter passed in via URL: ?player=A&player=B
  const playerFilter = searchParams.getAll('player');
  const clearPlayerFilter = useCallback(() => {
    setSearchParams(new URLSearchParams());
  }, [setSearchParams]);

  const handleExportPgn = useCallback(() => {
    const { pgn } = exportPgn(state.tree, {}, {
      includeComments: true,
      includeNags: true,
      includeVariations: true,
    });
    const blob = new Blob([pgn], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'analysis.pgn';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [state.tree]);

  const [rightbarWidth, setRightbarWidth] = useState(280);
  const [isResizingRightbar, setIsResizingRightbar] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState<'tree' | 'explorer'>(
    playerFilter.length > 0 || searchParams.get('tab') === 'explorer' ? 'explorer' : 'tree',
  );
  const [boardWidth, setBoardWidth] = useState(500);
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const mainRef = useRef<HTMLDivElement | null>(null);

  const rightbarMin = 220;
  const rightbarMax = 520;

  // 加载树：有 pgn → importPgn；否则空棋盘
  useEffect(() => {
    if (pgn) {
      try {
        const result = importPgn(pgn);
        if (result.tree) {
          loadTree(result.tree);
          return;
        }
      } catch {
        // fall through to empty tree
      }
    }
    loadTree(createEmptyTree());
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);   // 只在 mount 时运行一次，pgn 通过 location.state 传入

  // 测量 main 列动态调整棋盘大小
  useEffect(() => {
    if (!mainRef.current) return;
    const measure = () => {
      const el = mainRef.current;
      if (!el) return;
      const NAV_HEIGHT = 42;
      const size = Math.min(el.clientWidth, el.clientHeight - NAV_HEIGHT);
      if (size > 0) setBoardWidth(Math.floor(size));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(mainRef.current);
    return () => ro.disconnect();
  }, []);

  // 右栏拖拽 resize
  useEffect(() => {
    if (!isResizingRightbar) return;
    const handlePointerMove = (e: PointerEvent) => {
      if (!layoutRef.current) return;
      const rect = layoutRef.current.getBoundingClientRect();
      const next = rect.right - e.clientX;
      setRightbarWidth(Math.min(rightbarMax, Math.max(rightbarMin, next)));
    };
    const handlePointerUp = () => setIsResizingRightbar(false);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingRightbar]);

  return (
    <div className="analysis-page">
      {/* ---- Header ---- */}
      <div className="analysis-header">
        <h2 className="analysis-title">
          {gameContext ? 'Game Analysis' : 'Analysis Board'}
        </h2>
        <div className="analysis-header-actions">
          <button
            type="button"
            className="analysis-send-btn"
            onClick={() => setShowPicker(true)}
          >
            Send to Study
          </button>
        </div>
      </div>

      {/* ---- Game Banner（仅分析对局时显示）---- */}
      {gameContext && (
        <GameBanner
          ctx={gameContext}
          onBack={() => navigate(gameContext.backUrl)}
        />
      )}

      {/* ---- 主布局 ---- */}
      <div className="analysis-layout" ref={layoutRef}>
        <div className="analysis-sidebar">
          <AnalysisSidebar />
        </div>

        <div className="analysis-main" ref={mainRef}>
          <StudyBoard boardWidth={boardWidth} />
        </div>

        <div
          className="analysis-splitter"
          onPointerDown={(e) => { e.preventDefault(); setIsResizingRightbar(true); }}
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize move tree panel"
        />

        <div className="analysis-rightbar" style={{ width: `${rightbarWidth}px` }}>
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
            </div>
            <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              {rightPanelTab === 'tree' ? (
                <MoveTree />
              ) : (
                <ExplorerPanel
                  fen={state.currentFen}
                  onMoveSelect={addMove}
                  playerFilter={playerFilter.length > 0 ? playerFilter : undefined}
                  onClearPlayerFilter={clearPlayerFilter}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ---- Output footer ---- */}
      <div className="analysis-footer">
        <OutputPanel
          exportActions={
            <button
              type="button"
              className="study-fen-button study-output-action-btn"
              onClick={handleExportPgn}
            >
              Export PGN
            </button>
          }
        />
      </div>

      {showPicker && (
        <StudyPickerModal
          currentTree={state.tree}
          onClose={() => setShowPicker(false)}
          onNavigate={(studyId) => navigate(`/patch/workspace/${studyId}`)}
        />
      )}
    </div>
  );
}

export function AnalysisPage() {
  return (
    <StudyProvider>
      <AnalysisPageContent />
    </StudyProvider>
  );
}

export default AnalysisPage;
