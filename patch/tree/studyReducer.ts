/**
 * Created at: 2026-07-08 22:15 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-08 22:15 EDT
 * Last Modified by: Codex
 *
 * studyReducer — pure reducer + types for study state. No React imports.
 * Safe to test independently.
 */

import { replaySanPath, STARTING_FEN } from '../chessJS/replay';
import type { ReplayResult } from '../chessJS/replay';
import { StudyTree, createEmptyTree } from './StudyTree';
import type { StudyTree as StudyTreeData, Shape } from './type';
import { upgradeTree } from './type';
import { validateFen } from '../chessJS/fen';

// =============================================================================
// Error types
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
// State types
// =============================================================================

export interface StudyStateSnapshot {
  studyId: string | null;
  chapterId: string | null;
  effectivePermission: 'owner' | 'admin' | 'editor' | 'commenter' | 'viewer' | null;
  canEdit: boolean;
  tree: StudyTreeData;
  cursorNodeId: string;
  currentPath: string[];
  currentFen: string;
  startFen: string;
  treeRevision: number;
  treeUpdatedAt: string | null;
  remoteTreeRevision: number | null;
  remoteTreeUpdatedAt: string | null;
  remoteUpdateAvailable: boolean;
  lastReplayResult: ReplayResult | null;
  error: StudyError | null;
  isLoading: boolean;
  isDirty: boolean;
  lastSavedAt: number | null;
  isSaving: boolean;
  lastSavedHash: string | null;
  isTrainMode: boolean;
  trainEngineUnlocked: boolean;
}

export interface StudyState extends StudyStateSnapshot {
  history: StudyStateSnapshot[];
}

// =============================================================================
// Actions
// =============================================================================

export type StudyAction =
  | { type: 'SET_STUDY'; studyId: string }
  | {
      type: 'SET_ACCESS';
      canEdit: boolean;
      effectivePermission?: StudyStateSnapshot['effectivePermission'];
    }
  | { type: 'SET_CHAPTER'; chapterId: string; startFen?: string }
  | { type: 'LOAD_TREE'; tree: StudyTreeData; startFen?: string }
  | { type: 'SET_TREE_REVISION'; treeRevision: number; treeUpdatedAt?: string | null }
  | { type: 'SET_REMOTE_TREE_REVISION'; treeRevision: number; treeUpdatedAt?: string | null }
  | { type: 'CLEAR_REMOTE_UPDATE' }
  | { type: 'SET_CURSOR'; nodeId: string; precomputedFen?: string }
  | { type: 'ADD_MOVE'; san: string }
  | { type: 'SET_COMMENT'; nodeId: string; comment: string }
  | { type: 'SET_SHAPES'; nodeId: string; shapes: Shape[] }
  | { type: 'DELETE_MOVE'; nodeId: string }
  | { type: 'PROMOTE_VARIATION'; nodeId: string }
  | { type: 'UNDO' }
  | { type: 'SET_REPLAY_RESULT'; result: ReplayResult }
  | { type: 'SET_ERROR'; error: StudyError }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'MARK_SAVED'; timestamp: number; hash: string; keepDirty?: boolean }
  | { type: 'SET_SAVING'; isSaving: boolean }
  | { type: 'RESET' }
  | { type: 'ENTER_TRAIN_MODE' }
  | { type: 'EXIT_TRAIN_MODE' }
  | { type: 'SUBMIT_TRAIN'; mergedTree: StudyTreeData };

// =============================================================================
// Initial state
// =============================================================================

export const initialTree = createEmptyTree();

export const initialSnapshot: StudyStateSnapshot = {
  studyId: null,
  chapterId: null,
  effectivePermission: null,
  canEdit: false,
  tree: initialTree,
  cursorNodeId: initialTree.rootId,
  currentPath: [],
  currentFen: STARTING_FEN,
  startFen: STARTING_FEN,
  treeRevision: 0,
  treeUpdatedAt: null,
  remoteTreeRevision: null,
  remoteTreeUpdatedAt: null,
  remoteUpdateAvailable: false,
  lastReplayResult: null,
  error: null,
  isLoading: false,
  isDirty: false,
  lastSavedAt: null,
  isSaving: false,
  lastSavedHash: null,
  isTrainMode: false,
  trainEngineUnlocked: false,
};

export const initialState: StudyState = {
  ...initialSnapshot,
  history: [],
};

// =============================================================================
// Helpers
// =============================================================================

/** Maximum number of undo snapshots retained. Older entries are evicted. */
const MAX_HISTORY = 50;

/** Creates a history snapshot (excludes the history stack itself). */
export const createSnapshot = (state: StudyState): StudyStateSnapshot => {
  const { history, ...snapshot } = state;
  return { ...snapshot, currentPath: [...snapshot.currentPath] };
};

/** Append a snapshot to the history stack, capped at MAX_HISTORY. */
function pushHistory(history: StudyStateSnapshot[], snapshot: StudyStateSnapshot): StudyStateSnapshot[] {
  const next = [...history, snapshot];
  return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
}

// =============================================================================
// Reducer
// =============================================================================

export function studyReducer(state: StudyState, action: StudyAction): StudyState {
  switch (action.type) {
    case 'SET_STUDY':
      return { ...initialState, studyId: action.studyId };

    case 'SET_ACCESS':
      return {
        ...state,
        canEdit: action.canEdit,
        effectivePermission: action.effectivePermission ?? state.effectivePermission,
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
        startFen,
        currentFen: startFen,
        treeRevision: 0,
        treeUpdatedAt: null,
        remoteTreeRevision: null,
        remoteTreeUpdatedAt: null,
        remoteUpdateAvailable: false,
        error: startValidation.valid
          ? null
          : { type: 'INVALID_FEN', message: `Invalid starting FEN, falling back to default: ${startValidation.error}`, timestamp: Date.now() },
        isDirty: false,
        lastSavedAt: null,
        isSaving: false,
        lastSavedHash: null,
        history: [],
      };
    }

    case 'LOAD_TREE': {
      const requestedFen = action.startFen ?? state.startFen;
      const startValidation = validateFen(requestedFen);
      const safeStartFen = startValidation.valid ? requestedFen : STARTING_FEN;
      const upgrade = upgradeTree(action.tree);
      if (!upgrade.tree) {
        return {
          ...state,
          error: { type: 'LOAD_ERROR', message: upgrade.errors.join('; ') || 'Invalid tree data', timestamp: Date.now() },
        };
      }
      return {
        ...state,
        tree: upgrade.tree,
        cursorNodeId: upgrade.tree.rootId,
        currentPath: [],
        startFen: safeStartFen,
        currentFen: safeStartFen,
        remoteTreeRevision: null,
        remoteTreeUpdatedAt: null,
        remoteUpdateAvailable: false,
        error: startValidation.valid
          ? null
          : { type: 'INVALID_FEN', message: `Invalid starting FEN, falling back to default: ${startValidation.error}`, timestamp: Date.now() },
        isDirty: false,
        lastSavedAt: null,
        isSaving: false,
        lastSavedHash: null,
        history: [],
      };
    }

    case 'SET_TREE_REVISION':
      return {
        ...state,
        treeRevision: action.treeRevision,
        treeUpdatedAt: action.treeUpdatedAt ?? state.treeUpdatedAt,
        remoteTreeRevision: null,
        remoteTreeUpdatedAt: null,
        remoteUpdateAvailable: false,
      };

    case 'SET_REMOTE_TREE_REVISION':
      if (action.treeRevision <= state.treeRevision) return state;
      return {
        ...state,
        remoteTreeRevision: action.treeRevision,
        remoteTreeUpdatedAt: action.treeUpdatedAt ?? null,
        remoteUpdateAvailable: true,
      };

    case 'CLEAR_REMOTE_UPDATE':
      return {
        ...state,
        remoteTreeRevision: null,
        remoteTreeUpdatedAt: null,
        remoteUpdateAvailable: false,
      };

    case 'SET_CURSOR': {
      if (!state.tree.nodes[action.nodeId]) {
        return {
          ...state,
          error: { type: 'REPLAY_ERROR', message: `Cannot set cursor: Node ${action.nodeId} not found`, timestamp: Date.now() },
        };
      }

      const treeOps = new StudyTree(state.tree);
      const moves = treeOps.getPathSan(action.nodeId);

      if (action.precomputedFen) {
        return { ...state, cursorNodeId: action.nodeId, currentPath: moves, currentFen: action.precomputedFen, error: null };
      }

      // Cache miss — replay from startFen
      const replayResult = replaySanPath(moves, state.startFen);
      return {
        ...state,
        cursorNodeId: action.nodeId,
        currentPath: moves,
        currentFen: replayResult.finalFen,
        lastReplayResult: replayResult,
        error: replayResult.error
          ? { type: 'REPLAY_ERROR', message: replayResult.error, context: { illegalMoveIndex: replayResult.illegalMoveIndex }, timestamp: Date.now() }
          : null,
      };
    }

    case 'ADD_MOVE': {
      if (!state.canEdit) return state;
      const treeClone = structuredClone(state.tree);
      const treeOps = new StudyTree(treeClone);
      try {
        const newNode = treeOps.addMove(state.cursorNodeId, action.san);
        const newPath = [...state.currentPath, newNode.san];

        // Fast path: play just the new move on the current FEN — O(1) instead of O(n)
        const singleStep = replaySanPath([newNode.san], state.currentFen);
        const snapshot = createSnapshot(state);

        return {
          ...state,
          tree: treeOps.getData(),
          cursorNodeId: newNode.id,
          currentPath: newPath,
          currentFen: singleStep.finalFen,
          lastReplayResult: singleStep,
          isDirty: true,
          error: singleStep.error
            ? { type: 'REPLAY_ERROR', message: singleStep.error, context: { illegalMoveIndex: singleStep.illegalMoveIndex }, timestamp: Date.now() }
            : null,
          history: pushHistory(state.history, snapshot),
        };
      } catch (e: any) {
        return {
          ...state,
          error: { type: 'REPLAY_ERROR', message: e.message || 'Failed to add move', timestamp: Date.now() },
        };
      }
    }

    case 'SET_COMMENT': {
      if (!state.canEdit) return state;
      if (!state.tree.nodes[action.nodeId]) return state;
      const updatedNode = { ...state.tree.nodes[action.nodeId], comment: action.comment || null };
      const newTree = { ...state.tree, nodes: { ...state.tree.nodes, [action.nodeId]: updatedNode } };
      const snapshot = createSnapshot(state);
      return { ...state, tree: newTree, isDirty: true, history: [...state.history, snapshot] };
    }

    case 'SET_SHAPES': {
      if (!state.canEdit) return state;
      if (!state.tree.nodes[action.nodeId]) return state;
      const updatedNode = { ...state.tree.nodes[action.nodeId], shapes: action.shapes };
      const newTree = { ...state.tree, nodes: { ...state.tree.nodes, [action.nodeId]: updatedNode } };
      return { ...state, tree: newTree, isDirty: true };
    }

    case 'DELETE_MOVE': {
      if (!state.canEdit) return state;
      if (action.nodeId === state.tree.rootId) return state;
      const snapshot = createSnapshot(state);
      const treeClone = structuredClone(state.tree);
      const treeOps = new StudyTree(treeClone);
      const oldTreeOps = new StudyTree(state.tree);
      const currentPathIds = oldTreeOps.getPathToNode(state.cursorNodeId);

      let nextCursorId = state.cursorNodeId;
      let nextPath = state.currentPath;
      let nextFen = state.currentFen;

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
        return { ...state, tree: treeOps.getData(), cursorNodeId: nextCursorId, currentPath: nextPath, currentFen: nextFen, isDirty: true, history: [...state.history, snapshot] };
      } catch (e: any) {
        return { ...state, error: { type: 'SAVE_ERROR', message: e.message, timestamp: Date.now() } };
      }
    }

    case 'PROMOTE_VARIATION': {
      if (!state.canEdit) return state;
      if (action.nodeId === state.tree.rootId || !state.tree.nodes[action.nodeId]) return state;
      const snapshot = createSnapshot(state);
      const treeClone = structuredClone(state.tree);
      const treeOps = new StudyTree(treeClone);
      try {
        treeOps.promoteVariation(action.nodeId);
        return { ...state, tree: treeOps.getData(), isDirty: true, history: [...state.history, snapshot] };
      } catch (e: any) {
        return { ...state, error: { type: 'SAVE_ERROR', message: e.message, timestamp: Date.now() } };
      }
    }

    case 'UNDO': {
      if (!state.canEdit) return state;
      if (state.history.length === 0) return state;
      const previous = state.history[state.history.length - 1];
      return { ...previous, history: state.history.slice(0, -1) };
    }

    case 'SET_REPLAY_RESULT':
      return {
        ...state,
        lastReplayResult: action.result,
        currentFen: action.result.finalFen,
        error: action.result.error
          ? { type: 'REPLAY_ERROR', message: action.result.error, context: { illegalMoveIndex: action.result.illegalMoveIndex, path: state.currentPath }, timestamp: Date.now() }
          : null,
      };

    case 'SET_ERROR':
      return { ...state, error: action.error };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'SET_LOADING':
      return { ...state, isLoading: action.isLoading };

    case 'MARK_SAVED':
      return {
        ...state,
        isDirty: action.keepDirty ? state.isDirty : false,
        lastSavedAt: action.timestamp,
        lastSavedHash: action.hash,
      };

    case 'SET_SAVING':
      return { ...state, isSaving: action.isSaving };

    case 'RESET':
      return initialState;

    case 'ENTER_TRAIN_MODE':
      return { ...state, isTrainMode: true };

    case 'EXIT_TRAIN_MODE':
      return { ...state, isTrainMode: false };

    case 'SUBMIT_TRAIN':
      if (!state.canEdit) return state;
      return { ...state, isTrainMode: false, trainEngineUnlocked: true, tree: action.mergedTree, isDirty: true };

    default:
      return state;
  }
}
