import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { StudyProvider, useStudy } from './studyContext';
import { StudyBoard } from './board/studyBoard';
import { MoveTree } from './sidebar/movetree';
import { StudySidebar } from './sidebar/StudySidebar';
import { CommentBox } from './CommentBox';
import { api } from '@ui/assets/api';
import { createEmptyTree } from './tree/StudyTree';
import { TREE_SCHEMA_VERSION } from './tree/type';

export interface PatchStudyPageProps {
  className?: string;
}

function StudyPageContent({ className }: PatchStudyPageProps) {
  const { id } = useParams<{ id: string }>();
  const { state, clearError, setError, selectChapter, loadTree, saveTree } = useStudy();
  const [chapters, setChapters] = useState<any[]>([]);
  const [studyTitle, setStudyTitle] = useState<string>('');
  const [displayPath, setDisplayPath] = useState<string>('root');
  const savedTime = state.lastSavedAt ? new Date(state.lastSavedAt).toLocaleTimeString() : null;
  const savedLabel = state.isSaving
    ? 'Saving...'
    : state.isDirty
      ? 'Unsaved changes'
      : savedTime
        ? `Saved at ${savedTime}`
        : 'Unsaved changes';

  const patchBase = '/api/v1/workspace/studies/study-patch';

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

  const handleCreateChapter = useCallback(async () => {
    if (!id) return;
    try {
      const title = `Chapter ${chapters.length + 1}`;
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
            onClick={saveTree}
            disabled={state.isSaving || !state.isDirty}
          >
            {state.isSaving ? 'Saving...' : (state.isDirty ? 'Save' : 'Saved')}
          </button>
        </div>
        <div className="patch-study-save-status">{savedLabel}</div>
      </div>
      <div className="patch-study-layout" style={{ height: '600px' }}>
        <div className="patch-study-sidebar">
          <StudySidebar
            chapters={chapters}
            currentChapterId={state.chapterId}
            onSelectChapter={handleSelectChapter}
            onCreateChapter={handleCreateChapter}
          />
        </div>
        <div className="patch-study-main">
          <StudyBoard />
        </div>
        <div className="patch-study-rightbar">
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
