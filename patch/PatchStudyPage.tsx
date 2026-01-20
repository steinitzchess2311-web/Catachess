import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { StudyProvider, useStudy } from './studyContext';
import { StudyBoard } from './board/studyBoard';
import { MoveTree } from './sidebar/movetree';
import { api } from '@ui/assets/api';
import { createEmptyTree } from './tree/StudyTree';
import { TREE_SCHEMA_VERSION } from './tree/type';

export interface PatchStudyPageProps {
  className?: string;
}

function StudyPageContent({ className }: PatchStudyPageProps) {
  const { id } = useParams<{ id: string }>();
  const { state, clearError, setError, selectChapter, loadTree } = useStudy();
  const savedTime = state.lastSavedAt ? new Date(state.lastSavedAt).toLocaleTimeString() : null;

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    const resolveChapterAndTree = async () => {
      try {
        const extractChapters = (response: any) =>
          response?.chapters || response?.study?.chapters || response?.data?.chapters;

        const getSortValue = (ch: any, key: string) => {
          const value = ch?.[key];
          if (typeof value === 'number') return value;
          if (typeof value === 'string') {
            const parsed = Date.parse(value);
            if (!Number.isNaN(parsed)) return parsed;
            return value;
          }
          return null;
        };

        const sortChapters = (items: any[]) => {
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
        };

        const studyResponse = await api.get(`/api/v1/workspace/studies/${id}`);
        const responseChapters = extractChapters(studyResponse);
        if (!Array.isArray(responseChapters)) {
          throw new Error('API response unexpected: chapters list missing');
        }

        let chapters = sortChapters(responseChapters);

        let chapter = chapters[0];

        if (!chapter) {
          try {
            chapter = await api.post(`/api/v1/workspace/studies/${id}/chapters`, {
              title: 'Chapter 1',
            });
          } catch (createError) {
            const retryResponse = await api.get(`/api/v1/workspace/studies/${id}`);
            const retryChapters = extractChapters(retryResponse);

            if (!Array.isArray(retryChapters)) {
              throw createError;
            }

            chapters = sortChapters(retryChapters);
            chapter = chapters[0];
            if (!chapter) {
              throw createError;
            }
          }
        }

        if (cancelled) return;

        selectChapter(chapter.id);

        try {
          const treeResponse = await api.get(`/study-patch/chapter/${chapter.id}/tree`);
          if (treeResponse?.success && treeResponse.tree) {
            if (!treeResponse.tree.version) {
              console.warn(`[patch] Tree missing version for chapter ${chapter.id}, will re-save.`);
              const upgradedTree = { ...treeResponse.tree, version: TREE_SCHEMA_VERSION };
              await api.put(`/study-patch/chapter/${chapter.id}/tree`, upgradedTree);
              loadTree(upgradedTree);
              return;
            }
            loadTree(treeResponse.tree);
            return;
          }
        } catch (e) {
          console.warn(`[patch] Tree load failed for chapter ${chapter.id}, initializing empty tree.`);
        }

        const emptyTree = createEmptyTree();
        const createResponse = await api.put(`/study-patch/chapter/${chapter.id}/tree`, emptyTree);
        if (!createResponse?.success) {
          throw new Error(createResponse?.error || 'Failed to initialize tree');
        }
        loadTree(emptyTree);
      } catch (e) {
        if (cancelled) return;
        setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to enter study');
      }
    };

    resolveChapterAndTree();

    return () => {
      cancelled = true;
    };
  }, [id, loadTree, selectChapter, setError]);

  return (
    <div className={`patch-study-page ${className || ''}`}>
      {state.error && (
        <div className="patch-study-error-banner" style={{
          backgroundColor: '#ffebee',
          color: '#c62828',
          padding: '10px',
          margin: '10px',
          border: '1px solid #ef9a9a',
          borderRadius: '4px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span><strong>Error:</strong> {state.error.message}</span>
          <button onClick={clearError} style={{
            background: 'none',
            border: 'none',
            color: '#c62828',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}>✕</button>
        </div>
      )}
      <div className="patch-study-header">
        <h2>Patch Study Mode (ID: {id})</h2>
        <p className="patch-study-notice">
          This is the new patch-based study interface. Development in progress.
        </p>
        <div className="patch-study-save-status">
          {state.isSaving && <span>Saving...</span>}
          {!state.isSaving && state.isDirty && <span>Unsaved changes</span>}
          {!state.isSaving && !state.isDirty && savedTime && <span>Saved at {savedTime}</span>}
        </div>
      </div>
      <div className="patch-study-layout">
        <div className="patch-study-sidebar">
          <MoveTree />
        </div>
        <div className="patch-study-main">
          <StudyBoard />
        </div>
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
