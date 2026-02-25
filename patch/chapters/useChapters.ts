import { useCallback, useState } from 'react';
import { api } from '@ui/assets/api';
import { useStudy } from '../studyContext';
import { createEmptyTree } from '../tree/StudyTree';
import { TREE_SCHEMA_VERSION } from '../tree/type';

const PATCH_BASE = '/api/v1/workspace/studies/study-patch';

export function useChapters(studyId: string | undefined) {
  const { loadTree, selectChapter, setError, state } = useStudy();

  const [chapters, setChapters] = useState<any[]>([]);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<string[]>([]);
  const [pendingDeleteChapters, setPendingDeleteChapters] = useState<Array<{ id: string; order?: number }>>([]);

  const hasPendingDeletes = pendingDeleteIds.length > 0;

  // ── Sorting helpers ──────────────────────────────────────────────────────

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
      const createdA = getSortValue(a, 'created_at');
      const createdB = getSortValue(b, 'created_at');
      if (createdA !== null || createdB !== null) {
        if (createdA === null) return 1;
        if (createdB === null) return -1;
        return createdA < createdB ? -1 : createdA > createdB ? 1 : 0;
      }
      return `${a?.id ?? ''}`.localeCompare(`${b?.id ?? ''}`);
    });
  }, [getSortValue]);

  const applyChapterOrder = useCallback((items: any[], order: string[]) => {
    const byId = new Map(items.map((ch) => [ch.id, ch]));
    const ordered: any[] = [];
    order.forEach((chapterId, index) => {
      const ch = byId.get(chapterId);
      if (ch) ordered.push({ ...ch, order: index });
    });
    const known = new Set(order);
    items.forEach((ch, index) => {
      if (!known.has(ch.id)) ordered.push({ ...ch, order: order.length + index });
    });
    return ordered;
  }, []);

  const extractChapters = useCallback((response: any) => {
    return response?.chapters || response?.study?.chapters || response?.data?.chapters;
  }, []);

  const getNextChapterIndex = useCallback(() => {
    const taken = new Set(chapters.map((ch) => ch.title).filter(Boolean));
    let n = chapters.length + 1;
    while (taken.has(`Chapter ${n}`)) n++;
    return n;
  }, [chapters]);

  // ── Tree loading ─────────────────────────────────────────────────────────

  const loadChapterTree = useCallback(async (chapterId: string, retryCount = 0) => {
    const maxRetries = 3;
    try {
      const res = await api.get(`${PATCH_BASE}/chapter/${chapterId}/tree`);
      if (res?.success && res.tree) {
        const startFen = res.starting_fen || undefined;
        if (!res.tree.version) {
          const upgraded = { ...res.tree, version: TREE_SCHEMA_VERSION };
          await api.put(`${PATCH_BASE}/chapter/${chapterId}/tree`, upgraded);
          loadTree(upgraded, startFen);
          return;
        }
        loadTree(res.tree, startFen);
        return;
      }
      if (retryCount < maxRetries) {
        await new Promise((r) => setTimeout(r, 500));
        return loadChapterTree(chapterId, retryCount + 1);
      }
    } catch (e) {
      if (retryCount < maxRetries) {
        await new Promise((r) => setTimeout(r, 500));
        return loadChapterTree(chapterId, retryCount + 1);
      }
      console.warn(`[patch] Tree load failed for chapter ${chapterId}`, e);
    }
    const empty = createEmptyTree();
    const createRes = await api.put(`${PATCH_BASE}/chapter/${chapterId}/tree`, empty);
    if (!createRes?.success) throw new Error(createRes?.error || 'Failed to initialize tree');
    loadTree(empty);
  }, [loadTree]);

  // ── Chapter CRUD ─────────────────────────────────────────────────────────

  const handleSelectChapter = useCallback(async (chapterId: string) => {
    selectChapter(chapterId);
    try {
      await loadChapterTree(chapterId);
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to load chapter');
    }
  }, [loadChapterTree, selectChapter, setError]);

  const handleCreateChapter = useCallback(async (title: string) => {
    if (!studyId) return;
    try {
      const chapter = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, { title });
      setChapters((prev) => sortChapters([...prev, chapter]));
      if (chapter?.id) {
        selectChapter(chapter.id);
        await loadChapterTree(chapter.id);
      }
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to create chapter');
    }
  }, [loadChapterTree, selectChapter, setError, sortChapters, studyId]);

  const handleRenameChapter = useCallback(async (chapterId: string, title: string) => {
    if (!studyId) return;
    try {
      const updated = await api.put(`/api/v1/workspace/studies/${studyId}/chapters/${chapterId}`, { title });
      setChapters((prev) =>
        sortChapters(prev.map((ch) => ch.id === chapterId ? { ...ch, title: updated?.title || title } : ch))
      );
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to rename chapter');
      throw e;
    }
  }, [setError, sortChapters, studyId]);

  const processPendingDeletes = useCallback(async (deleteIds: string[]) => {
    if (!studyId || deleteIds.length === 0) return;
    try {
      await Promise.all(
        deleteIds.map((chapterId) =>
          api.delete(`/api/v1/workspace/studies/${studyId}/chapters/${chapterId}`)
        )
      );
      setPendingDeleteIds((prev) => prev.filter((id) => !deleteIds.includes(id)));
      setPendingDeleteChapters((prev) => prev.filter((ch) => !deleteIds.includes(ch.id)));
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to delete chapter');
      throw e;
    }
  }, [setError, studyId]);

  const handleDeleteChapter = useCallback(async (chapterId: string) => {
    if (!studyId) return;
    try {
      const deletedChapter = chapters.find((ch) => ch.id === chapterId);
      const remaining = chapters.filter((ch) => ch.id !== chapterId);
      setPendingDeleteIds((prev) => prev.includes(chapterId) ? prev : [...prev, chapterId]);
      if (deletedChapter) {
        setPendingDeleteChapters((prev) =>
          prev.some((item) => item.id === chapterId) ? prev : [...prev, deletedChapter]
        );
      }
      setChapters(sortChapters(remaining));
      if (state.chapterId === chapterId) {
        const next = sortChapters(remaining)[0];
        if (next) await loadChapterTree(next.id);
      }
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to delete chapter');
      throw e;
    }
  }, [chapters, loadChapterTree, setError, sortChapters, state.chapterId, studyId]);

  const handleReorderChapters = useCallback(
    async (order: string[], _ctx: { draggedId: string; targetId: string; placement: 'before' | 'after' }) => {
      if (!studyId) return;
      const previous = chapters;
      setChapters(applyChapterOrder(previous, order));
      try {
        const response = await api.post(`/api/v1/workspace/studies/${studyId}/chapters/reorder`, { order });
        if (Array.isArray(response)) setChapters(sortChapters(response));
      } catch (e) {
        setChapters(previous);
        setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to reorder chapters');
      }
    },
    [applyChapterOrder, chapters, setError, sortChapters, studyId]
  );

  return {
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
  };
}
