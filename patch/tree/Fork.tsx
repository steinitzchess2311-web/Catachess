/**
 * Fork.tsx – inline branch-choice widget for the study move tree.
 *
 * Mirrors Lichess analyse/src/fork.ts + css/_fork.scss.
 * When a position has 2+ children, the Fork component renders them as a
 * 2-per-row clickable grid with blue highlighting on the active path.
 *
 * Key exports
 * ───────────
 *  buildActivePath  – build the Set of ancestor IDs from root → cursorNodeId
 *  getActiveChild   – pick the child of a node that lies on the active path
 *  Fork             – React component (the visible widget)
 */

import React from 'react';
import type { StudyNode } from './type';
import './fork.css';

// ---------------------------------------------------------------------------
// Path helpers
// ---------------------------------------------------------------------------

/**
 * Walk from cursorNodeId up to the root, collecting every visited ID.
 * The resulting Set is used to determine which branch is "active" at each
 * fork point.
 */
export function buildActivePath(
  cursorNodeId: string,
  nodes: Record<string, StudyNode>,
): Set<string> {
  const path = new Set<string>();
  let id: string | null = cursorNodeId;
  while (id && nodes[id]) {
    path.add(id);
    id = nodes[id].parentId;
  }
  return path;
}

/**
 * Given a node with 2+ children, return the child that lies on the active
 * path to cursorNodeId.  Falls back to children[0] (main line) when the
 * cursor is above this fork (none of the children are ancestors of cursor).
 */
export function getActiveChild(
  node: StudyNode,
  activePath: Set<string>,
): string {
  return node.children.find(id => activePath.has(id)) ?? node.children[0];
}

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

/** Convert a 1-based half-move ply to a human-readable prefix ("3." / "3..."). */
function movePrefix(ply: number): string {
  const moveNum = Math.floor((ply + 1) / 2);
  const isWhite = ply % 2 === 1;
  return isWhite ? `${moveNum}.` : `${moveNum}...`;
}

// ---------------------------------------------------------------------------
// Fork component
// ---------------------------------------------------------------------------

export interface ForkProps {
  /** Child node IDs (must be ≥ 2) to display as alternatives. */
  childIds: string[];
  nodes: Record<string, StudyNode>;
  /** 1-based half-move ply of the children – used to build the move prefix. */
  ply: number;
  /** The child that is currently on the active path (shown highlighted). */
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
