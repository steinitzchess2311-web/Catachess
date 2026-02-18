import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { StudyProvider, useStudy } from '@patch/studyContext';
import { StudyBoard } from '@patch/board/studyBoard';
import { MoveTree } from '@patch/sidebar/movetree';
import { createEmptyTree } from '@patch/tree/StudyTree';
import { AnalysisSidebar } from './AnalysisSidebar';
import { StudyPickerModal } from './StudyPickerModal';
import './analysis.css';

function AnalysisPageContent() {
  const navigate = useNavigate();
  const { state, loadTree } = useStudy();
  const [rightbarWidth, setRightbarWidth] = useState(280);
  const [isResizingRightbar, setIsResizingRightbar] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [boardWidth, setBoardWidth] = useState(500);
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const mainRef = useRef<HTMLDivElement | null>(null);

  const rightbarMin = 220;
  const rightbarMax = 520;

  // Bootstrap an empty local tree (no chapter ID → auto-save is skipped by context)
  useEffect(() => {
    loadTree(createEmptyTree());
  }, [loadTree]);

  // Measure main column to size board responsively
  useEffect(() => {
    if (!mainRef.current) return;
    const measure = () => {
      const el = mainRef.current;
      if (!el) return;
      const size = Math.min(el.clientWidth, el.clientHeight);
      if (size > 0) setBoardWidth(Math.floor(size));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(mainRef.current);
    return () => ro.disconnect();
  }, []);

  // Rightbar drag-resize
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
      <div className="analysis-header">
        <h2 className="analysis-title">Analysis Board</h2>
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
            <MoveTree />
          </div>
        </div>
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
