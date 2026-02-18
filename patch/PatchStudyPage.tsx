import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StudyProvider, useStudy } from './studyContext';
import { StudyBoard } from './board/studyBoard';
import { MoveTree } from './sidebar/movetree';
import { StudySidebar } from './sidebar/StudySidebar';
import { CommentBox } from './CommentBox';
import { api } from '@ui/assets/api';
import { createEmptyTree } from './tree/StudyTree';
import { TREE_SCHEMA_VERSION } from './tree/type';
import { TerminalLauncher } from './modules/terminal';
import { ExplorerPanel } from './modules/explorer';
import { importMultiPgn } from './pgn/import';

function pgnGameTitle(headers: Record<string, string>): string {
  const white = headers['White'] ?? '?';
  const black = headers['Black'] ?? '?';
  const event = headers['Event'] ?? '';
  if (white === '?' && black === '?' && !event) return 'Imported Game';
  const players = white === '?' && black === '?' ? '' : `${white} vs ${black}`;
  return [players, event].filter(Boolean).join(' – ');
}

export interface PatchStudyPageProps {
  className?: string;
}

interface Breadcrumb {
  id: string;
  title: string;
  nodeType: 'root' | 'folder' | 'study';
}

function StudyPageContent({ className }: PatchStudyPageProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { state, clearError, setError, selectChapter, loadTree, saveTree, loadStudy, addMove } = useStudy();
  const [chapters, setChapters] = useState<any[]>([]);
  const [studyTitle, setStudyTitle] = useState<string>('');
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreatingChapter, setIsCreatingChapter] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createTitle, setCreateTitle] = useState<string>('');
  const [createTitleError, setCreateTitleError] = useState<string | null>(null);
  const [createFen, setCreateFen] = useState<string>('');
  const [createMode, setCreateMode] = useState<'empty' | 'fen' | 'pgn'>('empty');
  const [createPgnText, setCreatePgnText] = useState('');
  const [createPgnParsed, setCreatePgnParsed] = useState<ReturnType<typeof importMultiPgn> | null>(null);
  const [createPgnImporting, setCreatePgnImporting] = useState(false);
  const createPgnFileRef = useRef<HTMLInputElement | null>(null);
  const [rightbarWidth, setRightbarWidth] = useState<number>(280);
  const [rightPanelTab, setRightPanelTab] = useState<'tree' | 'explorer'>('tree');
  const [isResizingRightbar, setIsResizingRightbar] = useState(false);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<string[]>([]);
  const [pendingDeleteChapters, setPendingDeleteChapters] = useState<Array<{ id: string; order?: number }>>([]);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [draftTitle, setDraftTitle] = useState<string>('');
  const [titleError, setTitleError] = useState<string | null>(null);
  const [showNavigationWarning, setShowNavigationWarning] = useState(false);
  const [navigationTarget, setNavigationTarget] = useState<Breadcrumb | null>(null);
  const createTitleInputRef = useRef<HTMLInputElement | null>(null);
  const titleInputRef = useRef<HTMLInputElement | null>(null);
  const lastSavedAtRef = useRef<number | null>(state.lastSavedAt);
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const studyNodeRef = useRef<any>(null);
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
          crumbs.push({
            id: node.id,
            title: node.title,
            nodeType: node.node_type,
          });
        }
        currentId = node.parent_id || null;
      }

      if (crumbs.length === 0) {
        return [
          { id: 'root', title: 'root', nodeType: 'root' },
          { id: studyId, title: fallbackTitle || 'Study', nodeType: 'study' },
        ];
      }

      // Reverse to get root -> ... -> study order
      crumbs.reverse();

      // Add root at the beginning if not already present
      if (crumbs[0]?.nodeType !== 'root') {
        crumbs.unshift({ id: 'root', title: 'root', nodeType: 'root' });
      }

      return crumbs;
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

  const applyChapterOrder = useCallback((items: any[], order: string[]) => {
    const byId = new Map(items.map((chapter) => [chapter.id, chapter]));
    const ordered: any[] = [];
    order.forEach((chapterId, index) => {
      const chapter = byId.get(chapterId);
      if (!chapter) return;
      ordered.push({ ...chapter, order: index });
    });
    const known = new Set(order);
    items.forEach((chapter, index) => {
      if (known.has(chapter.id)) return;
      ordered.push({ ...chapter, order: order.length + index });
    });
    return ordered;
  }, []);

  const getNextChapterIndex = useCallback(() => {
    const orders = [
      ...chapters.map((chapter) => (typeof chapter.order === 'number' ? chapter.order : null)),
      ...pendingDeleteChapters.map((chapter) => (typeof chapter.order === 'number' ? chapter.order : null)),
    ].filter((value): value is number => typeof value === 'number');
    const maxOrder = orders.length > 0 ? Math.max(...orders) : -1;
    return maxOrder + 2;
  }, [chapters, pendingDeleteChapters]);

  const loadChapterTree = useCallback(async (chapterId: string, retryCount = 0) => {
    const maxRetries = 3;
    const retryDelay = 500; // ms

    try {
      const treeResponse = await api.get(`${patchBase}/chapter/${chapterId}/tree`);

      if (treeResponse?.success && treeResponse.tree) {
        const startFen = treeResponse.starting_fen || undefined;

        if (!treeResponse.tree.version) {
          console.warn(`[patch] Tree missing version for chapter ${chapterId}, will re-save.`);
          const upgradedTree = { ...treeResponse.tree, version: TREE_SCHEMA_VERSION };
          await api.put(`${patchBase}/chapter/${chapterId}/tree`, upgradedTree);
          loadTree(upgradedTree, startFen);
          return;
        }
        loadTree(treeResponse.tree, startFen);
        return;
      }

      // Retry if R2 storage hasn't propagated yet
      if (retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        return loadChapterTree(chapterId, retryCount + 1);
      }

      console.warn(`[patch] Tree not found after ${maxRetries} retries for chapter ${chapterId}, initializing empty tree`);
    } catch (e) {
      console.warn(`[patch] Tree load failed for chapter ${chapterId}, initializing empty tree.`, e);
    }

    // Initialize empty tree for new chapter
    const emptyTree = createEmptyTree();
    const createResponse = await api.put(`${patchBase}/chapter/${chapterId}/tree`, emptyTree);
    if (!createResponse?.success) {
      throw new Error(createResponse?.error || 'Failed to initialize tree');
    }
    loadTree(emptyTree);
  }, [loadTree, patchBase]);

  const handleSelectChapter = useCallback(async (chapterId: string) => {
    selectChapter(chapterId); // instant optimistic update — board resets, chapter highlighted immediately
    try {
      await loadChapterTree(chapterId);
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to load chapter');
    }
  }, [loadChapterTree, selectChapter, setError]);

  const handleCreateChapter = useCallback(async (title: string) => {
    if (!id) return;
    try {
      const chapter = await api.post(`/api/v1/workspace/studies/${id}/chapters`, { title });
      const nextChapters = sortChapters([...chapters, chapter]);
      setChapters(nextChapters);
      if (chapter?.id) {
        selectChapter(chapter.id);
        await loadChapterTree(chapter.id);
      }
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to create chapter');
    }
  }, [chapters, id, loadChapterTree, selectChapter, setError, sortChapters]);


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

  const renameStudyNode = useCallback(async (newTitle: string) => {
    if (!id || !studyNodeRef.current) return;

    const trimmed = newTitle.trim();
    if (!trimmed) return;
    if (trimmed.includes('/')) {
      setTitleError('No "/" in study or folder name');
      return;
    }

    try {
      console.log(`[STUDY RENAME] Attempting to rename study | study_id=${id} | new_title=${trimmed} | version=${studyNodeRef.current.version}`);

      const response = await api.put(`/api/v1/workspace/nodes/${id}`, {
        title: trimmed,
        version: studyNodeRef.current.version,
      });

      // Update local state
      studyNodeRef.current = response;
      setStudyTitle(response.title);

      // Update breadcrumbs
      const resolvedBreadcrumbs = await resolveDisplayPath('', response.title, id);
      setBreadcrumbs(resolvedBreadcrumbs);

      console.log(`[STUDY RENAME] ✓ Success | new_title=${response.title} | new_version=${response.version}`);

    } catch (error: any) {
      // Handle version conflict by fetching latest version and retrying
      if (error.message && error.message.includes('Version conflict')) {
        try {
          console.log(`[STUDY RENAME] Version conflict detected, fetching latest version for study ${id}`);
          const latestNode = await api.get(`/api/v1/workspace/nodes/${id}`);
          const retryResponse = await api.put(`/api/v1/workspace/nodes/${id}`, {
            title: trimmed,
            version: latestNode.version,
          });

          studyNodeRef.current = retryResponse;
          setStudyTitle(retryResponse.title);

          const resolvedBreadcrumbs = await resolveDisplayPath('', retryResponse.title, id);
          setBreadcrumbs(resolvedBreadcrumbs);

          console.log(`[STUDY RENAME] ✓ Success after retry | new_title=${retryResponse.title} | new_version=${retryResponse.version}`);

        } catch (retryError) {
          console.error('[STUDY RENAME] Failed after retry:', retryError);
          setTitleError('Rename failed. Please try again.');
          throw retryError;
        }
      } else {
        console.error('[STUDY RENAME] Failed:', error);
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
    if (!draftTitle.trim() || draftTitle.trim() === studyTitle) {
      cancelEditingTitle();
      return;
    }

    try {
      await renameStudyNode(draftTitle);
      cancelEditingTitle();
    } catch (e) {
      // Error already handled in renameStudyNode
    }
  }, [draftTitle, studyTitle, renameStudyNode, cancelEditingTitle]);

  const navigateToBreadcrumb = useCallback((crumb: Breadcrumb) => {
    if (crumb.id === 'root') {
      navigate('/workspace-select');
    } else {
      navigate(`/workspace-select?parent=${crumb.id}`);
    }
  }, [navigate]);

  const handleBreadcrumbDoubleClick = useCallback((crumb: Breadcrumb, index: number) => {
    // Last item (current study) is not clickable
    if (index === breadcrumbs.length - 1) {
      return;
    }

    // Check for unsaved changes
    if (hasUnsavedChanges) {
      setNavigationTarget(crumb);
      setShowNavigationWarning(true);
      return;
    }

    // Navigate directly
    navigateToBreadcrumb(crumb);
  }, [breadcrumbs.length, hasUnsavedChanges, navigateToBreadcrumb]);

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

  const handleReorderChapters = useCallback(
    async (
      order: string[],
      _context: { draggedId: string; targetId: string; placement: 'before' | 'after' }
    ) => {
      if (!id) return;
      const previous = chapters;
      const next = applyChapterOrder(previous, order);
      setChapters(next);
      try {
        const response = await api.post(`/api/v1/workspace/studies/${id}/chapters/reorder`, {
          order,
        });
        if (Array.isArray(response)) {
          setChapters(sortChapters(response));
        }
      } catch (e) {
        setChapters(previous);
        setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to reorder chapters');
      }
    },
    [applyChapterOrder, chapters, id, setChapters, setError, sortChapters]
  );

  const openCreateModal = useCallback(() => {
    setCreateError(null);
    setCreateTitleError(null);
    const nextIndex = getNextChapterIndex();
    setCreateTitle(`Chapter ${nextIndex}`);
    setCreateMode('empty');
    setCreateFen('');
    setCreatePgnText('');
    setCreatePgnParsed(null);
    setIsCreateModalOpen(true);
  }, [getNextChapterIndex]);

  const closeCreateModal = useCallback(() => {
    if (isCreatingChapter || createPgnImporting) return;
    setIsCreateModalOpen(false);
    setCreatePgnText('');
    setCreatePgnParsed(null);
  }, [isCreatingChapter, createPgnImporting]);

  const handlePgnFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      if (content) setCreatePgnText(content);
    };
    reader.readAsText(file);
    e.target.value = '';
  }, []);

  const confirmCreateChapter = useCallback(async () => {
    if (isCreatingChapter || createPgnImporting) return;
    setCreateError(null);

    // ── PGN mode ──────────────────────────────────────────────────────────
    if (createMode === 'pgn') {
      if (!createPgnParsed || createPgnParsed.games.length === 0 || !id) return;
      setCreatePgnImporting(true);
      const errs: string[] = [];
      let firstChapterId: string | null = null;
      let addedChapters: any[] = [];
      try {
        for (const game of createPgnParsed.games) {
          const title = pgnGameTitle(game.headers);
          let chapterId: string | null = null;
          try {
            if (game.startingFen) {
              const resp = await api.post('/api/v1/import-export/fen/import', {
                study_id: id,
                chapter_title: title,
                fen: game.startingFen,
              });
              chapterId = resp?.chapter_id ?? null;
              if (chapterId) addedChapters.push({ id: chapterId, title, order: chapters.length + addedChapters.length });
            } else {
              const resp = await api.post(`/api/v1/workspace/studies/${id}/chapters`, { title });
              chapterId = resp?.id ?? null;
              if (chapterId) addedChapters.push({ id: chapterId, title, order: chapters.length + addedChapters.length });
            }
          } catch (e) {
            errs.push(`Failed to create "${title}": ${e instanceof Error ? e.message : 'error'}`);
            continue;
          }
          if (!chapterId) { errs.push(`Could not get chapter ID for "${title}"`); continue; }
          if (!firstChapterId) firstChapterId = chapterId;
          try {
            await api.put(`/api/v1/workspace/studies/study-patch/chapter/${chapterId}/tree`, game.tree);
          } catch (e) {
            errs.push(`Failed to save tree for "${title}": ${e instanceof Error ? e.message : 'error'}`);
          }
        }
      } finally {
        setCreatePgnImporting(false);
      }
      if (errs.length > 0) { setCreateError(errs.join('\n')); return; }
      if (addedChapters.length > 0) {
        setChapters((prev) => sortChapters([...prev, ...addedChapters]));
      }
      if (firstChapterId) await loadChapterTree(firstChapterId);
      setIsCreateModalOpen(false);
      setCreatePgnText('');
      setCreatePgnParsed(null);
      return;
    }

    // ── Empty / FEN mode ──────────────────────────────────────────────────
    const fallbackTitle = `Chapter ${getNextChapterIndex()}`;
    const nextTitle = createTitle.trim() || fallbackTitle;
    const trimmedFen = createMode === 'fen' ? createFen.trim() : '';

    if (nextTitle.includes('/')) {
      setCreateTitleError('No "/" in study or folder name');
      return;
    }

    setIsCreatingChapter(true);
    try {
      if (trimmedFen) {
        const response = await api.post('/api/v1/import-export/fen/import', {
          study_id: id,
          chapter_title: nextTitle,
          fen: trimmedFen
        });
        const chapter = {
          id: response.chapter_id,
          title: nextTitle,
          order: chapters.length,
          starting_fen: response.starting_fen
        };
        const nextChapters = sortChapters([...chapters, chapter]);
        setChapters(nextChapters);
        if (chapter.id) await loadChapterTree(chapter.id);
      } else {
        await handleCreateChapter(nextTitle);
      }
      setIsCreateModalOpen(false);
      setCreateFen('');
    } catch (e: any) {
      let errorMessage = 'Failed to create chapter';
      if (e.response?.status === 422 && e.response?.data?.detail) {
        const detail = e.response.data.detail;
        if (Array.isArray(detail)) {
          errorMessage = detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join('; ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        }
      } else {
        errorMessage = e.response?.data?.detail || e.message || errorMessage;
      }
      setCreateError(errorMessage);
    } finally {
      setIsCreatingChapter(false);
    }
  }, [createMode, createTitle, createFen, createPgnParsed, createPgnImporting, getNextChapterIndex, handleCreateChapter, isCreatingChapter, id, chapters, loadChapterTree, sortChapters]);

  useEffect(() => {
    if (isCreateModalOpen && createMode !== 'pgn' && createTitleInputRef.current) {
      createTitleInputRef.current.focus();
      createTitleInputRef.current.select();
    }
  }, [isCreateModalOpen, createMode]);

  useEffect(() => {
    const text = createPgnText.trim();
    if (!text) { setCreatePgnParsed(null); return; }
    setCreatePgnParsed(importMultiPgn(text, 64));
  }, [createPgnText]);

  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [isEditingTitle]);

  useEffect(() => {
    if (!id) return;
    loadStudy(id);
    let cancelled = false;

    const resolveChapterAndTree = async () => {
      try {
        const studyResponse = await api.get(`/api/v1/workspace/studies/${id}`);
        const resolvedTitle =
          studyResponse?.study?.title || studyResponse?.title || 'Study';
        setStudyTitle(resolvedTitle);

        // Render chapters immediately — don't block on breadcrumbs or studyNode
        const responseChapters = extractChapters(studyResponse);
        if (!Array.isArray(responseChapters)) {
          throw new Error('API response unexpected: chapters list missing');
        }
        let sortedChapters = sortChapters(responseChapters);
        setChapters(sortedChapters);

        // Breadcrumbs + studyNode in parallel, neither blocks the chapter list
        Promise.all([
          resolveDisplayPath('', resolvedTitle, id),
          api.get(`/api/v1/workspace/nodes/${id}`).catch((nodeError) => {
            console.warn(`[STUDY PAGE] Failed to fetch study node:`, nodeError);
            return null;
          }),
        ]).then(([resolvedBreadcrumbs, studyNode]) => {
          if (cancelled) return;
          setBreadcrumbs(resolvedBreadcrumbs);
          if (studyNode) {
            studyNodeRef.current = studyNode;
          }
        });

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
        const retryBreadcrumbs = await resolveDisplayPath('', retryTitle, id);
        setBreadcrumbs(retryBreadcrumbs);
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
        {isEditingTitle ? (
          <div className="patch-study-title-edit">
            <input
              ref={titleInputRef}
              type="text"
              className="patch-study-title-input"
              value={draftTitle}
              onChange={(e) => {
                setDraftTitle(e.target.value);
                if (!e.target.value.includes('/')) {
                  setTitleError(null);
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  commitEditingTitle();
                }
                if (e.key === 'Escape') {
                  e.preventDefault();
                  cancelEditingTitle();
                }
              }}
              onBlur={cancelEditingTitle}
            />
            {titleError && (
              <span className="patch-study-title-error">{titleError}</span>
            )}
          </div>
        ) : (
          <h2
            className="patch-study-title"
            onDoubleClick={startEditingTitle}
            title="Double-click to rename"
          >
            {studyTitle || 'Study'}
          </h2>
        )}
        <div className="patch-study-breadcrumb">
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.id}>
              {index > 0 && <span className="breadcrumb-separator">/</span>}
              <span
                className={`breadcrumb-item ${
                  index === breadcrumbs.length - 1 ? 'current' : 'clickable'
                }`}
                onDoubleClick={() => handleBreadcrumbDoubleClick(crumb, index)}
                title={
                  index === breadcrumbs.length - 1
                    ? 'Current study'
                    : 'Double-click to navigate'
                }
              >
                {crumb.title}
              </span>
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
            onReorderChapters={handleReorderChapters}
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
            {rightPanelTab === 'tree' ? (
              <MoveTree />
            ) : (
              <ExplorerPanel
                fen={state.currentFen}
                onMoveSelect={addMove}
              />
            )}
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
            <h3>New Chapter</h3>

            {/* Mode tabs */}
            <div className="patch-modal-tabs">
              {(['empty', 'fen', 'pgn'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`patch-modal-tab${createMode === mode ? ' is-active' : ''}`}
                  onClick={() => { setCreateMode(mode); setCreateError(null); setCreateTitleError(null); }}
                  disabled={isCreatingChapter || createPgnImporting}
                >
                  {mode === 'empty' ? 'Empty' : mode === 'fen' ? 'From FEN' : 'From PGN'}
                </button>
              ))}
            </div>

            {/* Title input (Empty + FEN modes) */}
            {createMode !== 'pgn' && (
              <>
                <label className="patch-modal-label">Chapter Title</label>
                <input
                  ref={createTitleInputRef}
                  className="patch-modal-input"
                  value={createTitle}
                  onChange={(event) => {
                    const nextValue = event.target.value;
                    setCreateTitle(nextValue);
                    if (!nextValue.includes('/')) setCreateTitleError(null);
                  }}
                  onFocus={(event) => event.target.select()}
                  placeholder="Chapter 1"
                />
                {createTitleError && <div className="patch-modal-error">{createTitleError}</div>}
              </>
            )}

            {/* FEN input */}
            {createMode === 'fen' && (
              <>
                <label className="patch-modal-label">Starting Position (FEN)</label>
                <textarea
                  className="patch-modal-textarea"
                  value={createFen}
                  onChange={(event) => setCreateFen(event.target.value)}
                  placeholder="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                  rows={2}
                />
                <div className="patch-modal-hint-text">
                  Enter a FEN string to start from a custom position (endgames, puzzles, etc.)
                </div>
              </>
            )}

            {/* PGN input */}
            {createMode === 'pgn' && (
              <>
                <textarea
                  className="patch-modal-textarea patch-modal-textarea--pgn"
                  value={createPgnText}
                  onChange={(event) => setCreatePgnText(event.target.value)}
                  placeholder="Paste PGN here…"
                  spellCheck={false}
                  rows={8}
                />
                <div className="patch-modal-pgn-actions">
                  <button
                    type="button"
                    className="patch-modal-button"
                    onClick={() => createPgnFileRef.current?.click()}
                    disabled={createPgnImporting}
                  >
                    Load .pgn file
                  </button>
                  <input
                    ref={createPgnFileRef}
                    type="file"
                    accept=".pgn,text/plain"
                    style={{ display: 'none' }}
                    onChange={handlePgnFileChange}
                  />
                  {createPgnText && (
                    <button
                      type="button"
                      className="patch-modal-button"
                      onClick={() => { setCreatePgnText(''); setCreatePgnParsed(null); }}
                      disabled={createPgnImporting}
                    >
                      Clear
                    </button>
                  )}
                </div>
                {createPgnParsed && createPgnParsed.games.length > 0 && (
                  <div className="patch-modal-pgn-preview">
                    <strong>
                      {createPgnParsed.games.length === 1
                        ? '1 game found'
                        : `${createPgnParsed.games.length} games found${createPgnParsed.truncated ? ' (truncated to 64)' : ''}`}
                    </strong>
                    <div className="patch-modal-pgn-preview__first">
                      {pgnGameTitle(createPgnParsed.games[0].headers)}
                      {createPgnParsed.games[0].startingFen && <span> · Custom starting position</span>}
                    </div>
                  </div>
                )}
                {createPgnParsed && createPgnParsed.games.length === 0 && (
                  <div className="patch-modal-error">No valid PGN games found.</div>
                )}
              </>
            )}

            {createError && <div className="patch-modal-error" style={{ whiteSpace: 'pre-line' }}>{createError}</div>}
            <div className="patch-modal-actions">
              <button
                type="button"
                className="patch-modal-button"
                onClick={closeCreateModal}
                disabled={isCreatingChapter || createPgnImporting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="patch-modal-button primary"
                onClick={confirmCreateChapter}
                disabled={
                  isCreatingChapter ||
                  createPgnImporting ||
                  (createMode === 'pgn' && (!createPgnParsed || createPgnParsed.games.length === 0))
                }
              >
                {createMode === 'pgn'
                  ? createPgnImporting
                    ? 'Importing…'
                    : createPgnParsed && createPgnParsed.games.length > 0
                      ? `Import ${createPgnParsed.games.length} game${createPgnParsed.games.length > 1 ? 's' : ''}`
                      : 'Import'
                  : isCreatingChapter
                    ? 'Creating…'
                    : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
      {showNavigationWarning && navigationTarget && (
        <div className="patch-modal-overlay">
          <div className="patch-modal">
            <h3>Unsaved Changes</h3>
            <p>You have unsaved changes. Do you want to save before leaving?</p>
            <div className="patch-modal-actions">
              <button
                type="button"
                className="patch-modal-button"
                onClick={() => setShowNavigationWarning(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="patch-modal-button secondary"
                onClick={() => {
                  setShowNavigationWarning(false);
                  navigateToBreadcrumb(navigationTarget);
                }}
              >
                Don't Save
              </button>
              <button
                type="button"
                className="patch-modal-button primary"
                onClick={async () => {
                  await saveAll();
                  navigateToBreadcrumb(navigationTarget);
                }}
              >
                Save & Leave
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
