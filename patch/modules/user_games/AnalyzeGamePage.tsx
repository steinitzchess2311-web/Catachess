// ============================================================
// AnalyzeGamePage — 赛后分析页
// 路由：/chess/:gameId/analyze
//
// 从 gameserver 拉 PGN → importPgn 解析 → 套 StudyProvider
// 复用 StudyBoard + MoveTree + Send to Study
// ============================================================

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { StudyProvider, useStudy } from '@patch/studyContext';
import { StudyBoard } from '@patch/board/studyBoard';
import { MoveTree } from '@patch/sidebar/movetree';
import { StudyPickerModal } from '@patch/components/StudyPickerModal';
import { fetchGamePgn } from './api';
import { importPgn } from '@patch/pgn/import';
import { createEmptyTree } from '@patch/tree/StudyTree';
import type { StudyTree } from '@patch/tree/type';

// ---- 内容层（必须在 StudyProvider 内）----------------------

function AnalyzeGameContent({ pgn }: { pgn: string }) {
  const { state, loadTree } = useStudy();
  const navigate = useNavigate();
  const layoutRef = useRef<HTMLDivElement>(null);
  const [rightbarWidth, setRightbarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [rightTab, setRightTab] = useState<'moves' | 'analysis'>('moves');

  const rightbarMin = 220;
  const rightbarMax = 520;

  // 解析 PGN → 加载进 study context
  useEffect(() => {
    if (!pgn) {
      loadTree(createEmptyTree());
      return;
    }
    try {
      const result = importPgn(pgn);
      if (result.tree) {
        loadTree(result.tree);
      } else {
        loadTree(createEmptyTree());
      }
    } catch {
      loadTree(createEmptyTree());
    }
  }, [pgn, loadTree]);

  // 右侧栏拖拽 resize
  useEffect(() => {
    if (!isResizing) return;
    const onMove = (e: PointerEvent) => {
      if (!layoutRef.current) return;
      const rect = layoutRef.current.getBoundingClientRect();
      setRightbarWidth(
        Math.min(rightbarMax, Math.max(rightbarMin, rect.right - e.clientX)),
      );
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

  // Send to Study 跳转
  const handleSendNavigate = useCallback(
    (studyId: string) => {
      navigate(`/workspace/private/${studyId}`);
    },
    [navigate],
  );

  return (
    <div className="patch-study-page">
      <div className="patch-study-layout" ref={layoutRef}>
        {/* 棋盘 */}
        <div className="patch-study-main">
          <StudyBoard />
        </div>

        {/* 拖拽分隔线 */}
        <div
          className="patch-study-splitter"
          onPointerDown={(e) => { e.preventDefault(); setIsResizing(true); }}
          role="separator"
          aria-orientation="vertical"
        />

        {/* 右侧：走法列表 */}
        <div className="patch-study-rightbar" style={{ width: rightbarWidth }}>
          <div className="patch-right-panel">
            <div className="patch-sidebar-tabs">
              <button
                type="button"
                className={`patch-sidebar-tab${rightTab === 'moves' ? ' is-active' : ''}`}
                onClick={() => setRightTab('moves')}
              >
                Moves
              </button>
              <button
                type="button"
                className={`patch-sidebar-tab${rightTab === 'analysis' ? ' is-active' : ''}`}
                onClick={() => setRightTab('analysis')}
              >
                Analysis
              </button>
              {/* Send to Study 入口 */}
              <button
                type="button"
                className="patch-sidebar-tab analysis-send-btn"
                onClick={() => setShowPicker(true)}
                title="Save this game to a study chapter"
              >
                Save to Study
              </button>
            </div>
            <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              {rightTab === 'moves' ? <MoveTree /> : null}
            </div>
          </div>
        </div>
      </div>

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

// ---- 加载状态 -----------------------------------------------

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
    <div className="game-viewer-loading">
      <p style={{ color: '#888', fontSize: 14 }}>{message}</p>
    </div>
  );
}

// ---- 页面入口 -----------------------------------------------

export function AnalyzeGamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [pgn, setPgn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) return;
    fetchGamePgn(gameId)
      .then(setPgn)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load game'));
  }, [gameId]);

  if (error) return <ErrorScreen message={error} />;
  if (pgn === null) return <LoadingScreen />;

  return (
    <StudyProvider>
      <AnalyzeGameContent pgn={pgn} />
    </StudyProvider>
  );
}
