/**
 * Created at: 2026-07-08 22:15 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-08 22:15 EDT
 * Last Modified by: Codex
 *
 * Patch study React context. Owns study tree state, replay helpers, and the
 * coalesced autosave pipeline for persisted chapter tree JSON.
 */

import { createContext, useContext, useReducer, useCallback, useEffect, useRef, ReactNode } from 'react';
import { api } from '@ui/assets/api';
import { replaySanPath, STARTING_FEN } from './chessJS/replay';
import type { ReplayResult } from './chessJS/replay';
import type { StudyTree as StudyTreeData, Shape } from './tree/type';

import {
  studyReducer,
  initialState,
} from './tree/studyReducer';
import type { StudyState } from './tree/studyReducer';

export type {
  StudyErrorType,
  StudyError,
  StudyStateSnapshot,
  StudyState,
  StudyAction,
} from './tree/studyReducer';

// =============================================================================
// Context value type
// =============================================================================

export interface StudyContextValue {
  state: StudyState;
  replayPath: (moves: string[], startFen?: string) => ReplayResult;
  setError: (type: import('./tree/studyReducer').StudyErrorType, message: string, context?: Record<string, unknown>) => void;
  clearError: () => void;
  hasReplayError: () => boolean;
  loadStudy: (studyId: string) => Promise<void>;
  setAccess: (canEdit: boolean, effectivePermission?: import('./tree/studyReducer').StudyStateSnapshot['effectivePermission']) => void;
  selectChapter: (chapterId: string, startFen?: string) => Promise<void>;
  loadTree: (tree: StudyTreeData, startFen?: string) => void;
  setTreeRevision: (treeRevision: number, treeUpdatedAt?: string | null) => void;
  selectNode: (nodeId: string) => void;
  addMove: (san: string) => void;
  setComment: (nodeId: string, comment: string) => void;
  setShapes: (nodeId: string, shapes: Shape[]) => void;
  deleteMove: (nodeId: string) => void;
  promoteVariation: (nodeId: string) => void;
  undo: () => void;
  saveTree: () => Promise<void>;
  loadTreeFromServer: () => Promise<void>;
  enterTrainMode: () => void;
  exitTrainMode: () => void;
  submitTrain: (mergedTree: StudyTreeData) => void;
}

const defaultContextValue: StudyContextValue = {
  state: initialState,
  replayPath: () => ({ board: null, historySan: [], historyFen: [], illegalMoveIndex: -1, error: 'Context not initialized', finalFen: STARTING_FEN }),
  setError: () => {},
  clearError: () => {},
  hasReplayError: () => false,
  loadStudy: async () => {},
  setAccess: () => {},
  selectChapter: async () => {},
  loadTree: () => {},
  setTreeRevision: () => {},
  selectNode: () => {},
  addMove: () => {},
  setComment: () => {},
  setShapes: () => {},
  deleteMove: () => {},
  promoteVariation: () => {},
  undo: () => {},
  saveTree: async () => {},
  loadTreeFromServer: async () => {},
  enterTrainMode: () => {},
  exitTrainMode: () => {},
  submitTrain: () => {},
};

const StudyContext = createContext<StudyContextValue>(defaultContextValue);

const PATCH_STUDY_API_BASE = '/api/v1/workspace/studies/study-patch';
const AUTOSAVE_DELAY_MS = 2000;
const REMOTE_REVISION_POLL_MS = 10000;

async function createTreeSavePayload(tree: StudyTreeData): Promise<{ payload: string; hash: string }> {
  const payload = JSON.stringify(tree);
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) return { payload, hash: '' };

  try {
    const data = new TextEncoder().encode(payload);
    const buf = await subtle.digest('SHA-256', data);
    const hash = Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
    return { payload, hash };
  } catch {
    return { payload, hash: '' };
  }
}

// =============================================================================
// Provider
// =============================================================================

export function StudyProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(studyReducer, initialState);
  const fenCacheRef = useRef<Record<string, string>>({});
  const latestStateRef = useRef(state);
  const saveInFlightRef = useRef(false);
  const saveQueuedRef = useRef(false);

  useEffect(() => {
    latestStateRef.current = state;
  }, [state]);

  // Keep FEN cache in sync
  useEffect(() => {
    if (state.cursorNodeId && state.currentFen) {
      fenCacheRef.current[state.cursorNodeId] = state.currentFen;
    }
  }, [state.cursorNodeId, state.currentFen]);

  const replayPath = useCallback(
    (moves: string[], startFen?: string): ReplayResult => {
      const fen = startFen || state.startFen;
      const result = replaySanPath(moves, fen);
      dispatch({ type: 'SET_REPLAY_RESULT', result });
      return result;
    },
    [state.startFen]
  );

  const setError = useCallback(
    (type: import('./tree/studyReducer').StudyErrorType, message: string, context?: Record<string, unknown>) => {
      dispatch({ type: 'SET_ERROR', error: { type, message, context, timestamp: Date.now() } });
    },
    []
  );

  const clearError = useCallback(() => dispatch({ type: 'CLEAR_ERROR' }), []);

  const hasReplayError = useCallback(() => state.error?.type === 'REPLAY_ERROR', [state.error]);

  const loadStudy = useCallback(async (studyId: string) => {
    dispatch({ type: 'SET_STUDY', studyId });
  }, []);

  const setAccess = useCallback(
    (canEdit: boolean, effectivePermission?: import('./tree/studyReducer').StudyStateSnapshot['effectivePermission']) => {
      dispatch({ type: 'SET_ACCESS', canEdit, effectivePermission });
    },
    []
  );

  const selectChapter = useCallback(async (chapterId: string, startFen?: string) => {
    fenCacheRef.current = {};
    dispatch({ type: 'SET_CHAPTER', chapterId, startFen });
  }, []);

  const loadTree = useCallback((tree: StudyTreeData, startFen?: string) => {
    dispatch({ type: 'LOAD_TREE', tree, startFen });
  }, []);

  const setTreeRevision = useCallback((treeRevision: number, treeUpdatedAt?: string | null) => {
    dispatch({ type: 'SET_TREE_REVISION', treeRevision, treeUpdatedAt });
  }, []);

  const selectNode = useCallback((nodeId: string) => {
    const cachedFen = fenCacheRef.current[nodeId];
    dispatch({ type: 'SET_CURSOR', nodeId, precomputedFen: cachedFen });
  }, []);

  const addMove = useCallback((san: string) => dispatch({ type: 'ADD_MOVE', san }), []);

  const setComment = useCallback((nodeId: string, comment: string) => {
    dispatch({ type: 'SET_COMMENT', nodeId, comment });
  }, []);

  const setShapes = useCallback((nodeId: string, shapes: Shape[]) => {
    dispatch({ type: 'SET_SHAPES', nodeId, shapes });
  }, []);

  const deleteMove = useCallback((nodeId: string) => {
    if (state.tree.nodes[nodeId]?.is_base) return;
    dispatch({ type: 'DELETE_MOVE', nodeId });
  }, [state.tree.nodes]);

  const promoteVariation = useCallback((nodeId: string) => {
    if (state.tree.nodes[nodeId]?.is_base) return;
    dispatch({ type: 'PROMOTE_VARIATION', nodeId });
  }, [state.tree.nodes]);

  const undo = useCallback(() => dispatch({ type: 'UNDO' }), []);

  const saveTree = useCallback(async () => {
    const initialSnapshot = latestStateRef.current;
    if (!initialSnapshot.chapterId || !initialSnapshot.canEdit) return;

    if (saveInFlightRef.current) {
      saveQueuedRef.current = true;
      return;
    }

    saveInFlightRef.current = true;
    dispatch({ type: 'SET_SAVING', isSaving: true });

    try {
      const snapshot = latestStateRef.current;
      if (!snapshot.chapterId || !snapshot.canEdit) return;

      const { payload: treePayload, hash: currentHash } = await createTreeSavePayload(snapshot.tree);
      const latestBeforeRequest = latestStateRef.current;
      if (latestBeforeRequest.chapterId !== snapshot.chapterId) {
        saveQueuedRef.current = latestBeforeRequest.isDirty;
        return;
      }

      const changedWhileHashing = latestBeforeRequest.tree !== snapshot.tree;
      if (changedWhileHashing && latestBeforeRequest.isDirty) {
        saveQueuedRef.current = true;
      }

      if (currentHash && currentHash === latestBeforeRequest.lastSavedHash) {
        if (!changedWhileHashing) {
          dispatch({ type: 'MARK_SAVED', timestamp: Date.now(), hash: currentHash });
        }
        return;
      }

      if (!latestBeforeRequest.isDirty && !currentHash) return;

      const response = await api.request(`${PATCH_STUDY_API_BASE}/chapter/${snapshot.chapterId}/tree`, {
        method: 'PUT',
        headers: currentHash ? { 'X-Tree-Hash': currentHash } : {},
        body: treePayload,
      });

      if (response?.success === false) {
        throw new Error(response.error || 'Failed to save tree');
      }

      const latestAfterRequest = latestStateRef.current;
      if (latestAfterRequest.chapterId !== snapshot.chapterId) return;

      let keepDirty = latestAfterRequest.tree !== snapshot.tree;
      if (currentHash) {
        const latestPayload = latestAfterRequest.tree === snapshot.tree
          ? { hash: currentHash }
          : await createTreeSavePayload(latestAfterRequest.tree);
        keepDirty = latestPayload.hash !== currentHash;
      }

      dispatch({ type: 'MARK_SAVED', timestamp: Date.now(), hash: currentHash, keepDirty });
      if (typeof response?.tree_revision === 'number') {
        dispatch({
          type: 'SET_TREE_REVISION',
          treeRevision: response.tree_revision,
          treeUpdatedAt: response.tree_updated_at ?? null,
        });
      }
      if (keepDirty) {
        saveQueuedRef.current = true;
      }
    } catch (e) {
      saveQueuedRef.current = false;
      console.error('[saveTree] Save failed:', e);
      setError('SAVE_ERROR', e instanceof Error ? e.message : 'Failed to save tree');
    } finally {
      const shouldFlushQueuedSave = saveQueuedRef.current && latestStateRef.current.isDirty;
      saveQueuedRef.current = false;
      saveInFlightRef.current = false;
      dispatch({ type: 'SET_SAVING', isSaving: false });
      if (shouldFlushQueuedSave) {
        window.setTimeout(() => { void saveTree(); }, 0);
      }
    }
  }, [setError]);

  // Auto-save after the tree becomes dirty; saveTree coalesces in-flight writes.
  useEffect(() => {
    if (!state.canEdit || !state.isDirty || !state.chapterId || state.isSaving) return;
    const id = window.setTimeout(saveTree, AUTOSAVE_DELAY_MS);
    return () => window.clearTimeout(id);
  }, [state.canEdit, state.isDirty, state.chapterId, state.tree, state.isSaving, saveTree]);

  const loadTreeFromServer = useCallback(async () => {
    const snapshot = latestStateRef.current;
    if (!snapshot.chapterId) return;
    dispatch({ type: 'SET_LOADING', isLoading: true });
    try {
      const response = await api.get(`${PATCH_STUDY_API_BASE}/chapter/${snapshot.chapterId}/tree`);
      if (!response?.success || !response.tree) {
        throw new Error(response?.error || 'Failed to load tree');
      }
      const latest = latestStateRef.current;
      if (latest.chapterId !== snapshot.chapterId) return;
      fenCacheRef.current = {};
      dispatch({ type: 'LOAD_TREE', tree: response.tree, startFen: response.starting_fen || undefined });
      if (typeof response.tree_revision === 'number') {
        dispatch({
          type: 'SET_TREE_REVISION',
          treeRevision: response.tree_revision,
          treeUpdatedAt: response.tree_updated_at ?? null,
        });
      } else {
        dispatch({ type: 'CLEAR_REMOTE_UPDATE' });
      }
    } catch (e) {
      setError('LOAD_ERROR', e instanceof Error ? e.message : 'Failed to load latest tree');
    } finally {
      dispatch({ type: 'SET_LOADING', isLoading: false });
    }
  }, [setError]);

  useEffect(() => {
    if (!state.chapterId) return;
    let cancelled = false;
    const poll = async () => {
      const snapshot = latestStateRef.current;
      if (!snapshot.chapterId || snapshot.isSaving) return;
      try {
        const response = await api.get(`${PATCH_STUDY_API_BASE}/chapter/${snapshot.chapterId}/tree-meta`);
        if (cancelled || !response?.success || typeof response.tree_revision !== 'number') return;
        const latest = latestStateRef.current;
        if (latest.chapterId !== snapshot.chapterId || response.tree_revision <= latest.treeRevision) return;
        if (!latest.isDirty && !latest.isSaving) {
          await loadTreeFromServer();
          return;
        }
        dispatch({
          type: 'SET_REMOTE_TREE_REVISION',
          treeRevision: response.tree_revision,
          treeUpdatedAt: response.tree_updated_at ?? null,
        });
      } catch {
        // Polling is advisory; foreground load/save errors remain user-visible.
      }
    };
    const id = window.setInterval(() => { void poll(); }, REMOTE_REVISION_POLL_MS);
    void poll();
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [state.chapterId, loadTreeFromServer]);

  const enterTrainMode = useCallback(() => dispatch({ type: 'ENTER_TRAIN_MODE' }), []);
  const exitTrainMode = useCallback(() => dispatch({ type: 'EXIT_TRAIN_MODE' }), []);
  const submitTrain = useCallback((mergedTree: StudyTreeData) => {
    dispatch({ type: 'SUBMIT_TRAIN', mergedTree });
  }, []);

  const value: StudyContextValue = {
    state,
    replayPath,
    setError,
    clearError,
    hasReplayError,
    loadStudy,
    setAccess,
    selectChapter,
    loadTree,
    setTreeRevision,
    selectNode,
    addMove,
    setComment,
    setShapes,
    deleteMove,
    promoteVariation,
    undo,
    saveTree,
    loadTreeFromServer,
    enterTrainMode,
    exitTrainMode,
    submitTrain,
  };

  return <StudyContext.Provider value={value}>{children}</StudyContext.Provider>;
}

// =============================================================================
// Hook
// =============================================================================

export function useStudyContext(): StudyContextValue {
  return useContext(StudyContext);
}

export const useStudy = useStudyContext;

export default StudyContext;
