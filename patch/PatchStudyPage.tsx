import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { StudyProvider, useStudy } from './studyContext';
import { StudyBoard } from './board/studyBoard';
import { MoveTree } from './sidebar/movetree';
import { StudySidebar } from './sidebar/StudySidebar';
import { CommentBox } from './CommentBox';
import { api } from '@ui/assets/api';
import { createEmptyTree } from './tree/StudyTree';
import { TREE_SCHEMA_VERSION } from './tree/type';
import { TerminalLauncher } from './modules/terminal';

export interface PatchStudyPageProps {
  className?: string;
}

function StudyPageContent({ className }: PatchStudyPageProps) {
  const { id } = useParams<{ id: string }>();
  const { state, clearError, setError, selectChapter, loadTree, saveTree } = useStudy();
  const [chapters, setChapters] = useState<any[]>([]);
  const [studyTitle, setStudyTitle] = useState<string>('');
  const [displayPath, setDisplayPath] = useState<string>('root');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreatingChapter, setIsCreatingChapter] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createTitle, setCreateTitle] = useState<string>('');
  const [createTitleError, setCreateTitleError] = useState<string | null>(null);
  const [rightbarWidth, setRightbarWidth] = useState<number>(280);
  const [isResizingRightbar, setIsResizingRightbar] = useState(false);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<string[]>([]);
  const [pendingDeleteChapters, setPendingDeleteChapters] = useState<Array<{ id: string; order?: number }>>([]);
  const createTitleInputRef = useRef<HTMLInputElement | null>(null);
  const lastSavedAtRef = useRef<number | null>(state.lastSavedAt);
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const hasPendingDeletes = pendingDeleteIds.length > 0;
  const hasUnsavedChanges = state.isDirty || hasPendingDeletes;
  const savedTime = state.lastSavedAt ? new Date(state.lastSavedAt).toLocaleTimeString() : null;
  const savedLabel = state.isSaving
    ? 'Saving...'
    : hasUnsavedChanges
      ? 'Unsaved changes'
      : savedTime
        ? `Saved at ${savedTime}`
        : 'Unsaved changes';

  const patchBase = '/api/v1/workspace/studies/study-patch';
  const rightbarMin = 220;
  const rightbarMax = 520;

  const startRightbarResize = (event: React.PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsResizingRightbar(true);
  };

  useEffect(() => {
    if (!isResizingRightbar) return;
    const handlePointerMove = (event: PointerEvent) => {
      if (!layoutRef.current) return;
      const rect = layoutRef.current.getBoundingClientRect();
      const nextWidth = rect.right - event.clientX;
      const clamped = Math.min(rightbarMax, Math.max(rightbarMin, nextWidth));
      setRightbarWidth(clamped);
    };
    const handlePointerUp = () => {
      setIsResizingRightbar(false);
    };
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

  const resolveDisplayPath = useCallback(
    async (_path: string, fallbackTitle: string, studyId?: string) => {
      if (!studyId) return `root/${fallbackTitle || 'Study'}`;
      const titles: string[] = [];
      let currentId: string | null = studyId;
      let safety = 0;

      while (currentId && safety < 20) {
        safety += 1;
        const node = await api.get(`/api/v1/workspace/nodes/${currentId}`).catch(() => null);
        if (!node) break;
        if (typeof node.title === 'string' && node.title.length > 0) {
          titles.push(node.title);
        }
        currentId = node.parent_id || null;
      }

      if (titles.length === 0) {
        return `root/${fallbackTitle || 'Study'}`;
      }

      return `root/${titles.reverse().join('/')}`;
    },
    []
  );

  const extractChapters = useCallback((response: any) => {
    return response?.chapters || response?.study?.chapters || response?.data?.chapters;
  }, []);

  const getSortValue = useCallback((ch: any, key: string) => {
    const value = ch?.[key];
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = Date.parse(value);
      if (!Number.isNaN(parsed)) return parsed;
      return value;
    }
    return null;
  }, []);

  const sortChapters = useCallback((items: any[]) => {
    return [...items].sort((a, b) => {
      const orderA = getSortValue(a, 'order');
      const orderB = getSortValue(b, 'order');
      if (orderA !== null || orderB !== null) {
        if (orderA === null) return 1;
        if (orderB === null) return -1;
        return orderA < orderB ? -1 : orderA > orderB ? 1 : 0;
      }

      console.warn('[patch] Chapter order missing, falling back to created_at/id.');
      const createdA = getSortValue(a, 'created_at');
      const createdB = getSortValue(b, 'created_at');
      if (createdA !== null || createdB !== null) {
        if (createdA === null) return 1;
        if (createdB === null) return -1;
        return createdA < createdB ? -1 : createdA > createdB ? 1 : 0;
      }

      const idA = `${a?.id ?? ''}`;
      const idB = `${b?.id ?? ''}`;
      return idA.localeCompare(idB);
    });
  }, [getSortValue]);

  const getNextChapterIndex = useCallback(() => {
    const orders = [
      ...chapters.map((chapter) => (typeof chapter.order === 'number' ? chapter.order : null)),
      ...pendingDeleteChapters.map((chapter) => (typeof chapter.order === 'number' ? chapter.order : null)),
    ].filter((value): value is number => typeof value === 'number');
    const maxOrder = orders.length > 0 ? Math.max(...orders) : -1;
    return maxOrder + 2;
  }, [chapters, pendingDeleteChapters]);

  const loadChapterTree = useCallback(async (chapterId: string) => {
    selectChapter(chapterId);

    try {
      const treeResponse = await api.get(`${patchBase}/chapter/${chapterId}/tree`);
      if (treeResponse?.success && treeResponse.tree) {
        if (!treeResponse.tree.version) {
          console.warn(`[patch] Tree missing version for chapter ${chapterId}, will re-save.`);
          const upgradedTree = { ...treeResponse.tree, version: TREE_SCHEMA_VERSION };
          await api.put(`${patchBase}/chapter/${chapterId}/tree`, upgradedTree);
          loadTree(upgradedTree);
          return;
        }
        loadTree(treeResponse.tree);
        return;
      }
    } catch (e) {
      console.warn(`[patch] Tree load failed for chapter ${chapterId}, initializing empty tree.`);
    }

    const emptyTree = createEmptyTree();
    const createResponse = await api.put(`${patchBase}/chapter/${chapterId}/tree`, emptyTree);
    if (!createResponse?.success) {
      throw new Error(createResponse?.error || 'Failed to initialize tree');
    }
    loadTree(emptyTree);
  }, [loadTree, patchBase, selectChapter]);

  const handleSelectChapter = useCallback(async (chapterId: string) => {
    try {
      await loadChapterTree(chapterId);
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to load chapter');
    }
  }, [loadChapterTree, setError]);

  const handleCreateChapter = useCallback(async (title: string) => {
    if (!id) return;
    try {
      const chapter = await api.post(`/api/v1/workspace/studies/${id}/chapters`, { title });
      const nextChapters = sortChapters([...chapters, chapter]);
      setChapters(nextChapters);
      if (chapter?.id) {
        await loadChapterTree(chapter.id);
      }
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to create chapter');
    }
  }, [chapters, id, loadChapterTree, setError, sortChapters]);

  const handleRenameChapter = useCallback(async (chapterId: string, title: string) => {
    if (!id) return;
    try {
      const updated = await api.put(`/api/v1/workspace/studies/${id}/chapters/${chapterId}`, { title });
      setChapters((prev) => {
        const next = prev.map((chapter) =>
          chapter.id === chapterId ? { ...chapter, title: updated?.title || title } : chapter
        );
        return sortChapters(next);
      });
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to rename chapter');
      throw e;
    }
  }, [id, setError, sortChapters]);

  const processPendingDeletes = useCallback(async (deleteIds: string[]) => {
    if (!id || deleteIds.length === 0) return;
    try {
      await Promise.all(
        deleteIds.map((chapterId) =>
          api.delete(`/api/v1/workspace/studies/${id}/chapters/${chapterId}`)
        )
      );
      setPendingDeleteIds((prev) => prev.filter((chapterId) => !deleteIds.includes(chapterId)));
      setPendingDeleteChapters((prev) => prev.filter((chapter) => !deleteIds.includes(chapter.id)));
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to delete chapter');
      throw e;
    }
  }, [id, setError]);

  const handleDeleteChapter = useCallback(async (chapterId: string) => {
    if (!id) return;
    try {
      const deletedChapter = chapters.find((chapter) => chapter.id === chapterId);
      const remaining = chapters.filter((chapter) => chapter.id !== chapterId);
      setPendingDeleteIds((prev) => (prev.includes(chapterId) ? prev : [...prev, chapterId]));
      if (deletedChapter) {
        setPendingDeleteChapters((prev) => (prev.some((item) => item.id === chapterId) ? prev : [...prev, deletedChapter]));
      }
      setChapters(sortChapters(remaining));
      if (state.chapterId === chapterId) {
        const nextChapter = sortChapters(remaining)[0];
        if (nextChapter) {
          await loadChapterTree(nextChapter.id);
        }
      }
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to delete chapter');
      throw e;
    }
  }, [chapters, id, loadChapterTree, setError, state.chapterId]);

  const openCreateModal = useCallback(() => {
    setCreateError(null);
    setCreateTitleError(null);
    const nextIndex = getNextChapterIndex();
    setCreateTitle(`Chapter ${nextIndex}`);
    setIsCreateModalOpen(true);
  }, [getNextChapterIndex]);

  const closeCreateModal = useCallback(() => {
    if (isCreatingChapter) return;
    setIsCreateModalOpen(false);
  }, [isCreatingChapter]);

  const confirmCreateChapter = useCallback(async () => {
    if (isCreatingChapter) return;
    setCreateError(null);
    const fallbackTitle = `Chapter ${getNextChapterIndex()}`;
    const nextTitle = createTitle.trim() || fallbackTitle;
    if (nextTitle.includes('/')) {
      setCreateTitleError('No "/" in study or folder name');
      return;
    }
    setIsCreatingChapter(true);
    try {
      await handleCreateChapter(nextTitle);
      setIsCreateModalOpen(false);
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : 'Failed to create chapter');
    } finally {
      setIsCreatingChapter(false);
    }
  }, [createTitle, getNextChapterIndex, handleCreateChapter, isCreatingChapter]);

  useEffect(() => {
    if (isCreateModalOpen && createTitleInputRef.current) {
      createTitleInputRef.current.focus();
      createTitleInputRef.current.select();
    }
  }, [isCreateModalOpen]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    const resolveChapterAndTree = async () => {
      try {
        const studyResponse = await api.get(`/api/v1/workspace/studies/${id}`);
        const resolvedTitle =
          studyResponse?.study?.title || studyResponse?.title || 'Study';
        setStudyTitle(resolvedTitle);
        const resolvedDisplayPath = await resolveDisplayPath('', resolvedTitle, id);
        setDisplayPath(resolvedDisplayPath);
        const responseChapters = extractChapters(studyResponse);
        if (!Array.isArray(responseChapters)) {
          throw new Error('API response unexpected: chapters list missing');
        }

        let sortedChapters = sortChapters(responseChapters);
        setChapters(sortedChapters);

        let chapter = sortedChapters[0];

        if (!chapter) {
          try {
            chapter = await api.post(`/api/v1/workspace/studies/${id}/chapters`, {
              title: 'Chapter 1',
            });
          } catch (createError) {
        const retryResponse = await api.get(`/api/v1/workspace/studies/${id}`);
        const retryTitle =
          retryResponse?.study?.title || retryResponse?.title || 'Study';
        setStudyTitle(retryTitle);
        const retryDisplayPath = await resolveDisplayPath('', retryTitle, id);
        setDisplayPath(retryDisplayPath);
        const retryChapters = extractChapters(retryResponse);

            if (!Array.isArray(retryChapters)) {
              throw createError;
            }

            sortedChapters = sortChapters(retryChapters);
            setChapters(sortedChapters);
            chapter = sortedChapters[0];
            if (!chapter) {
              throw createError;
            }
          }
        }

        if (cancelled) return;
        await loadChapterTree(chapter.id);
      } catch (e) {
        if (cancelled) return;
        setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to enter study');
      }
    };

    resolveChapterAndTree();

    return () => {
      cancelled = true;
    };
  }, [extractChapters, id, loadChapterTree, resolveDisplayPath, setError, sortChapters]);

  const saveAll = useCallback(async () => {
    if (state.isSaving) return;
    if (!hasUnsavedChanges) return;
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
    const timeoutId = window.setTimeout(() => {
      saveAll();
    }, 30000);
    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [hasPendingDeletes, saveAll, state.isSaving]);

  useEffect(() => {
    if (!hasPendingDeletes) {
      lastSavedAtRef.current = state.lastSavedAt;
      return;
    }
    if (state.lastSavedAt && state.lastSavedAt !== lastSavedAtRef.current) {
      lastSavedAtRef.current = state.lastSavedAt;
      processPendingDeletes(pendingDeleteIds);
    }
  }, [hasPendingDeletes, pendingDeleteIds, processPendingDeletes, state.lastSavedAt]);

  return (
    <div className={`patch-study-page ${className || ''}`}>
      <div className="patch-study-header">
        <h2>{studyTitle || 'Study'}</h2>
        <p className="patch-study-notice">
          {displayPath}
        </p>
        <div className="patch-study-actions">
          <button
            type="button"
            className="patch-study-save-button"
            onClick={saveAll}
            disabled={state.isSaving || !hasUnsavedChanges}
          >
            {state.isSaving ? 'Saving...' : (hasUnsavedChanges ? 'Save' : 'Saved')}
          </button>
        </div>
        <div className="patch-study-save-status">{savedLabel}</div>
      </div>
      <div className="patch-study-layout" style={{ height: '600px' }} ref={layoutRef}>
        <div className="patch-study-sidebar">
          <StudySidebar
            chapters={chapters}
            currentChapterId={state.chapterId}
            onSelectChapter={handleSelectChapter}
            onCreateChapter={openCreateModal}
            onRenameChapter={handleRenameChapter}
            onDeleteChapter={handleDeleteChapter}
          />
        </div>
        <div className="patch-study-main">
          <StudyBoard />
        </div>
        <div
          className="patch-study-splitter"
          onPointerDown={startRightbarResize}
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize move tree panel"
        />
        <div className="patch-study-rightbar" style={{ width: `${rightbarWidth}px` }}>
          <div className="patch-right-panel">
            <MoveTree />
          </div>
        </div>
      </div>
      <div className="patch-study-footer-row">
        <div className="patch-study-footer-spacer" />
        <div className="patch-study-footer-box">
          <CommentBox />
        </div>
        <div className="patch-study-footer-spacer" />
      </div>
      {isCreateModalOpen && (
        <div className="patch-modal-overlay" role="dialog" aria-modal="true">
          <div className="patch-modal">
            <h3>Create new chapter?</h3>
            <p>This will add a new chapter to the current study.</p>
            <input
              ref={createTitleInputRef}
              className="patch-modal-input"
              value={createTitle}
              onChange={(event) => {
                const nextValue = event.target.value;
                setCreateTitle(nextValue);
                if (!nextValue.includes('/')) {
                  setCreateTitleError(null);
                }
              }}
              onFocus={(event) => {
                event.target.select();
              }}
            />
            {createTitleError && <div className="patch-modal-error">{createTitleError}</div>}
            {createError && <div className="patch-modal-error">{createError}</div>}
            <div className="patch-modal-actions">
              <button
                type="button"
                className="patch-modal-button"
                onClick={closeCreateModal}
                disabled={isCreatingChapter}
              >
                Cancel
              </button>
              <button
                type="button"
                className="patch-modal-button primary"
                onClick={confirmCreateChapter}
                disabled={isCreatingChapter}
              >
                {isCreatingChapter ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
      <TerminalLauncher />
    </div>
  );
}

export function PatchStudyPage(props: PatchStudyPageProps) {
  return (
    <StudyProvider>
      <StudyPageContent {...props} />
    </StudyProvider>
  );
}

export default PatchStudyPage;
