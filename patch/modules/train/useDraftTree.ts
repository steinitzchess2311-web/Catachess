/**
 * useDraftTree.ts - Local hook managing draft tree state for train mode.
 *
 * No global state: all data is local to this hook instance.
 * Discarded on exit without submit.
 */

import { useState, useCallback, useMemo } from 'react';
import { validateMove } from '../../chessJS/replay';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface DraftNode {
  id: string;
  parentId: string | null;
  san: string;
  children: string[];
  comment: string;
  isValid: boolean;
}

export interface AddMoveResult {
  ok: boolean;
  san: string | null;
  error: string | null;
}

interface DraftState {
  rootId: string;
  nodes: Record<string, DraftNode>;
  /** node id → FEN after that move */
  nodeFen: Map<string, string>;
  startFen: string;
  /** cursorNodeId from main tree at train entry */
  startNodeId: string;
}

// ─── ID generator ─────────────────────────────────────────────────────────────

function generateId(): string {
  return 'draft_' + Math.random().toString(36).substring(2, 10) + Date.now().toString(36).substring(4);
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export interface UseDraftTreeReturn {
  nodes: Record<string, DraftNode>;
  nodeFen: Map<string, string>;
  rootId: string;
  startFen: string;
  startNodeId: string;
  addMove: (parentId: string, san: string) => AddMoveResult;
  setComment: (nodeId: string, comment: string) => void;
  deleteNode: (nodeId: string) => void;
  isSubmittable: boolean;
}

export function useDraftTree(startFen: string, startNodeId: string): UseDraftTreeReturn {
  const rootId = useMemo(() => generateId(), []);

  const [state, setState] = useState<DraftState>(() => {
    const root: DraftNode = {
      id: rootId,
      parentId: null,
      san: '',
      children: [],
      comment: '',
      isValid: true,
    };
    const nodeFen = new Map<string, string>();
    nodeFen.set(rootId, startFen);
    return {
      rootId,
      nodes: { [rootId]: root },
      nodeFen,
      startFen,
      startNodeId,
    };
  });

  const addMove = useCallback((parentId: string, san: string): AddMoveResult => {
    const parentFen = state.nodeFen.get(parentId);
    if (!parentFen) {
      return { ok: false, san: null, error: 'Parent node FEN not found' };
    }

    const result = validateMove(parentFen, san);
    if (!result.valid || !result.san || !result.fenAfter) {
      return { ok: false, san: null, error: result.error || 'Invalid move' };
    }

    const normalizedSan = result.san;
    const fenAfter = result.fenAfter;

    // Check for duplicate SAN among siblings
    const parent = state.nodes[parentId];
    if (parent) {
      const duplicate = parent.children.find(
        (cId) => state.nodes[cId]?.san === normalizedSan
      );
      if (duplicate) {
        return { ok: false, san: null, error: 'Move already exists' };
      }
    }

    const newId = generateId();
    const newNode: DraftNode = {
      id: newId,
      parentId,
      san: normalizedSan,
      children: [],
      comment: '',
      isValid: true,
    };

    setState((prev) => {
      const newNodes = { ...prev.nodes };
      newNodes[newId] = newNode;
      if (newNodes[parentId]) {
        newNodes[parentId] = {
          ...newNodes[parentId],
          children: [...newNodes[parentId].children, newId],
        };
      }
      const newFenMap = new Map(prev.nodeFen);
      newFenMap.set(newId, fenAfter);
      return { ...prev, nodes: newNodes, nodeFen: newFenMap };
    });

    return { ok: true, san: normalizedSan, error: null };
  }, [state.nodeFen, state.nodes]);

  const setComment = useCallback((nodeId: string, comment: string) => {
    setState((prev) => {
      if (!prev.nodes[nodeId]) return prev;
      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [nodeId]: { ...prev.nodes[nodeId], comment },
        },
      };
    });
  }, []);

  const deleteNode = useCallback((nodeId: string) => {
    setState((prev) => {
      if (!prev.nodes[nodeId] || nodeId === prev.rootId) return prev;

      // Collect all IDs to delete (subtree)
      const toDelete = new Set<string>();
      const queue = [nodeId];
      while (queue.length > 0) {
        const id = queue.shift()!;
        toDelete.add(id);
        const node = prev.nodes[id];
        if (node) queue.push(...node.children);
      }

      const newNodes = { ...prev.nodes };
      const newFenMap = new Map(prev.nodeFen);

      // Remove from parent's children
      const deletedNode = prev.nodes[nodeId];
      if (deletedNode?.parentId && newNodes[deletedNode.parentId]) {
        newNodes[deletedNode.parentId] = {
          ...newNodes[deletedNode.parentId],
          children: newNodes[deletedNode.parentId].children.filter((id) => id !== nodeId),
        };
      }

      // Delete all nodes in subtree
      toDelete.forEach((id) => {
        delete newNodes[id];
        newFenMap.delete(id);
      });

      return { ...prev, nodes: newNodes, nodeFen: newFenMap };
    });
  }, []);

  const isSubmittable = useMemo(() => {
    // Submittable if at least one non-root node exists
    return Object.keys(state.nodes).length > 1;
  }, [state.nodes]);

  return {
    nodes: state.nodes,
    nodeFen: state.nodeFen,
    rootId: state.rootId,
    startFen: state.startFen,
    startNodeId: state.startNodeId,
    addMove,
    setComment,
    deleteNode,
    isSubmittable,
  };
}
