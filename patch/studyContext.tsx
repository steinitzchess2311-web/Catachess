import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef, ReactNode } from 'react';
import { api } from '@ui/assets/api';
import { replaySanPath, STARTING_FEN } from './chessJS/replay';
import type { ReplayResult } from './chessJS/replay';
import { StudyTree, createEmptyTree } from './tree/StudyTree';
import type { StudyTree as StudyTreeData } from './tree/type';
import { upgradeTree } from './tree/type';
import { validateFen } from './chessJS/fen';

/**
 * StudyContext - State management for the patch study module
 *
 * Handles:
 * - Tree state (loaded from tree.json)
 * - Current cursor position
 * - Computed FEN (via replay, never persisted)
 * - Replay errors (illegal moves, invalid SAN)
 * - Undo history
 */

// =============================================================================
// Error Handling Types
// =============================================================================

export type StudyErrorType =
  | 'REPLAY_ERROR'
  | 'INVALID_FEN'
  | 'LOAD_ERROR'
  | 'SAVE_ERROR';

export interface StudyError {
  type: StudyErrorType;
  message: string;
  context?: Record<string, unknown>;
  timestamp: number;
}

// =============================================================================
// State Types
// =============================================================================

/**
 * Snapshot of the state for history
 */
export interface StudyStateSnapshot {
  studyId: string | null;
  chapterId: string | null;
  tree: StudyTreeData;
  cursorNodeId: string;
  currentPath: string[];
  currentFen: string;
  startFen: string;
  lastReplayResult: ReplayResult | null;
  error: StudyError | null;
  isLoading: boolean;
  isDirty: boolean;
  lastSavedAt: number | null;
  isSaving: boolean;
  lastSavedHash: string | null;
}

export interface StudyState extends StudyStateSnapshot {
  /**
   * Stack of previous states for Undo
   */
  history: StudyStateSnapshot[];
}

// =============================================================================
// Actions
// =============================================================================

type StudyAction =
  | { type: 'SET_STUDY'; studyId: string }
  | { type: 'SET_CHAPTER'; chapterId: string; startFen?: string }
  | { type: 'LOAD_TREE'; tree: StudyTreeData }
  | { type: 'SET_CURSOR'; nodeId: string; precomputedFen?: string }
  | { type: 'ADD_MOVE'; san: string }
  | { type: 'SET_COMMENT'; nodeId: string; comment: string }
  | { type: 'DELETE_MOVE'; nodeId: string }
  | { type: 'PROMOTE_VARIATION'; nodeId: string }
  | { type: 'UNDO' }
  | { type: 'SET_REPLAY_RESULT'; result: ReplayResult }
  | { type: 'SET_ERROR'; error: StudyError }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'MARK_SAVED'; timestamp: number; hash: string }
  | { type: 'SET_SAVING'; isSaving: boolean }
  | { type: 'RESET' };

// =============================================================================
// Reducer
// =============================================================================

const initialTree = createEmptyTree();
const initialSnapshot: StudyStateSnapshot = {
  studyId: null,
  chapterId: null,
  tree: initialTree,
  cursorNodeId: initialTree.rootId,
  currentPath: [],
  currentFen: STARTING_FEN,
  startFen: STARTING_FEN,
  lastReplayResult: null,
  error: null,
  isLoading: false,
  isDirty: false,
  lastSavedAt: null,
  isSaving: false,
  lastSavedHash: null,
};

const initialState: StudyState = {
  ...initialSnapshot,
  history: [],
};

// Helper to create a snapshot for the history stack
const createSnapshot = (state: StudyState): StudyStateSnapshot => {
  const { history, ...snapshot } = state;
  // Deep clone tree to ensure snapshot is immutable
  return {
    ...snapshot,
    tree: JSON.parse(JSON.stringify(snapshot.tree)),
    currentPath: [...snapshot.currentPath],
  };
};

function studyReducer(state: StudyState, action: StudyAction): StudyState {
  switch (action.type) {
    case 'SET_STUDY':
      return {
        ...initialState,
        studyId: action.studyId,
      };

    case 'SET_CHAPTER': {
      const emptyTree = createEmptyTree();
      const requestedStartFen = action.startFen || STARTING_FEN;
      const startValidation = validateFen(requestedStartFen);
      const startFen = startValidation.valid ? requestedStartFen : STARTING_FEN;
      return {
        ...state,
        chapterId: action.chapterId,
        tree: emptyTree,
        cursorNodeId: emptyTree.rootId,
        currentPath: [],
        startFen: startFen,
        currentFen: startFen,
        error: startValidation.valid
          ? null
          : {
              type: 'INVALID_FEN',
              message: `Invalid starting FEN, falling back to default: ${startValidation.error}`,
              timestamp: Date.now(),
            },
        isDirty: false,
        lastSavedAt: null,
        isSaving: false,
        lastSavedHash: null,
        history: [], // Reset history on new chapter
      };
    }

    case 'LOAD_TREE': {
      const startValidation = validateFen(state.startFen);
      const safeStartFen = startValidation.valid ? state.startFen : STARTING_FEN;
      const upgrade = upgradeTree(action.tree);
      if (!upgrade.tree) {
        return {
          ...state,
          error: {
            type: 'LOAD_ERROR',
            message: upgrade.errors.join('; ') || 'Invalid tree data',
            timestamp: Date.now(),
          },
        };
      }

      return {
        ...state,
        tree: upgrade.tree,
        cursorNodeId: upgrade.tree.rootId,
        currentPath: [],
        startFen: safeStartFen,
        currentFen: safeStartFen,
        error: startValidation.valid
          ? null
          : {
              type: 'INVALID_FEN',
              message: `Invalid starting FEN, falling back to default: ${startValidation.error}`,
              timestamp: Date.now(),
            },
        isDirty: false,
        lastSavedAt: null,
        isSaving: false,
        lastSavedHash: null,
        history: [],
      };
    }

    case 'SET_CURSOR': {
      if (!state.tree.nodes[action.nodeId]) {
        return {
          ...state,
          error: {
            type: 'REPLAY_ERROR',
            message: `Cannot set cursor: Node ${action.nodeId} not found`,
            timestamp: Date.now(),
          },
        };
      }

      if (action.precomputedFen) {
        const treeOps = new StudyTree(state.tree);
        const moves = treeOps.getPathSan(action.nodeId);

        return {
          ...state,
          cursorNodeId: action.nodeId,
          currentPath: moves,
          currentFen: action.precomputedFen,
          error: null,
        };
      }

      const treeOps = new StudyTree(state.tree);
      const moves = treeOps.getPathSan(action.nodeId);

      // Miss cache, replay
      const replayResult = replaySanPath(moves, state.startFen);

      return {
        ...state,
        cursorNodeId: action.nodeId,
        currentPath: moves,
        currentFen: replayResult.finalFen,
        lastReplayResult: replayResult,
        error: replayResult.error
          ? {
              type: 'REPLAY_ERROR',
              message: replayResult.error,
              context: { illegalMoveIndex: replayResult.illegalMoveIndex },
              timestamp: Date.now(),
            }
          : null,
      };
    }

    case 'ADD_MOVE': {
      const treeClone = JSON.parse(JSON.stringify(state.tree));
      const treeOps = new StudyTree(treeClone);

      try {
        const newNode = treeOps.addMove(state.cursorNodeId, action.san);
        const newPath = [...state.currentPath, newNode.san];
        const replayResult = replaySanPath(newPath, state.startFen);
        const nextFen = replayResult.finalFen;

        const snapshot = createSnapshot(state);

        return {
          ...state,
          tree: treeOps.getData(),
          cursorNodeId: newNode.id,
          currentPath: newPath,
          currentFen: nextFen,
          lastReplayResult: replayResult || state.lastReplayResult,
          isDirty: true,
          error: replayResult?.error
            ? {
                type: 'REPLAY_ERROR',
                message: replayResult.error,
                context: { illegalMoveIndex: replayResult.illegalMoveIndex },
                timestamp: Date.now(),
              }
            : null,
          history: [...state.history, snapshot],
        };
      } catch (e: any) {
        return {
          ...state,
          error: {
            type: 'REPLAY_ERROR',
            message: e.message || 'Failed to add move',
            timestamp: Date.now(),
          },
        };
      }
    }

    case 'SET_COMMENT': {
      const treeClone = JSON.parse(JSON.stringify(state.tree));
      if (treeClone.nodes[action.nodeId]) {
        treeClone.nodes[action.nodeId].comment = action.comment || null;
      }
      const snapshot = createSnapshot(state);
      return {
        ...state,
        tree: treeClone,
        isDirty: true,
        history: [...state.history, snapshot],
      };
    }

    case 'DELETE_MOVE': {
      if (action.nodeId === state.tree.rootId) return state;

      const snapshot = createSnapshot(state);
      const treeClone = JSON.parse(JSON.stringify(state.tree));
      const treeOps = new StudyTree(treeClone);

      let nextCursorId = state.cursorNodeId;
      let nextPath = state.currentPath;
      let nextFen = state.currentFen;

      const oldTreeOps = new StudyTree(state.tree);
      const currentPathIds = oldTreeOps.getPathToNode(state.cursorNodeId);

      if (currentPathIds.includes(action.nodeId)) {
        const nodeToDelete = state.tree.nodes[action.nodeId];
        const newCursorId = nodeToDelete?.parentId || state.tree.rootId;
        nextCursorId = newCursorId;

        const moves = oldTreeOps.getPathSan(newCursorId);
        nextPath = moves;
        nextFen = replaySanPath(moves, state.startFen).finalFen;
      }

      try {
        treeOps.removeNode(action.nodeId);
        return {
          ...state,
          tree: treeOps.getData(),
          cursorNodeId: nextCursorId,
          currentPath: nextPath,
          currentFen: nextFen,
          isDirty: true,
          history: [...state.history, snapshot],
        };
      } catch (e: any) {
        return {
          ...state,
          error: { type: 'SAVE_ERROR', message: e.message, timestamp: Date.now() },
        };
      }
    }

    case 'PROMOTE_VARIATION': {
      if (action.nodeId === state.tree.rootId) return state;
      if (!state.tree.nodes[action.nodeId]) return state;

      const snapshot = createSnapshot(state);
      const treeClone = JSON.parse(JSON.stringify(state.tree));
      const treeOps = new StudyTree(treeClone);

      try {
        treeOps.promoteVariation(action.nodeId);
        return {
          ...state,
          tree: treeOps.getData(),
          isDirty: true,
          history: [...state.history, snapshot],
        };
      } catch (e: any) {
        return {
          ...state,
          error: { type: 'SAVE_ERROR', message: e.message, timestamp: Date.now() },
        };
      }
    }

    case 'UNDO': {
      if (state.history.length === 0) return state;
      const previous = state.history[state.history.length - 1];
      const newHistory = state.history.slice(0, -1);
      return {
        ...previous,
        history: newHistory,
      };
    }

    case 'SET_REPLAY_RESULT':
      return {
        ...state,
        lastReplayResult: action.result,
        currentFen: action.result.finalFen,
        error: action.result.error
          ? {
              type: 'REPLAY_ERROR',
              message: action.result.error,
              context: {
                illegalMoveIndex: action.result.illegalMoveIndex,
                path: state.currentPath,
              },
              timestamp: Date.now(),
            }
          : null,
      };

    case 'SET_ERROR':
      return { ...state, error: action.error };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'SET_LOADING':
      return { ...state, isLoading: action.isLoading };

    case 'MARK_SAVED':
      return { ...state, isDirty: false, lastSavedAt: action.timestamp, lastSavedHash: action.hash };

    case 'SET_SAVING':
      return { ...state, isSaving: action.isSaving };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

// =============================================================================
// Context Value
// =============================================================================

export interface StudyContextValue {
  state: StudyState;
  replayPath: (moves: string[], startFen?: string) => ReplayResult;
  setError: (type: StudyErrorType, message: string, context?: Record<string, unknown>) => void;
  clearError: () => void;
  hasReplayError: () => boolean;
  loadStudy: (studyId: string) => Promise<void>;
  selectChapter: (chapterId: string, startFen?: string) => Promise<void>;
  loadTree: (tree: StudyTreeData) => void;
  selectNode: (nodeId: string) => void;
  addMove: (san: string) => void;
  setComment: (nodeId: string, comment: string) => void;
  deleteMove: (nodeId: string) => void;
  promoteVariation: (nodeId: string) => void;
  undo: () => void;
  saveTree: () => Promise<void>;
  loadTreeFromServer: () => Promise<void>;
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
  deleteMove: () => {},
  promoteVariation: () => {},
  undo: () => {},
  saveTree: async () => {},
  loadTreeFromServer: async () => {},
};

const StudyContext = createContext<StudyContextValue>(defaultContextValue);

// =============================================================================
// Provider
// =============================================================================

export interface StudyProviderProps {
  children: ReactNode;
}

export function StudyProvider({ children }: StudyProviderProps) {
  const [state, dispatch] = useReducer(studyReducer, initialState);
  const fenCacheRef = useRef<Record<string, string>>({});
  const patchBase = '/api/v1/workspace/studies/study-patch';

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
    (type: StudyErrorType, message: string, context?: Record<string, unknown>) => {
      dispatch({
        type: 'SET_ERROR',
        error: { type, message, context, timestamp: Date.now() },
      });
    },
    []
  );

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const hasReplayError = useCallback(() => {
    return state.error?.type === 'REPLAY_ERROR';
  }, [state.error]);

  const loadStudy = useCallback(async (studyId: string) => {
    dispatch({ type: 'SET_STUDY', studyId });
  }, []);

  const selectChapter = useCallback(async (chapterId: string, startFen?: string) => {
    fenCacheRef.current = {};
    dispatch({ type: 'SET_CHAPTER', chapterId, startFen });
  }, []);

  const loadTree = useCallback((tree: StudyTreeData) => {
    dispatch({ type: 'LOAD_TREE', tree });
  }, []);

  const selectNode = useCallback((nodeId: string) => {
    const cachedFen = fenCacheRef.current[nodeId];
    dispatch({ type: 'SET_CURSOR', nodeId, precomputedFen: cachedFen });
  }, []);

  const addMove = useCallback((san: string) => {
    dispatch({ type: 'ADD_MOVE', san });
  }, []);

  const setComment = useCallback((nodeId: string, comment: string) => {
    dispatch({ type: 'SET_COMMENT', nodeId, comment });
  }, []);

  const deleteMove = useCallback((nodeId: string) => {
    dispatch({ type: 'DELETE_MOVE', nodeId });
  }, []);

  const promoteVariation = useCallback((nodeId: string) => {
    dispatch({ type: 'PROMOTE_VARIATION', nodeId });
  }, []);

  const undo = useCallback(() => {
    dispatch({ type: 'UNDO' });
  }, []);

  const saveTree = useCallback(async () => {
    if (!state.chapterId) {
      setError('SAVE_ERROR', 'Cannot save: missing chapter id');
      return;
    }
    if (state.isSaving) {
      return;
    }

    const treePayload = JSON.stringify(state.tree);
    let currentHash = '';
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(treePayload);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      currentHash = Array.from(new Uint8Array(hashBuffer))
        .map((byte) => byte.toString(16).padStart(2, '0'))
        .join('');
    } catch {
      currentHash = '';
    }
    if (currentHash === state.lastSavedHash && !state.isDirty) {
      return;
    }

    console.info(`[saveTree] Saving tree for chapter ${state.chapterId}`, { hash: currentHash || 'n/a' });
    dispatch({ type: 'SET_SAVING', isSaving: true });
    try {
      await api.put(`${patchBase}/chapter/${state.chapterId}/tree`, state.tree);

      console.info(`[saveTree] Saved tree for chapter ${state.chapterId}`, { hash: currentHash });
      dispatch({ type: 'MARK_SAVED', timestamp: Date.now(), hash: currentHash });
    } catch (e) {
      setError('SAVE_ERROR', e instanceof Error ? e.message : 'Failed to save tree');
    } finally {
      dispatch({ type: 'SET_SAVING', isSaving: false });
    }
  }, [patchBase, state.chapterId, state.isSaving, state.isDirty, state.lastSavedHash, state.tree, setError]);

  useEffect(() => {
    if (!state.isDirty || !state.chapterId) return;

    const timeoutId = window.setTimeout(() => {
      saveTree();
    }, 15000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [state.isDirty, state.chapterId, state.tree, saveTree]);

  const loadTreeFromServer = useCallback(async () => {
    console.log("loadTreeFromServer placeholder called");
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
    deleteMove,
    promoteVariation,
    undo,
    saveTree,
    loadTreeFromServer,
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
