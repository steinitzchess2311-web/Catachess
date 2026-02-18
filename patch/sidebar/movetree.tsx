import React from 'react';
import { useStudy } from '../studyContext';
import { StudyNode } from '../tree/type';
import type { StudyTree as StudyTreeData } from '../tree/type';
import { Fork, buildActivePath, getActiveChild } from '../tree/Fork';

export interface MoveTreeProps {
  className?: string;
}

// ─── Thin wrapper ────────────────────────────────────────────────────────────
// Re-renders on every context change, but is lightweight (just passes props).
// MoveTreeDisplay below is memoized so it skips re-renders caused by unrelated
// state changes (isSaving, currentFen, error, isDirty, etc.).

export function MoveTree({ className }: MoveTreeProps) {
  const {
    state,
    selectNode,
    selectChapter,
    loadTreeFromServer,
    saveTree,
    deleteMove,
    promoteVariation,
  } = useStudy();

  return (
    <MoveTreeDisplay
      className={className}
      tree={state.tree}
      cursorNodeId={state.cursorNodeId}
      chapterId={state.chapterId}
      onSelectNode={selectNode}
      onSelectChapter={selectChapter}
      loadTreeFromServer={loadTreeFromServer}
      saveTree={saveTree}
      onDeleteMove={deleteMove}
      onPromoteVariation={promoteVariation}
    />
  );
}

// ─── MoveTreeDisplay props ────────────────────────────────────────────────────

interface MoveTreeDisplayProps {
  className?: string;
  tree: StudyTreeData;
  cursorNodeId: string;
  chapterId: string | null;
  onSelectNode: (nodeId: string) => void;
  onSelectChapter: (chapterId: string, startFen?: string) => Promise<void>;
  loadTreeFromServer: () => Promise<void>;
  saveTree: () => Promise<void>;
  onDeleteMove: (nodeId: string) => void;
  onPromoteVariation: (nodeId: string) => void;
}

// ─── Memoized display ────────────────────────────────────────────────────────
// Only re-renders when tree or cursorNodeId changes (or local UI state).
// Unrelated context changes (isSaving, currentFen, error…) are blocked here.

const MoveTreeDisplay = React.memo(function MoveTreeDisplay({
  className,
  tree,
  cursorNodeId,
  chapterId,
  onSelectNode,
  onSelectChapter,
  loadTreeFromServer,
  saveTree,
  onDeleteMove,
  onPromoteVariation,
}: MoveTreeDisplayProps) {
  const [menuState, setMenuState] = React.useState<{
    nodeId: string;
    x: number;
    y: number;
    canPromote: boolean;
  } | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = React.useState<string | null>(null);

  const handleReload = React.useCallback(() => {
    if (chapterId) {
      onSelectChapter(chapterId);
      return;
    }
    loadTreeFromServer();
  }, [chapterId, onSelectChapter, loadTreeFromServer]);

  const handleNodeClick = React.useCallback((nodeId: string) => {
    onSelectNode(nodeId);
  }, [onSelectNode]);

  // tree.nodes is stable when only cursorNodeId changes, so this callback
  // won't be recreated on every cursor move.
  const handleContextMenu = React.useCallback((nodeId: string, event: React.MouseEvent) => {
    if (event.shiftKey) return;
    event.preventDefault();
    event.stopPropagation();
    const node = tree.nodes[nodeId];
    const parentId = node?.parentId;
    const canPromote = Boolean(
      parentId && tree.nodes[parentId]?.children?.[0] && tree.nodes[parentId]?.children[0] !== nodeId
    );
    setMenuState({ nodeId, x: event.clientX, y: event.clientY, canPromote });
  }, [tree.nodes]);

  // Build the active-path set once per cursor change so fork widgets know
  // which branch to highlight.
  const activePath = React.useMemo(
    () => buildActivePath(cursorNodeId, tree.nodes),
    [cursorNodeId, tree.nodes],
  );

  if (!tree || !tree.nodes || !tree.rootId || !cursorNodeId) {
    return <MoveTreeUnavailable onReload={handleReload} className={className} />;
  }

  const rootNode = tree.nodes[tree.rootId];
  if (!rootNode || !tree.nodes[cursorNodeId]) {
    return <MoveTreeUnavailable onReload={handleReload} className={className} />;
  }

  // When the root itself has multiple first-move alternatives, determine which
  // branch the cursor is currently in so MoveBranch starts at the right node.
  const activeStartId =
    rootNode.children.length >= 2
      ? getActiveChild(rootNode, activePath)
      : rootNode.children[0] ?? null;

  return (
    <div
      className={`move-tree-container ${className || ''}`}
      style={{
        padding: '10px',
        fontFamily: 'sans-serif',
        fontSize: '14px',
        overflowY: 'auto'
      }}
    >
      <div className="move-tree-title" style={{ fontWeight: 'bold', marginBottom: '10px', borderBottom: '1px solid #ddd', paddingBottom: '5px' }}>
        <span>Move Tree</span>
      </div>
      <div className="move-tree-content">
        {rootNode.children.length >= 2 && (
          <Fork
            childIds={rootNode.children}
            nodes={tree.nodes}
            ply={1}
            activeChildId={getActiveChild(rootNode, activePath)}
            onSelect={handleNodeClick}
            onContextMenu={handleContextMenu}
          />
        )}
        {activeStartId && (
          <MoveBranch
            startNodeId={activeStartId}
            nodes={tree.nodes}
            cursorNodeId={cursorNodeId}
            activePath={activePath}
            onSelect={handleNodeClick}
            startPly={1}
            onContextMenu={handleContextMenu}
          />
        )}
      </div>
      {menuState && (
        <div
          className="patch-context-menu"
          style={{ top: menuState.y, left: menuState.x }}
          onMouseLeave={() => setMenuState(null)}
        >
          <button
            type="button"
            className="patch-context-item"
            disabled={!menuState.canPromote}
            onClick={() => {
              onPromoteVariation(menuState.nodeId);
              setMenuState(null);
            }}
          >
            Promote to Mainline
          </button>
          <button
            type="button"
            className="patch-context-item is-danger"
            onClick={() => {
              setConfirmDeleteId(menuState.nodeId);
              setMenuState(null);
            }}
          >
            Delete Branch
          </button>
        </div>
      )}
      {confirmDeleteId && (
        <div className="patch-confirm-overlay">
          <div className="patch-confirm-card">
            <div className="patch-confirm-title">Delete branch?</div>
            <div className="patch-confirm-body">
              This will delete this move and all following moves in this branch.
            </div>
            <div className="patch-confirm-actions">
              <button
                type="button"
                className="patch-confirm-btn"
                onClick={() => setConfirmDeleteId(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="patch-confirm-btn is-danger"
                onClick={() => {
                  onDeleteMove(confirmDeleteId);
                  setConfirmDeleteId(null);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

// ─── Unavailable fallback ─────────────────────────────────────────────────────

function MoveTreeUnavailable({ onReload, className }: { onReload: () => void; className?: string }) {
  return (
    <div className={`move-tree-container ${className || ''}`} style={{ padding: '20px', color: '#666', fontStyle: 'italic' }}>
      <div style={{ marginBottom: '8px' }}>Move tree unavailable.</div>
      <button
        type="button"
        onClick={onReload}
        style={{
          padding: '6px 10px',
          backgroundColor: '#4a4a4a',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Reload Chapter
      </button>
    </div>
  );
}

// ─── MoveBranch ───────────────────────────────────────────────────────────────
// Renders the active path through the tree, injecting Fork widgets at every
// branch point (nodes with 2+ children).  Only the currently active branch is
// followed; the other alternatives are visible (and clickable) in the Fork grid.

interface MoveBranchProps {
  startNodeId: string;
  nodes: Record<string, StudyNode>;
  cursorNodeId: string;
  /** Set of ancestor IDs from root → cursorNodeId (inclusive). */
  activePath: Set<string>;
  onSelect: (nodeId: string) => void;
  startPly: number;
  onContextMenu: (nodeId: string, event: React.MouseEvent) => void;
}

// React.memo prevents re-renders when only MoveTreeDisplay's local UI state
// changes (menuState, confirmDeleteId).
const MoveBranch = React.memo(function MoveBranch({
  startNodeId,
  nodes,
  cursorNodeId,
  activePath,
  onSelect,
  startPly,
  onContextMenu,
}: MoveBranchProps) {
  if (!startNodeId) return null;

  const lines: React.ReactNode[] = [];
  const lineStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'max-content max-content',
    gap: '6px',
    marginBottom: '4px',
    alignItems: 'center',
  };

  let currentId: string | null = startNodeId;
  let ply = startPly;

  while (currentId) {
    const currentNode = nodes[currentId];
    if (!currentNode) break;

    const isWhite = ply % 2 === 1;
    const moveNumber = Math.floor((ply + 1) / 2);

    if (isWhite) {
      const whiteNode = currentNode;
      const whiteId = whiteNode.id;

      if (whiteNode.children.length === 0) {
        // Terminal white move
        lines.push(
          <div key={`line-white-${whiteId}`} className="move-line" style={lineStyle}>
            <MoveItem nodeId={whiteId} nodes={nodes} cursorNodeId={cursorNodeId}
              onSelect={onSelect} isMainline={true} prefix={`${moveNumber}.`}
              onContextMenu={onContextMenu} />
            <div />
          </div>
        );
        currentId = null;

      } else if (whiteNode.children.length >= 2) {
        // Fork: multiple black responses – show white alone then fork grid
        const activeNextId = getActiveChild(whiteNode, activePath);
        lines.push(
          <div key={`line-white-${whiteId}`} className="move-line" style={lineStyle}>
            <MoveItem nodeId={whiteId} nodes={nodes} cursorNodeId={cursorNodeId}
              onSelect={onSelect} isMainline={true} prefix={`${moveNumber}.`}
              onContextMenu={onContextMenu} />
            <div />
          </div>
        );
        lines.push(
          <Fork key={`fork-${whiteId}`} childIds={whiteNode.children} nodes={nodes}
            ply={ply + 1} activeChildId={activeNextId}
            onSelect={onSelect} onContextMenu={onContextMenu} />
        );
        currentId = activeNextId;
        ply += 1;

      } else {
        // Single black response
        const blackId = whiteNode.children[0];
        const blackNode = nodes[blackId];

        if (!blackNode) {
          lines.push(
            <div key={`line-white-${whiteId}`} className="move-line" style={lineStyle}>
              <MoveItem nodeId={whiteId} nodes={nodes} cursorNodeId={cursorNodeId}
                onSelect={onSelect} isMainline={true} prefix={`${moveNumber}.`}
                onContextMenu={onContextMenu} />
              <div />
            </div>
          );
          currentId = null;

        } else if (blackNode.children.length >= 2) {
          // Fork: multiple white continuations after the black response
          const activeNextId = getActiveChild(blackNode, activePath);
          lines.push(
            <div key={`line-pair-${whiteId}`} className="move-line" style={lineStyle}>
              <MoveItem nodeId={whiteId} nodes={nodes} cursorNodeId={cursorNodeId}
                onSelect={onSelect} isMainline={true} prefix={`${moveNumber}.`}
                onContextMenu={onContextMenu} />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <MoveItem nodeId={blackId} nodes={nodes} cursorNodeId={cursorNodeId}
                  onSelect={onSelect} isMainline={true} prefix={`${moveNumber}...`}
                  onContextMenu={onContextMenu} />
              </div>
            </div>
          );
          lines.push(
            <Fork key={`fork-${blackId}`} childIds={blackNode.children} nodes={nodes}
              ply={ply + 2} activeChildId={activeNextId}
              onSelect={onSelect} onContextMenu={onContextMenu} />
          );
          currentId = activeNextId;
          ply += 2;

        } else {
          // Linear pair (no fork) – standard white + black on one row
          lines.push(
            <div key={`line-pair-${whiteId}`} className="move-line" style={lineStyle}>
              <MoveItem nodeId={whiteId} nodes={nodes} cursorNodeId={cursorNodeId}
                onSelect={onSelect} isMainline={true} prefix={`${moveNumber}.`}
                onContextMenu={onContextMenu} />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <MoveItem nodeId={blackId} nodes={nodes} cursorNodeId={cursorNodeId}
                  onSelect={onSelect} isMainline={true} prefix={`${moveNumber}...`}
                  onContextMenu={onContextMenu} />
              </div>
            </div>
          );
          currentId = blackNode.children[0] || null;
          ply += 2;
        }
      }

    } else {
      // Black's move (variation branch that starts mid-game from black's turn)
      const blackNode = currentNode;
      const blackId = blackNode.id;

      lines.push(
        <div key={`line-black-${blackId}`} className="move-line" style={lineStyle}>
          <div />
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <MoveItem nodeId={blackId} nodes={nodes} cursorNodeId={cursorNodeId}
              onSelect={onSelect} isMainline={true} prefix={`${moveNumber}...`}
              onContextMenu={onContextMenu} />
          </div>
        </div>
      );

      if (blackNode.children.length >= 2) {
        const activeNextId = getActiveChild(blackNode, activePath);
        lines.push(
          <Fork key={`fork-${blackId}`} childIds={blackNode.children} nodes={nodes}
            ply={ply + 1} activeChildId={activeNextId}
            onSelect={onSelect} onContextMenu={onContextMenu} />
        );
        currentId = activeNextId;
      } else {
        currentId = blackNode.children[0] || null;
      }
      ply += 1;
    }
  }

  return (
    <div className="move-branch">
      {lines}
    </div>
  );
});

// ─── MoveItem ─────────────────────────────────────────────────────────────────

interface MoveItemProps {
  nodeId: string;
  nodes: Record<string, StudyNode>;
  cursorNodeId: string;
  onSelect: (nodeId: string) => void;
  isMainline: boolean;
  prefix?: string;
  onContextMenu: (nodeId: string, event: React.MouseEvent) => void;
}

// Custom comparator: only re-renders when this node's own data changes OR its
// active state flips. Cursor navigation that doesn't touch this node is skipped.
function moveItemPropsAreEqual(prev: MoveItemProps, next: MoveItemProps): boolean {
  const prevActive = prev.cursorNodeId === prev.nodeId;
  const nextActive = next.cursorNodeId === next.nodeId;
  return (
    prevActive === nextActive &&
    prev.nodes[prev.nodeId] === next.nodes[next.nodeId] &&
    prev.isMainline === next.isMainline &&
    prev.prefix === next.prefix &&
    prev.onSelect === next.onSelect &&
    prev.onContextMenu === next.onContextMenu
  );
}

const MoveItem = React.memo(function MoveItem({
  nodeId,
  nodes,
  cursorNodeId,
  onSelect,
  isMainline,
  prefix = '',
  onContextMenu,
}: MoveItemProps) {
  const node = nodes[nodeId];
  if (!node) return null;

  const isActive = cursorNodeId === nodeId;

  return (
    <div
      className={`move-item ${isActive ? 'active' : ''}`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(nodeId);
      }}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onContextMenu(nodeId, e);
      }}
      onContextMenu={(e) => onContextMenu(nodeId, e)}
      style={{
        display: 'block',
        width: 'max-content',
        textAlign: 'left',
        padding: '2px 6px',
        margin: '2px',
        borderRadius: '3px',
        cursor: 'pointer',
        backgroundColor: isActive ? '#3b82f6' : 'transparent',
        color: isActive ? 'white' : (isMainline ? '#000' : '#444'),
        fontWeight: isMainline ? 'bold' : 'normal',
        border: isActive ? 'none' : '1px solid transparent',
        transition: 'all 0.1s',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = '#e5e7eb';
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      {prefix && <span className="move-prefix" style={{ marginRight: '4px' }}>{prefix}</span>}
      <span className="move-san">{node.san}</span>
      {node.nags && node.nags.length > 0 && (
        <span className="move-nags" style={{ marginLeft: '2px', color: isActive ? 'white' : '#d97706' }}>
          {node.nags.map(nagToSymbol).join('')}
        </span>
      )}
      {node.comment && (
        <span className="move-comment-icon" title={node.comment} style={{ marginLeft: '4px', opacity: 0.6 }}>
          💬
        </span>
      )}
    </div>
  );
}, moveItemPropsAreEqual);

function nagToSymbol(nag: number): string {
  const map: Record<number, string> = {
    1: '!',
    2: '?',
    3: '!!',
    4: '??',
    5: '!?',
    6: '?!',
  };
  return map[nag] || '';
}

export default MoveTree;
