import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef, ReactNode } from 'react';
import { api } from '@ui/assets/api';
import { replaySanPath, STARTING_FEN } from './chessJS/replay';
import type { ReplayResult } from './chessJS/replay';
import type { StudyTree as StudyTreeData, Shape } from './tree/type';

import {
  studyReducer,
  initialState,
  createSnapshot,
} from './tree/studyReducer';

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
  state: ReturnType<typeof studyReducer>;
  replayPath: (moves: string[], startFen?: string) => ReplayResult;
  setError: (type: import('./tree/studyReducer').StudyErrorType, message: string, context?: Record<string, unknown>) => void;
  clearError: () => void;
  hasReplayError: () => boolean;
  loadStudy: (studyId: string) => Promise<void>;
  selectChapter: (chapterId: string, startFen?: string) => Promise<void>;
  loadTree: (tree: StudyTreeData, startFen?: string) => void;
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
  selectChapter: async () => {},
  loadTree: () => {},
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

// =============================================================================
// Provider
// =============================================================================

export function StudyProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(studyReducer, initialState);
  const fenCacheRef = useRef<Record<string, string>>({});
  const patchBase = '/api/v1/workspace/studies/study-patch';

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

  const selectChapter = useCallback(async (chapterId: string, startFen?: string) => {
    fenCacheRef.current = {};
    dispatch({ type: 'SET_CHAPTER', chapterId, startFen });
  }, []);

  const loadTree = useCallback((tree: StudyTreeData, startFen?: string) => {
    dispatch({ type: 'LOAD_TREE', tree, startFen });
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

  const deleteMove = useCallback((nodeId: string) => dispatch({ type: 'DELETE_MOVE', nodeId }), []);

  const promoteVariation = useCallback((nodeId: string) => dispatch({ type: 'PROMOTE_VARIATION', nodeId }), []);

  const undo = useCallback(() => dispatch({ type: 'UNDO' }), []);

  const saveTree = useCallback(async () => {
    if (!state.chapterId || state.isSaving) return;

    const treePayload = JSON.stringify(state.tree);
    let currentHash = '';
    try {
      const data = new TextEncoder().encode(treePayload);
      const buf = await crypto.subtle.digest('SHA-256', data);
      currentHash = Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
    } catch { /* ignore hash errors */ }

    if (currentHash === state.lastSavedHash && !state.isDirty) return;

    dispatch({ type: 'SET_SAVING', isSaving: true });
    try {
      await api.put(`${patchBase}/chapter/${state.chapterId}/tree`, state.tree);
      dispatch({ type: 'MARK_SAVED', timestamp: Date.now(), hash: currentHash });
    } catch (e) {
      console.error('[saveTree] Save failed:', e);
      setError('SAVE_ERROR', e instanceof Error ? e.message : 'Failed to save tree');
    } finally {
      dispatch({ type: 'SET_SAVING', isSaving: false });
    }
  }, [patchBase, state.chapterId, state.isSaving, state.isDirty, state.lastSavedHash, state.tree, setError]);

  // Auto-save 5 s after the tree becomes dirty
  useEffect(() => {
    if (!state.isDirty || !state.chapterId) return;
    const id = window.setTimeout(saveTree, 5000);
    return () => window.clearTimeout(id);
  }, [state.isDirty, state.chapterId, state.tree, saveTree]);

  const loadTreeFromServer = useCallback(async () => {}, []);

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
    selectChapter,
    loadTree,
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
