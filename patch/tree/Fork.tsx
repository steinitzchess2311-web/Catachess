/**
 * Fork.tsx – inline branch-choice widget for the study move tree.
 *
 * Mirrors Lichess analyse/src/fork.ts + css/_fork.scss.
 * When a position has 2+ child moves, the Fork component renders them as a
 * 2-per-row clickable grid with blue highlighting on the active/hovered cell.
 *
 * Exports
 * ───────
 *  Fork        – pure presentational component (the visible grid)
 *  ForkWidget  – context-aware wrapper: reads useStudy(), renders Fork when
 *                the current cursor node has 2+ children.  Place this at the
 *                bottom of the sidebar panel.
 */

import React from 'react';
import type { StudyNode } from './type';
import { useStudy } from '../studyContext';
import './fork.css';

// ---------------------------------------------------------------------------
// Annotation helpers
// ---------------------------------------------------------------------------

const NAG_MAP: Record<number, string> = {
  1: '!',
  2: '?',
  3: '!!',
  4: '??',
  5: '!?',
  6: '?!',
};

function nagToSymbol(nag: number): string {
  return NAG_MAP[nag] ?? '';
}

/** Convert a 1-based half-move ply to a human-readable move prefix. */
function movePrefix(ply: number): string {
  const moveNum = Math.floor((ply + 1) / 2);
  const isWhite = ply % 2 === 1;
  return isWhite ? `${moveNum}.` : `${moveNum}...`;
}

/**
 * Count the depth of nodeId from the root (root = depth 0).
 * Returns the ply that nodeId's children are at (depth + 1).
 */
function childPlyOf(nodeId: string, nodes: Record<string, StudyNode>): number {
  let depth = 0;
  let id: string | null = nodeId;
  while (id && nodes[id] && nodes[id].parentId !== null) {
    depth++;
    id = nodes[id].parentId;
  }
  return depth + 1; // children are one level deeper
}

// ---------------------------------------------------------------------------
// Fork – presentational component
// ---------------------------------------------------------------------------

export interface ForkProps {
  /** Child node IDs (must be ≥ 2) to display as alternatives. */
  childIds: string[];
  nodes: Record<string, StudyNode>;
  /** 1-based half-move ply of the children – used to build the move prefix. */
  ply: number;
  /** The child that is shown as highlighted by default (main line). */
  activeChildId: string;
  onSelect: (nodeId: string) => void;
  onContextMenu?: (nodeId: string, event: React.MouseEvent) => void;
}

export const Fork = React.memo(function Fork({
  childIds,
  nodes,
  ply,
  activeChildId,
  onSelect,
  onContextMenu,
}: ForkProps) {
  if (childIds.length < 2) return null;

  const prefix = movePrefix(ply);

  return (
    <div className="study-fork">
      {childIds.map((id) => {
        const node = nodes[id];
        if (!node) return null;
        const isActive = id === activeChildId;

        return (
          <div
            key={id}
            className={`study-fork__move${isActive ? ' active' : ''}`}
            onClick={() => onSelect(id)}
            onContextMenu={
              onContextMenu
                ? (e) => { e.preventDefault(); onContextMenu(id, e); }
                : undefined
            }
            onDoubleClick={
              onContextMenu
                ? (e) => { e.stopPropagation(); onContextMenu(id, e); }
                : undefined
            }
          >
            <span className="study-fork__prefix">{prefix}</span>
            <span className="study-fork__san">&nbsp;{node.san}</span>
            {node.nags && node.nags.length > 0 && (
              <span className="study-fork__nag">
                {node.nags.map(nagToSymbol).join('')}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
});

// ---------------------------------------------------------------------------
// ForkWidget – context-aware wrapper, place at the bottom of the sidebar
// ---------------------------------------------------------------------------

/**
 * Reads the current cursor position from useStudy().
 * Renders a Fork grid when the cursor node has 2+ children (i.e. there are
 * multiple candidate moves from the current position).
 * Renders nothing when there is only one (or zero) continuation.
 */
export function ForkWidget() {
  const { state, selectNode } = useStudy();
  const { tree, cursorNodeId } = state;

  if (!tree?.nodes || !cursorNodeId) return null;

  const cursorNode = tree.nodes[cursorNodeId];
  if (!cursorNode || cursorNode.children.length < 2) return null;

  const ply = childPlyOf(cursorNodeId, tree.nodes);

  return (
    <Fork
      childIds={cursorNode.children}
      nodes={tree.nodes}
      ply={ply}
      activeChildId={cursorNode.children[0]}
      onSelect={selectNode}
    />
  );
}
