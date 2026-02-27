import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useExplorerPlayers, loadPlayersFromStorage } from './modules/explorer/hooks/useExplorerPlayers';
import { ChevronDownIcon, ChevronUpIcon } from '@radix-ui/react-icons';
import { StudyProvider, useStudy } from './studyContext';
import { StudyBoard } from './board/studyBoard';
import { MoveTree } from './sidebar/movetree';
import { ForkWidget } from './tree/Fork';
import { StudySidebar } from './sidebar/StudySidebar';
import { CommentBox } from './commentbox';
import { api } from '@ui/assets/api';
import { TerminalLauncher } from './modules/terminal';
import { StudyErrorBoundary } from './components/ErrorBoundary';
import { ExplorerPanel } from './modules/explorer';
import { useChapters } from './chapters/useChapters';
import { NewChapterModal } from './chapters/NewChapterModal';
import { TrainPanel, TrainEntryModal } from './modules/train';

export interface PatchStudyPageProps {
  className?: string;
}

interface Breadcrumb {
  id: string;
  title: string;
  nodeType: 'root' | 'folder' | 'study';
}

function StudyPageContent({ className }: PatchStudyPageProps) {
  const { id, topFolder } = useParams<{ id?: string; topFolder?: string }>();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { state, clearError, setError, loadStudy, saveTree, addMove, enterTrainMode, exitTrainMode } = useStudy();

  const {
    chapters,
    setChapters,
    pendingDeleteIds,
    hasPendingDeletes,
    loadChapterTree,
    handleSelectChapter,
    handleCreateChapter,
    handleRenameChapter,
    handleDeleteChapter,
    handleReorderChapters,
    processPendingDeletes,
    getNextChapterIndex,
    sortChapters,
    extractChapters,
  } = useChapters(id);

  const [searchParams, setSearchParams] = useSearchParams();
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

  const [headerExpanded, setHeaderExpanded] = useState(true);
  const [studyTitle, setStudyTitle] = useState<string>('');
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [rightbarWidth, setRightbarWidth] = useState<number>(280);
  const [rightPanelTab, setRightPanelTab] = useState<'tree' | 'explorer'>('tree');
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [isResizingRightbar, setIsResizingRightbar] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [draftTitle, setDraftTitle] = useState<string>('');
  const [titleError, setTitleError] = useState<string | null>(null);
  const [showNavigationWarning, setShowNavigationWarning] = useState(false);
  const [navigationTarget, setNavigationTarget] = useState<Breadcrumb | null>(null);
  const [isStudyDeleted, setIsStudyDeleted] = useState(false);
  const titleInputRef = useRef<HTMLInputElement | null>(null);
  const lastSavedAtRef = useRef<number | null>(state.lastSavedAt);
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const studyNodeRef = useRef<any>(null);

  const hasUnsavedChanges = state.isDirty || hasPendingDeletes;
  const savedTime = state.lastSavedAt ? new Date(state.lastSavedAt).toLocaleTimeString() : null;
  const savedLabel = state.isSaving
    ? 'Saving...'
    : hasUnsavedChanges
      ? 'Unsaved changes'
      : savedTime
        ? `Saved at ${savedTime}`
        : 'Unsaved changes';

  const rightbarMin = 220;
  const rightbarMax = 520;

  // ── Rightbar resize ──────────────────────────────────────────────────────
  const startRightbarResize = (event: React.PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsResizingRightbar(true);
  };

  useEffect(() => {
    if (!isResizingRightbar) return;
    const onMove = (event: PointerEvent) => {
      if (!layoutRef.current) return;
      const rect = layoutRef.current.getBoundingClientRect();
      const next = Math.min(rightbarMax, Math.max(rightbarMin, rect.right - event.clientX));
      setRightbarWidth(next);
    };
    const onUp = () => setIsResizingRightbar(false);
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
  }, [isResizingRightbar]);

  // ── Breadcrumb resolution ────────────────────────────────────────────────
  const resolveDisplayPath = useCallback(
    async (_path: string, fallbackTitle: string, studyId?: string): Promise<Breadcrumb[]> => {
      if (!studyId) {
        return [
          { id: 'root', title: 'root', nodeType: 'root' },
          { id: studyId || '', title: fallbackTitle || 'Study', nodeType: 'study' },
        ];
      }
      const crumbs: Breadcrumb[] = [];
      let currentId: string | null = studyId;
      let safety = 0;
      while (currentId && safety < 20) {
        safety += 1;
        const node = await api.get(`/api/v1/workspace/nodes/${currentId}`).catch(() => null);
        if (!node) break;
        if (typeof node.title === 'string' && node.title.length > 0) {
          crumbs.push({ id: node.id, title: node.title, nodeType: node.node_type });
        }
        currentId = node.parent_id || null;
      }
      if (crumbs.length === 0) {
        return [
          { id: 'root', title: 'root', nodeType: 'root' },
          { id: studyId, title: fallbackTitle || 'Study', nodeType: 'study' },
        ];
      }
      crumbs.reverse();
      if (crumbs[0]?.nodeType !== 'root') {
        crumbs.unshift({ id: 'root', title: 'root', nodeType: 'root' });
      }
      return crumbs;
    },
    []
  );

  // ── Study title editing ──────────────────────────────────────────────────
  const renameStudyNode = useCallback(async (newTitle: string) => {
    if (!id || !studyNodeRef.current) return;
    const trimmed = newTitle.trim();
    if (!trimmed) return;
    if (trimmed.includes('/')) { setTitleError('No "/" in study or folder name'); return; }
    const doRename = async (version: number) => {
      const response = await api.put(`/api/v1/workspace/nodes/${id}`, { title: trimmed, version });
      studyNodeRef.current = response;
      setStudyTitle(response.title);
      const resolved = await resolveDisplayPath('', response.title, id);
      setBreadcrumbs(resolved);
      return response;
    };
    try {
      await doRename(studyNodeRef.current.version);
    } catch (error: any) {
      if (error.message?.includes('Version conflict')) {
        try {
          const latest = await api.get(`/api/v1/workspace/nodes/${id}`);
          await doRename(latest.version);
        } catch {
          setTitleError('Rename failed. Please try again.');
          throw error;
        }
      } else {
        setTitleError('Rename failed. Please try again.');
        throw error;
      }
    }
  }, [id, resolveDisplayPath]);

  const startEditingTitle = useCallback(() => {
    setDraftTitle(studyTitle);
    setTitleError(null);
    setIsEditingTitle(true);
  }, [studyTitle]);

  const cancelEditingTitle = useCallback(() => {
    setIsEditingTitle(false);
    setDraftTitle('');
    setTitleError(null);
  }, []);

  const commitEditingTitle = useCallback(async () => {
    if (!draftTitle.trim() || draftTitle.trim() === studyTitle) { cancelEditingTitle(); return; }
    try { await renameStudyNode(draftTitle); cancelEditingTitle(); } catch {}
  }, [cancelEditingTitle, draftTitle, renameStudyNode, studyTitle]);

  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [isEditingTitle]);

  // ── Navigation ───────────────────────────────────────────────────────────
  const navigateToBreadcrumb = useCallback((crumb: Breadcrumb) => {
    const mode = pathname.startsWith('/workspace/private') ? 'private'
               : pathname.startsWith('/workspace/public') ? 'public'
               : pathname.startsWith('/workspace/shared') ? 'shared'
               : 'private';
    const base = topFolder ? `/workspace/${mode}/${topFolder}` : `/workspace/${mode}`;
    if (crumb.id === 'root') {
      navigate(base);
    } else {
      navigate(`${base}?parent=${crumb.id}`);
    }
  }, [navigate, pathname, topFolder]);

  const handleBreadcrumbClick = useCallback((crumb: Breadcrumb, index: number) => {
    if (index === breadcrumbs.length - 1) return;
    if (hasUnsavedChanges) { setNavigationTarget(crumb); setShowNavigationWarning(true); return; }
    navigateToBreadcrumb(crumb);
  }, [breadcrumbs.length, hasUnsavedChanges, navigateToBreadcrumb]);

  // ── Save ─────────────────────────────────────────────────────────────────
  const saveAll = useCallback(async () => {
    if (state.isSaving || !hasUnsavedChanges) return;
    try {
      const processImmediately = !state.isDirty;
      await saveTree();
      if (processImmediately && pendingDeleteIds.length > 0) {
        await processPendingDeletes(pendingDeleteIds);
      }
    } catch (e) {
      setError('SAVE_ERROR', e instanceof Error ? e.message : 'Failed to save changes');
    }
  }, [hasUnsavedChanges, pendingDeleteIds, processPendingDeletes, saveTree, setError, state.isDirty, state.isSaving]);

  useEffect(() => {
    if (!hasPendingDeletes || state.isSaving) return;
    const t = window.setTimeout(saveAll, 30000);
    return () => window.clearTimeout(t);
  }, [hasPendingDeletes, saveAll, state.isSaving]);

  useEffect(() => {
    if (!hasPendingDeletes) { lastSavedAtRef.current = state.lastSavedAt; return; }
    if (state.lastSavedAt && state.lastSavedAt !== lastSavedAtRef.current) {
      lastSavedAtRef.current = state.lastSavedAt;
      processPendingDeletes(pendingDeleteIds);
    }
  }, [hasPendingDeletes, pendingDeleteIds, processPendingDeletes, state.lastSavedAt]);

  // ── Initial study load ───────────────────────────────────────────────────
  useEffect(() => {
    if (!id) return;
    loadStudy(id);
    let cancelled = false;

    const load = async () => {
      try {
        const studyResponse = await api.get(`/api/v1/workspace/studies/${id}`);
        const resolvedTitle = studyResponse?.study?.title || studyResponse?.title || 'Study';
        setStudyTitle(resolvedTitle);

        const responseChapters = extractChapters(studyResponse);
        if (!Array.isArray(responseChapters)) throw new Error('API response unexpected: chapters list missing');
        let sorted = sortChapters(responseChapters);
        setChapters(sorted);

        Promise.all([
          resolveDisplayPath('', resolvedTitle, id),
          api.get(`/api/v1/workspace/nodes/${id}`).catch((e) => { console.warn('[STUDY PAGE] Failed to fetch study node:', e); return null; }),
        ]).then(([crumbs, studyNode]) => {
          if (cancelled) return;
          setBreadcrumbs(crumbs);
          if (studyNode) {
            studyNodeRef.current = studyNode;
            setIsStudyDeleted(!!studyNode.deleted_at);
          }
        });

        let chapter = sorted[0];
        if (!chapter) {
          try {
            chapter = await api.post(`/api/v1/workspace/studies/${id}/chapters`, { title: 'Chapter 1' });
          } catch {
            const retry = await api.get(`/api/v1/workspace/studies/${id}`);
            const retryTitle = retry?.study?.title || retry?.title || 'Study';
            setStudyTitle(retryTitle);
            const retryCrumbs = await resolveDisplayPath('', retryTitle, id);
            setBreadcrumbs(retryCrumbs);
            const retryChapters = extractChapters(retry);
            if (!Array.isArray(retryChapters)) throw new Error('Failed to load chapters');
            sorted = sortChapters(retryChapters);
            setChapters(sorted);
            chapter = sorted[0];
            if (!chapter) throw new Error('No chapters available');
          }
        }

        if (cancelled) return;
        await handleSelectChapter(chapter.id);
      } catch (e) {
        if (cancelled) return;
        setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to enter study');
      }
    };

    load();
    return () => { cancelled = true; };
  }, [extractChapters, id, loadChapterTree, loadStudy, resolveDisplayPath, setChapters, setError, sortChapters]);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className={`patch-study-page ${className || ''}`}>
      {isStudyDeleted && (
        <div style={{
          background: '#dc2626',
          color: '#fff',
          padding: '10px 20px',
          fontSize: '0.875rem',
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          zIndex: 100,
        }}>
          <span>🗑️</span>
          <span>This study is in the Recycle Bin. Please restore it before making any changes.</span>
          <a
            href="/workspace/trash"
            style={{ color: '#fff', textDecoration: 'underline', marginLeft: 'auto', whiteSpace: 'nowrap' }}
          >
            Go to Recycle Bin →
          </a>
        </div>
      )}
      <div className={`patch-study-header-wrap${headerExpanded ? '' : ' is-collapsed'}`}>
        <div className="patch-study-header">
          {isEditingTitle ? (
            <div className="patch-study-title-edit">
              <input
                ref={titleInputRef}
                type="text"
                className="patch-study-title-input"
                value={draftTitle}
                onChange={(e) => { setDraftTitle(e.target.value); if (!e.target.value.includes('/')) setTitleError(null); }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') { e.preventDefault(); commitEditingTitle(); }
                  if (e.key === 'Escape') { e.preventDefault(); cancelEditingTitle(); }
                }}
                onBlur={cancelEditingTitle}
              />
              {titleError && <span className="patch-study-title-error">{titleError}</span>}
            </div>
          ) : (
            <h2 className="patch-study-title" onDoubleClick={startEditingTitle} title="Double-click to rename">
              {studyTitle || 'Study'}
            </h2>
          )}
          <div className="patch-study-breadcrumb">
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={crumb.id}>
                {index > 0 && <span className="breadcrumb-separator">/</span>}
                {index === breadcrumbs.length - 1 ? (
                  <span className="breadcrumb-item current" title="Current study">{crumb.title}</span>
                ) : (
                  <button
                    type="button"
                    className="breadcrumb-item clickable"
                    onClick={() => handleBreadcrumbClick(crumb, index)}
                    title="Click to navigate"
                  >
                    {crumb.title}
                  </button>
                )}
              </React.Fragment>
            ))}
          </div>
          <div className="patch-study-actions">
            <button
              type="button"
              className="patch-study-save-button"
              onClick={saveAll}
              disabled={state.isSaving || !hasUnsavedChanges}
            >
              {state.isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save' : 'Saved'}
            </button>
          </div>
          <div className="patch-study-save-status">{savedLabel}</div>
        </div>
      </div>

      <div className="patch-study-toggle-bar">
        <button
          type="button"
          className="patch-study-toggle-btn"
          onClick={() => setHeaderExpanded(v => !v)}
          title={headerExpanded ? 'Collapse header' : 'Expand header'}
        >
          {headerExpanded ? <ChevronUpIcon width={14} height={14} /> : <ChevronDownIcon width={14} height={14} />}
        </button>
      </div>

      <div className={`patch-study-layout${state.isTrainMode ? ' is-train-mode' : ''}`} ref={layoutRef}>
        {!state.isTrainMode && (
          <div className="patch-study-sidebar">
            <StudySidebar
              chapters={chapters}
              currentChapterId={state.chapterId}
              onSelectChapter={handleSelectChapter}
              onCreateChapter={() => setIsCreateModalOpen(true)}
              onRenameChapter={handleRenameChapter}
              onDeleteChapter={handleDeleteChapter}
              onReorderChapters={handleReorderChapters}
            />
          </div>
        )}
        <div className="patch-study-main">
          <StudyBoard isLocked={state.isTrainMode} />
        </div>
        <div
          className="patch-study-splitter"
          onPointerDown={startRightbarResize}
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize move tree panel"
        />
        <div className="patch-study-rightbar" style={{ width: `${rightbarWidth}px` }}>
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
              {rightPanelTab === 'tree' && <ForkWidget />}
            </div>
          )}
        </div>
      </div>

      {!state.isTrainMode && (
        <div className="patch-study-footer-row">
          <div className="patch-study-footer-spacer" />
          <div className="patch-study-footer-box">
            <CommentBox />
          </div>
          <div className="patch-study-footer-spacer" />
        </div>
      )}

      {isCreateModalOpen && id && (
        <NewChapterModal
          studyId={id}
          nextChapterIndex={getNextChapterIndex()}
          chaptersCount={chapters.length}
          existingChapterIds={chapters.map((ch) => ch.id)}
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={(chapter) => setChapters((prev) => sortChapters([...prev, chapter]))}
          onMultiCreated={(newChapters) => setChapters((prev) => sortChapters([...prev, ...newChapters]))}
          onSelectChapter={handleSelectChapter}
        />
      )}

      {showNavigationWarning && navigationTarget && (
        <div className="patch-modal-overlay">
          <div className="patch-modal">
            <h3>Unsaved Changes</h3>
            <p>You have unsaved changes. Do you want to save before leaving?</p>
            <div className="patch-modal-actions">
              <button type="button" className="patch-modal-button" onClick={() => setShowNavigationWarning(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="patch-modal-button secondary"
                onClick={() => { setShowNavigationWarning(false); navigateToBreadcrumb(navigationTarget); }}
              >
                Don't Save
              </button>
              <button
                type="button"
                className="patch-modal-button primary"
                onClick={async () => { await saveAll(); navigateToBreadcrumb(navigationTarget); }}
              >
                Save &amp; Leave
              </button>
            </div>
          </div>
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

      <TerminalLauncher />
    </div>
  );
}

export function PatchStudyPage(props: PatchStudyPageProps) {
  return (
    <StudyErrorBoundary>
      <StudyProvider>
        <StudyPageContent {...props} />
      </StudyProvider>
    </StudyErrorBoundary>
  );
}

export default PatchStudyPage;
